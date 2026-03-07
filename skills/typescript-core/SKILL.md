---
name: typescript-core
description: Use when working on TypeScript or TSX code, tsconfig settings, type errors, or API contracts. Focus on strict typing, safe refactors, and pragmatic type design.
---

# TypeScript Core

Use this skill when editing `*.ts`, `*.tsx`, or `tsconfig*.json`.

## Goals

- Keep runtime behavior stable while improving type safety.
- Prefer clear, maintainable types over type-level tricks.
- Catch problems at compile time, not in production.

## Workflow

1. Identify boundary types first:
   - API request/response
   - DB/result DTOs
   - public function signatures
2. Narrow unknown data early:
   - parse and validate at boundaries
   - avoid propagating `any`
3. Model domain with explicit unions and discriminators.
4. Refactor call sites with compiler guidance.
5. Run type checks before finishing.

## Rules

- Prefer `unknown` over `any`.
- Prefer discriminated unions over boolean flag combinations.
- Use `satisfies` for object shape checks without widening literals.
- Keep generics minimal and purposeful.
- Do not silence errors with broad assertions unless unavoidable.

## Patterns

```ts
type Result<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };
```

```ts
const config = {
  retries: 3,
  mode: "strict",
} as const satisfies { retries: number; mode: "strict" | "loose" };
```

```ts
function assertNever(x: never): never {
  throw new Error(`Unhandled case: ${String(x)}`);
}
```

## Verification

- `pnpm tsc --noEmit`
- or project-specific typecheck command from `package.json`

