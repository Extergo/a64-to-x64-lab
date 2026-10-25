"""Small straight-line AArch64 binary-to-x86-64 translator; Python 3.10+, no deps.

The native runner targets the Windows x64 ABI. RET X30 is an explicit block
terminator, not guest control-flow emulation. See README for the exact contract.
"""
from __future__ import annotations

import argparse
import ctypes
from dataclasses import dataclass
import json
import platform
from pathlib import Path
import struct
import sys

MASK64 = (1 << 64) - 1
MAX_INSTRUCTIONS = 4096
RET = 0xD65F03C0
NOP = 0xD503201F
BASES = {
    "ADD": 0x8B000000,
    "SUB": 0xCB000000,
    "AND": 0x8A000000,
    "ORR": 0xAA000000,
    "EOR": 0xCA000000,
}


class TranslationError(ValueError):
    """Input does not satisfy the supported block contract."""


@dataclass(frozen=True)
class Instruction:
    op: str
    rd: int = 0
    rn: int = 0
    rm: int = 0
    immediate: int = 0

    def __str__(self) -> str:
        reg = lambda n: "xzr" if n == 31 else f"x{n}"
        if self.op in ("RET", "NOP"):
            return self.op.lower()
        if self.op == "MOVZ":
            return f"movz {reg(self.rd)}, #{self.immediate:#x} (expanded value)"
        return f"{self.op.lower()} {reg(self.rd)}, {reg(self.rn)}, {reg(self.rm)}"


def decode(data: bytes) -> list[Instruction]:
    """Decode actual little-endian A64 words; reject everything outside the subset."""
    if not data or len(data) % 4:
        raise TranslationError("Expected a non-empty sequence of 4-byte A64 words")
    if len(data) // 4 > MAX_INSTRUCTIONS:
        raise TranslationError(f"Block exceeds {MAX_INSTRUCTIONS} instructions")
    instructions = []
    for offset in range(0, len(data), 4):
        word = struct.unpack_from("<I", data, offset)[0]
        rd, rn, rm = word & 31, (word >> 5) & 31, (word >> 16) & 31
        if word == RET:
            if offset != len(data) - 4:
                raise TranslationError("RET X30 must be the last word; trailing code rejected")
            instruction = Instruction("RET")
        elif word == NOP:
            instruction = Instruction("NOP")
        elif word & 0xFF800000 == 0xD2800000:
            immediate = ((word >> 5) & 0xFFFF) << (16 * ((word >> 21) & 3))
            instruction = Instruction("MOVZ", rd, immediate=immediate)
        else:
            # Require 64-bit, non-flag-setting, no inversion and LSL #0.
            op = next((name for name, base in BASES.items()
                       if word & 0xFFE0FC00 == base), None)
            if op is None:
                raise TranslationError(f"Unsupported encoding {word:#010x} at byte {offset}")
            instruction = Instruction(op, rd, rn, rm)
        instructions.append(instruction)
    if instructions[-1].op != "RET":
        raise TranslationError("Block must end in RET X30")
    return instructions


def compile_block(data: bytes) -> bytes:
    """Lower decoded instructions to a Windows x64 leaf function.

    RCX holds uint64_t guest[31]. RAX/RDX are scratch, never guest mappings.
    Keeping all guest registers in slots makes aliasing explicit and simple.
    """
    output = bytearray()

    def load(register: int, into_rdx: bool = False) -> None:
        if register == 31:
            output.extend(b"\x31\xd2" if into_rdx else b"\x31\xc0")
        else:
            output.extend(b"\x48\x8b\x91" if into_rdx else b"\x48\x8b\x81")
            output.extend(struct.pack("<I", 8 * register))

    def store(register: int) -> None:
        if register != 31:  # XZR discards writes; no slot 31 exists.
            output.extend(b"\x48\x89\x81" + struct.pack("<I", 8 * register))

    operations = {
        "ADD": b"\x48\x01\xd0", "SUB": b"\x48\x29\xd0",
        "AND": b"\x48\x21\xd0", "ORR": b"\x48\x09\xd0",
        "EOR": b"\x48\x31\xd0",
    }
    for instruction in decode(data):
        if instruction.op == "RET":
            load(0)
            output.append(0xC3)
        elif instruction.op == "NOP":
            output.append(0x90)
        elif instruction.op == "MOVZ":
            output.extend(b"\x48\xb8" + struct.pack("<Q", instruction.immediate))
            store(instruction.rd)
        else:
            load(instruction.rn)
            load(instruction.rm, into_rdx=True)
            output.extend(operations[instruction.op])
            store(instruction.rd)
    return bytes(output)


