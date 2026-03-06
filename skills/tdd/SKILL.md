---
name: tdd
description: Test-Driven Development discipline — Red-Green-Refactor cycle
trigger: when writing code that should be test-driven, or when TDD Guard is active
---

# TDD Skill — Red-Green-Refactor

Test-Driven Development enforces code quality through a strict write-test-first cycle.
This skill defines the rules and workflow for TDD within curdx.

## The Cycle

### 1. Red — Write ONE Failing Test

- Add exactly **one** new test case that captures the next behavior
- The test MUST fail before any implementation (confirms the test is meaningful)
- Never add multiple tests at once — each test drives one small step
- Exception: initial test file setup (imports, describe block, beforeEach) is allowed in one go

### 2. Green — Minimal Implementation

- Write the **minimum** code to make the failing test pass
- Do NOT add behavior beyond what the current test requires
- Map test failure types to implementation scope:
  - `not defined` / `cannot find` → create empty class/function/module
  - `not a function` / `has no method` → add method stub
  - assertion error (wrong value) → implement minimal logic
  - no test output → STOP, go back to Red phase
- Simple stubs for imports, constructors, and type definitions are always allowed

### 3. Yellow (Refactor) — Improve Under Green

- Refactor ONLY when all related tests pass (green bar)
- Refactoring may touch BOTH test and implementation code
- Allowed: rename, extract, restructure, improve types, add abstractions
- Forbidden: introduce NEW behavior (that requires a new test)
- After refactoring, all tests must still pass

## File Classification

**Test files** — contain `.test.`, `.spec.`, `_test.`, or live under `test/`, `tests/`, `__tests__/`:
- Writing/editing test files is always allowed (Red phase)
- Adding ONE test is always valid, even without prior test output

**Implementation files** — all other source files:
- Edits must be justified by a failing test
- New files need a corresponding test first (unless they are stubs/types/interfaces)

**Ignored files** — docs, config, assets (*.md, *.json, *.yaml, etc.):
- Never subject to TDD checks

## Guard Commands

Users can toggle TDD enforcement at any time:

- `tdd on` — enable TDD Guard (test-first enforcement)
- `tdd off` — disable TDD Guard

State persists across sessions in `~/.curdx/tdd-guard/config.json`.

## Common Violations

| Violation | Example | Fix |
|-----------|---------|-----|
| Multiple tests at once | Adding 3 test cases in one edit | Add one, make it pass, then add the next |
| Over-implementation | Building full feature before test fails | Delete excess code, let failing test guide you |
| Premature implementation | Writing impl before any test exists | Write a failing test first |
| Refactor without green | Restructuring while tests fail | Fix failing tests first, then refactor |

## Integration with curdx Workflow

- **POC-first tasks** (GREENFIELD): use TDD after initial spike — Make It Work, then add tests
- **Standard tasks** (MID_SIZED, REFACTOR): use TDD from the start
- **TRIVIAL tasks**: TDD optional, but recommended for logic changes
- The `spec-executor` agent follows TDD when the task type calls for it
- `file_checker.py` handles formatting/linting separately from TDD enforcement
