---
name: vue2-maintenance
description: Use when maintaining legacy Vue 2 codebases (including Vue 2.7), fixing Vue2-specific issues, or preparing incremental migration plans toward Vue 3.
---

# Vue 2 Maintenance

Use this skill only for Vue 2 projects.

## When To Trigger

- `package.json` has `vue@2.x`
- code relies on Vue 2 options API and legacy lifecycle hooks
- project uses `vue-router@3`, `vuex@3`, or old plugin ecosystem

## Working Rules

- Preserve existing Vue 2 behavior first.
- Avoid introducing Vue 3-only APIs into active Vue 2 modules.
- Keep template and reactivity semantics Vue2-compatible.
- Prefer small, low-risk refactors in legacy modules.

## Common Fixes

- Reactivity caveat for object key add:
  - use `this.$set(obj, key, value)` in Vue2 code.
- Array index updates:
  - use `this.$set(arr, index, value)` or `splice`.
- Watcher side effects:
  - isolate async calls and cancel stale requests when possible.

## Migration-Ready Strategy

1. Stabilize core pages and store modules.
2. Remove deprecated patterns (`$on/$off` event bus where possible).
3. Introduce adapter layers around HTTP/API modules.
4. Migrate router/store contracts before component-by-component rewrite.
5. Keep a compatibility matrix for dependencies that block Vue 3.

## Verification

- run existing Vue2 test/build pipeline (e.g. `npm run test`, `npm run build`)
- validate key flows in browser after each risky refactor

