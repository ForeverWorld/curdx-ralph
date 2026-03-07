---
name: echarts-visualization
description: Use when building or debugging Apache ECharts charts in web apps (Vue/React/TS), including option design, performance tuning, interactions, and responsive behavior.
license: MIT
compatibility: Claude Code
metadata:
  author: curdx
  maintainer: curdx
---

# ECharts Visualization

Use this skill for `echarts`/`apache-echarts` tasks.

## Core Objectives

- Correct chart semantics first (axes, series, units, legends).
- Keep chart options maintainable and composable.
- Ensure performance for large or frequently updated datasets.

## Workflow

1. Define data contract:
   - dimensions, units, time zone, null handling.
2. Build minimal working `option`.
3. Add interaction (`tooltip`, `legend`, `dataZoom`, click handlers).
4. Add responsiveness and lifecycle cleanup.
5. Tune performance for real data size.

## Option Design Rules

- Prefer `dataset` + `encode` for multi-series charts.
- Separate base style config from data mapping config.
- Use explicit axis formatting for money/percent/time.
- Keep color palette and theme tokens centralized.

## Performance Rules

- For large line/scatter:
  - set `series.progressive`
  - set `showSymbol: false` for dense lines
- Update with `setOption(next, { notMerge: false, lazyUpdate: true })`.
- Dispose chart on unmount to prevent leaks.

## Framework Integration Notes

- Vue/React:
  - initialize in mounted/effect
  - resize on container change
  - dispose on unmount
- TypeScript:
  - type options with ECharts option types
  - keep formatter functions typed and side-effect free

## Verification

- render check with realistic dataset
- resize check (mobile + desktop)
- interaction check (tooltip/legend/zoom/click)
- memory check (no duplicate chart instance after navigation)

