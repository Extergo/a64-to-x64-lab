# Contributor instructions

This is a new learning prototype, initially implemented with Codex assistance.
Keep the instruction subset and limitations explicit. Do not describe this as a
general Arm emulator or full compiler. Changes must add relevant semantic and
native differential checks. Preserve XZR, wraparound, register aliasing and the
Windows x64 ABI. Keep the native allocation writable only during emission and
executable/read-only during execution; free it after use.

Before expanding CV claims, distinguish project features, the learner's own
contributions and AI-assisted implementation. Do not copy private application
material or other repositories into this public project.

Run `python -m unittest discover -s tests -v` on Windows x86-64. Tests using the
native runner skip on other platforms; a portable test pass alone does not
establish native execution. The reference interpreter shares the decoder, so
also check fixture encodings against an external assembler when changing it.
