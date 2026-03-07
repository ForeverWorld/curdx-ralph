<div align="center">

<img src="./assets/logo/curdx-logo-en.png" alt="CURDX" width="760" />

# CURDX

**Spec-driven engineering workflow plugin for Claude Code**

[English](./README.md) | [简体中文](./README.zh-CN.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Platform-Claude%20Code-6f42c1)](https://code.claude.com/docs/en/plugins)
[![Quality Gates](https://img.shields.io/badge/CI-Quality%20Gates-2ea44f)](./.github/workflows/quality-gates.yml)
[![Security Scan](https://img.shields.io/badge/Security-Trivy%20Scan-blue)](./.github/workflows/security-scan.yml)

`research -> requirements -> design -> tasks -> implement`

</div>

---

## Overview

CURDX is a production-oriented Claude Code plugin for teams that want a repeatable, auditable, and guarded engineering workflow.

It combines:
- a spec lifecycle (`research` to `implement`)
- autonomous task execution with state tracking
- hook-based safety guardrails
- reusable skills, agents, templates, and references in one repository

## Why Teams Use CURDX

- Consistency: one shared workflow instead of prompt-by-prompt improvisation
- Auditability: explicit state and progress artifacts per spec
- Safety: pre/post hook checks, tool routing, and loop controls
- Throughput: fast path (`--quick`) and robust path (interactive phase-by-phase)
- Extensibility: add commands, skills, and agents without changing core architecture

## Installation

### Option A: Install from Marketplace (like superpowers style)

```text
/plugin marketplace add ForeverWorld/curdx-ralph
/plugin install curdx@curdx-marketplace
```

CLI equivalent:

```bash
claude plugin marketplace add ForeverWorld/curdx-ralph
claude plugin install curdx@curdx-marketplace
```

### Option B: One-click install with preflight checks

```bash
bash scripts/install-curdx.sh
```

Include MCP setup in the same run:

```bash
bash scripts/install-curdx.sh --with-mcp
```

### Option C: Local plugin directory

### 1. Clone the repository

```bash
git clone https://github.com/ForeverWorld/curdx-ralph.git
cd curdx-ralph
```

### 2. Load as Claude Code plugin

```bash
claude --plugin-dir /absolute/path/to/curdx-ralph
```

### 3. Validate plugin contract (recommended)

```bash
claude plugin validate .
```

### Team Auto-Install (project settings)

Add to `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": [
    "github:ForeverWorld/curdx-ralph"
  ],
  "enabledPlugins": [
    "curdx@curdx-marketplace"
  ]
}
```

## Quick Start

### Standard mode (recommended for important features)

```text
/curdx:start user-auth Add JWT authentication
/curdx:requirements
/curdx:design
/curdx:tasks
/curdx:implement
```

### Quick mode (faster, fewer prompts)

```text
/curdx:start user-auth Add JWT authentication --quick
```

## Core Workflow

### Phase chain

1. `research`: constraints, options, feasibility
2. `requirements`: user-facing and system requirements
3. `design`: architecture and implementation strategy
4. `tasks`: executable task breakdown
5. `implement`: autonomous loop with verification and progress updates

### Execution model

- Task-by-task delegation with fresh context per iteration
- Retries with configurable max limits
- Optional iterative recovery mode for failed tasks
- Progress persistence in `.progress.md`

## Command Reference

### Spec lifecycle

| Command | Purpose |
|---|---|
| `/curdx:start [name] [goal]` | Smart entry (resume existing or create new) |
| `/curdx:new <name> [goal]` | Create a new spec directly |
| `/curdx:research` | Run or re-run research |
| `/curdx:requirements` | Generate requirements |
| `/curdx:design` | Generate technical design |
| `/curdx:tasks` | Generate implementation tasks |
| `/curdx:implement` | Start execution loop |
| `/curdx:status` | Show spec status and progress |
| `/curdx:switch <name-or-path>` | Switch active spec |
| `/curdx:cancel [name-or-path]` | Cancel active loop and clean state |

### Supporting commands

| Command | Purpose |
|---|---|
| `/curdx:triage [epic-name] [goal]` | Split large initiatives into dependency-aware specs |
| `/curdx:index` | Index codebase and external resources into specs |
| `/curdx:refactor` | Update spec docs after execution |
| `/curdx:review-pr [aspects]` | Multi-agent PR review |
| `/curdx:mcp-doctor` | Check/install required MCP servers (context7, chrome-devtools) |
| `/curdx:commit` | Create commit |
| `/curdx:commit-push-pr` | Commit, push, and open PR |
| `/curdx:hookify` | Build behavior guard hooks from conversation analysis |
| `/curdx:hookify-list` | List hookify rules |
| `/curdx:hookify-configure` | Enable/disable hookify rules |
| `/curdx:help` | Show command help |

## Important Options

- `/curdx:start`
  - `--fresh`: force new spec
  - `--quick`: skip interactive phase gates
  - `--commit-spec` / `--no-commit-spec`: control spec commits
  - `--specs-dir <path>`: create spec in a configured directory
  - `--tasks-size fine|coarse`: task granularity hint
- `/curdx:implement`
  - `--max-task-iterations <n>`: max retries per task
  - `--max-global-iterations <n>`: safety cap for loop iterations
  - `--recovery-mode`: auto-generate and execute fix tasks on failure

## Spec Storage Model

Default structure:

```text
./specs/
├── .current-spec
└── <spec-name>/
    ├── .curdx-state.json
    ├── .progress.md
    ├── research.md
    ├── requirements.md
    ├── design.md
    └── tasks.md
```

Multi-directory specs are supported via `.claude/curdx.local.md`:

```yaml
---
specs_dirs:
  - ./specs
  - ./packages/api/specs
  - ./packages/web/specs
---
```

## Guardrails and Quality

## MCP Setup

Check MCP readiness:

```bash
bash scripts/mcp-doctor.sh
```

Auto-install missing known MCP servers:

```bash
bash scripts/mcp-doctor.sh --install-missing
```

Run via slash command:

```text
/curdx:mcp-doctor
/curdx:mcp-doctor --install-missing --scope project
```

Default required servers:
- `context7`
- `chrome-devtools`

Control-panel automation:
- For services with web consoles (e.g. Nacos, RabbitMQ, Grafana, Keycloak, Jenkins, Argo CD), CURDX plans MCP browser verification tasks:
  - login/config through `chrome-devtools-mcp`
  - API/CLI readback verification (not UI-only)

### Hook guardrails

- `SessionStart`: context bootstrap and TDD guard
- `PreToolUse`: security reminder, tool redirect, quick-mode constraints
- `PostToolUse`: file checks and context monitor
- `Stop`/`PreCompact`: loop continuity and state persistence

### CI workflows

- [`.github/workflows/quality-gates.yml`](./.github/workflows/quality-gates.yml)
  - syntax checks, plugin contract checks, policy checks, hook behavior tests
- [`.github/workflows/security-scan.yml`](./.github/workflows/security-scan.yml)
  - Trivy vulnerability and secret scanning (`CRITICAL,HIGH`)

### Local validation

```bash
bash -n hooks/scripts/*.sh scripts/*.sh
python3 -m py_compile hooks/scripts/*.py hooks/scripts/_checkers/*.py scripts/ci/*.py tests/hooks/*.py
python3 scripts/ci/check_plugin_manifest.py
python3 scripts/ci/check_claude_plugin_contract.py
python3 scripts/ci/check_skills_frontmatter.py
python3 scripts/ci/check_local_links.py
python3 scripts/ci/check_forbidden_files.py
python3 scripts/ci/check_workflow_hardening.py
python3 -m unittest discover -s tests/hooks -p 'test_*.py'
claude plugin validate .
```

## Relay Overload Auto-Retry

When relay/provider overload errors occur, use:

```bash
bash scripts/claude-auto-retry.sh --stop-on-success
```

Examples:

```bash
bash scripts/claude-auto-retry.sh --preset relay-common --preset cn-relay-common
bash scripts/claude-auto-retry.sh --extra-transient "upstream timeout|provider overloaded"
bash scripts/claude-auto-retry.sh --extra-non-retriable "insufficient quota|account suspended"
```

## Repository Layout

```text
curdx/
├── .claude-plugin/          # plugin metadata
├── commands/                # slash command definitions
├── agents/                  # phase and execution sub-agent prompts
├── hooks/                   # hook wiring and scripts
├── scripts/                 # CI checks and retry utilities
├── skills/                  # reusable skill packs
├── references/              # workflow references
├── templates/               # artifact templates
├── schemas/                 # structured schemas
└── assets/logo/             # README logo assets
```

## Troubleshooting

- `/curdx:start` stopped unexpectedly:
  - Run `/curdx:status`; it usually waits for a phase transition or approval gate.
- Task loop keeps failing:
  - Retry with `/curdx:implement --recovery-mode` or clear state via `/curdx:cancel`.
- Ambiguous spec name across directories:
  - Use full path in `/curdx:switch <spec-path>`.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution and validation requirements.

## License

MIT, see [LICENSE](./LICENSE).
