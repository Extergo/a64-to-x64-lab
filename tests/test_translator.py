import random
import struct
import unittest
from pathlib import Path

from translator import (BASES, MASK64, NOP, RET, TranslationError, compile_block,
                        decode, execute, interpret, native_available)


def words(*items):
    return b"".join(struct.pack("<I", word) for word in items)


def movz(rd, value, halfword=0):
    return 0xD2800000 | (halfword << 21) | (value << 5) | rd


def binary(op, rd, rn, rm):
    return BASES[op] | (rm << 16) | (rn << 5) | rd


class DecoderTests(unittest.TestCase):
    def test_known_add42_encoding(self):
        # Confirmed independently against LLVM's AArch64 assembler in validation.
        data = words(0xD2800500, 0xD2800041, 0x8B010000, RET)
        self.assertEqual([i.op for i in decode(data)], ["MOVZ", "MOVZ", "ADD", "RET"])
        self.assertEqual(interpret(data)[0], 42)

    def test_movz_halfwords_replace_whole_register(self):
        for shift in range(4):
            state = interpret(words(movz(5, 0xABCD, shift), RET), [MASK64] * 31)
            self.assertEqual(state[5], 0xABCD << (shift * 16))

    def test_rejects_other_instruction_forms(self):
        rejected = [0x14000000, 0xF9400020, 0x91000400, 0xAB010000,
                    0x0B010000, 0x8B010400, 0x8B410000, 0xAA210000,
                    0xD65F0000, 0xFFFFFFFF]
        for word in rejected:
            with self.subTest(word=hex(word)), self.assertRaises(TranslationError):
                compile_block(words(word, RET))

    def test_requires_bounded_complete_block(self):
        for data in (b"", b"abc", words(NOP), words(RET, NOP), words(*([NOP] * 4096), RET)):
            with self.subTest(size=len(data)), self.assertRaises(TranslationError):
                decode(data)

    def test_exact_native_add_encoding(self):
        expected = bytes.fromhex("48 8b 81 00 00 00 00 48 8b 91 08 00 00 00 "
                                 "48 01 d0 48 89 81 00 00 00 00 48 8b 81 00 00 00 00 c3")
        self.assertEqual(compile_block(words(binary("ADD", 0, 0, 1), RET)), expected)


@unittest.skipUnless(native_available(), "Native runner requires Windows x86-64")
class NativeTests(unittest.TestCase):
    def compare(self, data, initial=None):
        result, actual = execute(data, initial)
        expected = interpret(data, initial)
        self.assertEqual(actual, expected)
        self.assertEqual(result, expected[0])
        return actual

    def test_native_add42(self):
        actual = self.compare(words(movz(0, 40), movz(1, 2), binary("ADD", 0, 0, 1), RET))
        self.assertEqual(actual[0], 42)

    def test_llvm_assembled_fixtures(self):
        examples = Path(__file__).resolve().parents[1] / "examples"
        expected_add = words(0xD2800500, 0xD2800041, 0x8B010000, RET)
        self.assertEqual((examples / "add42.bin").read_bytes(), expected_add)
        self.assertEqual(self.compare(expected_add)[0], 42)
        logic = (examples / "logic.bin").read_bytes()
        self.assertEqual(self.compare(logic)[0], 1 << 48)

    def test_wraparound_and_subtraction_operand_order(self):
        for op, a, b, expected in (("ADD", MASK64, 1, 0), ("SUB", 0, 1, MASK64),
                                    ("SUB", 9, 4, 5)):
            initial = [0] * 31
            initial[1:3] = [a, b]
            actual = self.compare(words(binary(op, 0, 1, 2), RET), initial)
            self.assertEqual(actual[0], expected)

    def test_zero_register_and_aliases(self):
        for op in BASES:
            for rd, rn, rm in ((0, 0, 0), (30, 30, 1), (0, 31, 31),
                               (31, 1, 2), (0, 31, 2), (0, 1, 31), (2, 1, 2)):
                self.compare(words(binary(op, rd, rn, rm), RET), list(range(31)))
        self.compare(words(movz(31, 0xFFFF, 3), NOP, RET), [MASK64] * 31)

    def test_native_shifted_immediate(self):
        for shift in range(4):
            self.compare(words(movz(30, 0xF00D, shift), binary("ADD", 0, 30, 31), RET))

    def test_200_random_blocks_full_state(self):
        rng = random.Random(20261025)
        for case in range(200):
            initial = [rng.getrandbits(64) for _ in range(31)]
            block = []
            for _ in range(rng.randint(1, 40)):
                if rng.randrange(4) == 0:
                    block.append(movz(rng.randrange(32), rng.randrange(65536), rng.randrange(4)))
                else:
                    block.append(binary(rng.choice(list(BASES)), rng.randrange(32),
                                        rng.randrange(32), rng.randrange(32)))
            with self.subTest(case=case):
                self.compare(words(*block, RET), initial)


if __name__ == "__main__":
    unittest.main()
