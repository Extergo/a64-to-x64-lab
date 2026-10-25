# First validation — 25 October 2026

Host: Windows x86-64, 64-bit Python. LLVM clang 22.1.8.

Observed first implementation check:

- 10 unittest methods passed, including 200 seeded generated straight-line
  blocks compared with the reference across all 31 guest registers.
- Both `.s` fixtures assembled with `clang --target=aarch64-none-elf`;
  `.text` extracted using `llvm-objcopy` and decoded by `llvm-objdump`.
- `add42.bin` executed as translated native x86-64 code: X0 = 42; all guest
  registers matched the reference.
- `logic.bin` also executed and matched the complete reference state.

Final fixture-inclusive run: **11 test methods passed**, with no skips on
this Windows x86-64 host. The logic fixture returned X0 = 281474976710656
(2^48). The 200 deterministic generated blocks are cases within one method,
not 200 separate unittest methods.

Limits: no independent Arm execution oracle; shared-decoder reference;
no benchmarks, cross-platform native testing or real-program compatibility
testing. Generated blocks are constrained to the documented instruction subset.
