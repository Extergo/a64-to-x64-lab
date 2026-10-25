# First walkthrough

Start with the demo's four A64 words (shown in hexadecimal, not byte order):

```text
d2800500    movz x0, #40
d2800041    movz x1, #2
8b010000    add x0, x0, x1
d65f03c0    ret
```

`add42.bin` stores each word little-endian: the first word's bytes are
`00 05 80 d2`. The decoder reads a 32-bit word with `struct.unpack_from`.

For the ADD word, extract and check:

- `word & 31`: destination X0.
- `(word >> 5) & 31`: first source X0.
- `(word >> 16) & 31`: second source X1.
- The other accepted bits identify 64-bit ADD, no flags, LSL #0.

The host function receives a pointer to 31 uint64 register slots, rather
than pretending Arm and x86 registers correspond one-to-one. For the ADD:

```asm
mov rax, [rcx + 0]     ; guest X0
mov rdx, [rcx + 8]     ; guest X1
add rax, rdx
mov [rcx + 0], rax     ; guest X0 = 42
```

This works even when the destination aliases a source because both inputs
are read before the output is written. Register 31 is special: it reads as
zero and a store to it is ignored. It is not the stack pointer in these forms.

Questions to answer by editing an example and running it:

1. What happens if you swap the ADD for SUB?
2. Why does `0 - 1` become `18446744073709551615` in a 64-bit register?
3. Why is `add xzr, x0, x1` different from writing to X30?
4. Why would an ADD-immediate decoder need special care for register 31?
5. Why is interpreter/native agreement insufficient to prove the decoder?

Your first small contribution could be adding a new example with an expected
result and explaining each word and host instruction. A more substantial
next change is MOVK: unlike MOVZ, it preserves the other destination bits.
Write the preservation tests before implementing it.
