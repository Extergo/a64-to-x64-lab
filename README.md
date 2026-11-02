<div align="center">

# A64 → X64 Lab

### An independent systems programming challenge in Rust

Decode an instruction. Understand its behaviour. Translate it. Prove the result.

![Language: Rust](https://img.shields.io/badge/language-Rust-c45508?logo=rust&logoColor=white)
![Status: rewrite planned](https://img.shields.io/badge/status-rewrite_planned-64748b)
![Challenge: no LLM-assisted coding](https://img.shields.io/badge/challenge-no_LLM--assisted_coding-2563eb)

[The challenge](#the-challenge) · [Project scope](#project-scope) · [Milestones](#milestones) · [Development notes](#development-notes)

</div>

---

> [!NOTE]
> **Current status: preparing a fresh Rust implementation.** The previous implementation has been removed from the current branch. Progress and results will be documented as the rewrite develops.

## The challenge

I'm rebuilding this project from scratch in **Rust**, with **no LLM-assisted coding** for the new implementation.

The challenge is to understand the decisions all the way through: how an AArch64 instruction is encoded, what it does to machine state, how that behaviour can be represented on x86-64, and how to check that the translation is correct.

I want the difficult parts to be part of the learning: reading specifications, writing the code, investigating mistakes, and explaining why a solution works. It should be a demanding, enjoyable way to build confidence in Rust and computer architecture.

### The no-LLM coding rule

| Part of the rewrite | Commitment |
| :--- | :--- |
| **Implementation** | Write the Rust code myself, without LLM-generated code, AI coding agents, or generative code completion. |
| **Debugging** | Investigate failures and develop fixes myself, without asking an LLM to diagnose or patch the code. |
| **Tests** | Design the test cases and write the test code myself. |
| **Understanding** | Be able to explain the implementation, its trade-offs, and its limitations in my own words. |

Official documentation, architecture manuals, books, compilers, assemblers, debuggers, and profilers are part of the toolbox. External references and any reused material will be credited.

> [!IMPORTANT]
> **Project history:** an earlier prototype used LLM-assisted coding and remains visible in the Git history. The independent-coding commitment applies to the forthcoming Rust rewrite. The milestones below describe work still to be done.

## Project scope

Start with a small, explicit subset of **AArch64 instructions** and explore translating their behaviour into **x86-64** using Rust.

| Area | What I plan to explore |
| :--- | :--- |
| **Instruction decoding** | Extracting fields from instruction encodings and representing them clearly. |
| **Machine state** | Reasoning about registers, operand widths, and arithmetic behaviour. |
| **Translation** | Mapping supported operations onto x86-64 instructions. |
| **Correctness** | Checking expected results, edge cases, and agreement with independent references. |
| **Rust and safety** | Making ownership, memory handling, and any necessary unsafe boundaries explicit. |

The initial scope is a learning prototype with a documented instruction subset. Each extension should come with a clear explanation and relevant checks.

## Milestones

- [ ] Define the supported instruction subset and expected behaviour.
- [ ] Set up the Rust project and write the first decoding tests.
- [ ] Implement and validate the first supported operation.
- [ ] Build a small, repeatable set of correctness checks.
- [ ] Document unsupported cases and known limitations.
- [ ] Expand the subset as the implementation becomes better understood.

## Development notes

As the project develops, I'll publish:

- **Design decisions:** the options considered and why I chose an approach.
- **Debugging notes:** what failed, how I investigated it, and what fixed it.
- **Validation results:** the checks performed, their results, and what they establish.
- **Limitations:** the supported behaviour and the gaps still to address.

The aim is a project I can walk through confidently, from the first instruction encoding to the final test result.

---

<div align="center">

**Rust · Computer architecture · Instruction translation · Independent learning**

</div>
