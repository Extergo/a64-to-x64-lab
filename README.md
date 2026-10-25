# a64-to-x64-lab

A small learning prototype that translates a **restricted block of real
AArch64 instruction bytes into x86-64 machine code**, then executes it on
Windows x86-64. Direction: **Arm input, x86 output**.

Started 25 October 2026. The initial implementation and tests were produced
with Codex assistance. This is a starting point for studying instruction
decoding, lowering, register state and native execution; it does not imply
that the learner independently wrote or already understands every part.

## First run

Use 64-bit Python 3.10+ on Windows x86-64. No Python packages are required.
The `.bin` examples are raw A64 `.text` bytes, assembled from the adjacent
`.s` files with LLVM. The translator does not parse assembly text.

```powershell
python translator.py examples/add42.bin --run
python translator.py examples/logic.bin --run
python -m unittest discover -s tests -v
```

The first example is:

```asm
movz x0, #40
movz x1, #2
add  x0, x0, x1
ret
```

It returns:

```json
{"native_x0": 42, "reference_x0": 42, "all_31_registers_match": true}
```

The translator can decode and emit bytes on other Python platforms, but its
native runner currently implements only the Windows x64 ABI. Native tests
skip elsewhere; a skipped run is not evidence of working native execution.

## Exact supported subset

| Input | Supported form |
|---|---|
| MOVZ | 64-bit destination, 16-bit immediate, LSL 0/16/32/48 |
| ADD, SUB | 64-bit shifted-register encoding, LSL #0, no flag update |
| AND, ORR, EOR | 64-bit shifted-register encoding, LSL #0, no inversion/flags |
| NOP | Canonical encoding |
| RET | Exact RET X30 encoding, only as final block terminator |

The context contains X0 through X30. Operand register 31 is XZR: reads are
zero and writes are discarded. Arithmetic wraps modulo 2^64. Both operands
are loaded before the destination is stored, including aliased operands.

**RET is a harness convention:** the final RET X30 ends the translated block,
returns guest X0 to Python and leaves the resulting register context available.
It does not branch to the guest address in X30. X30 can otherwise hold data.
This is not full AArch64 control-flow or calling-convention emulation.

No guest loads/stores, stack pointer, branches/loops, flags, 32-bit forms,
floating point, SIMD, syscalls, exceptions, OS/ELF loader or arbitrary Arm
binaries. An input must be a non-empty sequence of little-endian 4-byte
words, at most 4096 instructions, ending with RET. Unsupported forms and
trailing bytes/instructions are rejected before execution.

## Pipeline and implementation decisions

```text
A64 bytes -> validated instructions -> x86-64 bytes -> native leaf function
                        |
                        +-> Python reference interpreter -> compare 31 registers
```

- `decode`: bit masks identify the accepted forms; operand fields become
  explicit instruction objects. There is no general assembler frontend.
- `compile_block`: every guest register lives in a uint64 context slot.
  Windows RCX holds the context pointer; volatile RAX/RDX are scratch.
  This is simple and transparent, with extra loads/stores, not an optimising
  register allocator.
- `interpret`: Python integer operations model the same small subset with
  explicit 64-bit masking. It shares the decoder, so agreement checks the
  emitter/runtime path but is not independent proof of decoder correctness.
- `execute`: reserves a writable allocation, emits code, switches it to
  executable/read-only, flushes the instruction cache, calls it, then frees
  the allocation. The emitted function touches no nonvolatile host registers
  or stack allocation and makes no nested calls.

`--emit build/output.bin` writes host bytes for inspection without implying
an executable file format. This project does not provide a general native-code
sandbox or a production JIT.

## Validation and reproduction

See [VALIDATION.md](VALIDATION.md) for the first observed run. Tests cover:

- known encodings and one exact emitted x86 ADD sequence;
- immediate shifts and whole-register replacement;
- unsupported opcode/form rejection and block boundaries;
- native overflow/underflow, operand order, aliases, XZR and X30;
- 200 deterministic generated blocks compared across all 31 guest registers;
- LLVM-assembled example fixtures checked against explicit expected results.

No speedup, broad compatibility or production-readiness claim is made.

To regenerate the Arm fixtures with LLVM installed (`clang`, `llvm-objcopy`
and `llvm-objdump` on PATH):

```powershell
New-Item -ItemType Directory -Force build
clang --target=aarch64-none-elf -c examples/add42.s -o build/add42.o
llvm-objcopy -O binary --only-section=.text build/add42.o examples/add42.bin
llvm-objdump -d build/add42.o
clang --target=aarch64-none-elf -c examples/logic.s -o build/logic.o
llvm-objcopy -O binary --only-section=.text build/logic.o examples/logic.bin
llvm-objdump -d build/logic.o
```

## Next learning steps

1. Walk through [LEARNING.md](LEARNING.md), predict a block result and explain
   the register slots and XZR behaviour before adding features.
2. Add one new instruction form with edge-case tests and an assembled fixture.
   Good candidates are MOVK or a nonzero LSL operand shift.
3. Check accepted blocks against an independent AArch64 execution oracle
   (hardware or an emulator), so decoder and semantics errors are less coupled.
4. Study branches, flags and guest PC explicitly before attempting loops.

Keep a contribution log for changes actually understood, implemented or
tested by the learner. AI-assisted implementation should remain attributed.

## References

- [Arm Instruction Set Reference Guide](https://documentation-service.arm.com/static/6245c734b059dc5ff9a8bdab)
- [Microsoft x64 instructions](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/x64-instructions)
- [Windows x64 calling convention](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention)
- [VirtualProtect and instruction-cache requirements](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualprotect)

MIT licensed. This is an independent learning project, not affiliated with Arm.