def initial_state(registers: list[int] | None) -> list[int]:
    if registers is None:
        return [0] * 31
    if len(registers) != 31 or any(not isinstance(v, int) for v in registers):
        raise ValueError("Initial state must contain exactly 31 integer values (X0..X30)")
    return [v & MASK64 for v in registers]


def interpret(data: bytes, registers: list[int] | None = None) -> list[int]:
    """Reference semantics over the shared decoder (not an independent ISA oracle)."""
    state = initial_state(registers)
    for instruction in decode(data):
        if instruction.op == "RET":
            break
        if instruction.op == "NOP":
            continue
        a = state[instruction.rn] if instruction.rn != 31 else 0
        b = state[instruction.rm] if instruction.rm != 31 else 0
        if instruction.op == "MOVZ":
            result = instruction.immediate
        elif instruction.op == "ADD":
            result = a + b
        elif instruction.op == "SUB":
            result = a - b
        elif instruction.op == "AND":
            result = a & b
        elif instruction.op == "ORR":
            result = a | b
        else:
            result = a ^ b
        if instruction.rd != 31:
            state[instruction.rd] = result & MASK64
    return state


def native_available() -> bool:
    return (sys.platform == "win32" and ctypes.sizeof(ctypes.c_void_p) == 8
            and platform.machine().lower() in ("amd64", "x86_64"))


def execute(data: bytes, registers: list[int] | None = None) -> tuple[int, list[int]]:
    """Compile and run the generated block, returning X0 and the full guest state."""
    if not native_available():
        raise RuntimeError("Native execution currently requires 64-bit Python on Windows x86-64")
    code = compile_block(data)  # Only validated A64 inputs reach the native buffer.
    state = (ctypes.c_uint64 * 31)(*initial_state(registers))
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32, ctypes.c_uint32]
    kernel.VirtualAlloc.restype = ctypes.c_void_p
    kernel.VirtualProtect.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32,
                                     ctypes.POINTER(ctypes.c_uint32)]
    kernel.VirtualProtect.restype = ctypes.c_int
    kernel.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32]
    kernel.VirtualFree.restype = ctypes.c_int
    kernel.GetCurrentProcess.argtypes = []
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.FlushInstructionCache.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
    kernel.FlushInstructionCache.restype = ctypes.c_int
    address = kernel.VirtualAlloc(None, len(code), 0x3000, 0x04)  # reserve+commit, RW
    if not address:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        ctypes.memmove(address, code, len(code))
        old_protection = ctypes.c_uint32()
        if not kernel.VirtualProtect(address, len(code), 0x20, ctypes.byref(old_protection)):
            raise ctypes.WinError(ctypes.get_last_error())  # RX, never writable+executable
        if not kernel.FlushInstructionCache(kernel.GetCurrentProcess(), address, len(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        function = ctypes.CFUNCTYPE(ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64))(address)
        result = function(state)
        return result, list(state)
    finally:
        if not kernel.VirtualFree(address, 0, 0x8000):
            raise ctypes.WinError(ctypes.get_last_error())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path, help="Raw little-endian A64 instruction bytes")
    parser.add_argument("--emit", type=Path, help="Write generated x86-64 bytes")
    parser.add_argument("--run", action="store_true", help="Execute on Windows x86-64 and compare state")
    args = parser.parse_args()
    try:
        data = args.binary.read_bytes()
        instructions = decode(data)
        code = compile_block(data)
        for index, instruction in enumerate(instructions):
            print(f"{index * 4:04x}: {instruction}")
        print(f"A64 input: {len(data)} bytes; x86-64 output: {len(code)} bytes")
        if args.emit:
            args.emit.write_bytes(code)
        expected = interpret(data)
        if args.run:
            result, actual = execute(data)
            if actual != expected or result != expected[0]:
                raise RuntimeError("Native result differs from reference semantics")
            print(json.dumps({"native_x0": result, "reference_x0": expected[0],
                              "all_31_registers_match": True}))
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
