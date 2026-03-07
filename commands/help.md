---
description: Show help for CURDX Specum plugin commands and workflow.
---

# CURDX Specum Help

## Overview

CURDX Specum is a spec-driven development plugin that guides you through research, requirements, design, and task generation phases, then executes tasks autonomously with fresh context per task.

## Commands

| Command | Description |
|---------|-------------|
| `/curdx:start [name] [goal]` | Smart entry point: resume or create new |
| `/curdx:new <name> [goal]` | Create new spec and start research |
| `/curdx:research` | Run/re-run research phase |
| `/curdx:requirements` | Generate requirements (approves research) |
| `/curdx:design` | Generate design (approves requirements) |
| `/curdx:tasks` | Generate tasks (approves design) |
| `/curdx:implement` | Start execution loop (approves tasks) |
| `/curdx:status` | Show all specs and progress |
| `/curdx:switch <name>` | Change active spec |
| `/curdx:cancel` | Cancel active loop, cleanup state |
| `/curdx:mcp-doctor` | Check/install required MCP servers |
| `/curdx:feedback [message]` | Submit feedback or report an issue |
| `/curdx:help` | Show this help |

## Workflow

```
/curdx:new "my-feature"
    |
    v
[Research Phase] - Automatic on new
    |
    v (review research.md)
/curdx:requirements
    |
    v (review requirements.md)
/curdx:design
    |
    v (review design.md)
/curdx:tasks
    |
    v (review tasks.md)
/curdx:implement
    |
    v
[Task-by-task execution with fresh context]
    |
    v
Done!
```

## Quick Start

```bash
# Easiest: use start (auto-detects resume or new)
/curdx:start user-auth Add JWT authentication

# Or resume an existing spec
/curdx:start

# Manual workflow with individual commands:
/curdx:new user-auth Add JWT authentication
/curdx:requirements
/curdx:design
/curdx:tasks
/curdx:implement
```

## Options

### start command
```
/curdx:start [name] [goal] [--fresh] [--quick] [--commit-spec] [--no-commit-spec]
```
- `--fresh`: Force new spec, overwrite if exists (skips "resume or fresh?" prompt)
- `--quick`: Skip interactive phases, auto-generate all specs, start execution immediately
- `--commit-spec`: Commit and push spec files after each phase (default: true in normal mode, false in quick mode)
- `--no-commit-spec`: Explicitly disable committing spec files

The `--commit-spec` setting is stored in `.curdx-state.json` and applies to all subsequent phases (research, requirements, design, tasks).

### new command
```
/curdx:new <name> [goal] [--skip-research]
```
- `--skip-research`: Skip research phase, start with requirements

### phase commands (research, requirements, design, tasks)
```
/curdx:<phase> [spec-name]
```
Phase commands use the `commitSpec` setting from `.curdx-state.json` (set during `/curdx:start`).

### implement command
```
/curdx:implement [--max-task-iterations 5]
```
- `--max-task-iterations`: Max retries per task before failure (default: 5)

### mcp-doctor command
```
/curdx:mcp-doctor [--install-missing] [--scope local|user|project] [--required a,b,c]
```
- `--install-missing`: Auto-install missing known MCP servers (`context7`, `chrome-devtools`)
- Default required MCP servers: `context7`, `chrome-devtools`
- `--scope`: MCP config scope passed to `claude mcp add` (default: `user`)
- `--required`: Override required server list (comma-separated)
- For web-console services (Nacos/RabbitMQ/Grafana/Keycloak/etc.), install `chrome-devtools` MCP first so UI config tasks can run autonomously

## Directory Structure

Specs are stored in `./specs/` by default:
```
./specs/
├── .current-spec           # Active spec name (or full path for multi-dir)
├── my-feature/
│   ├── .curdx-state.json   # Loop state (deleted on completion)
│   ├── .progress.md        # Progress tracking (persists)
│   ├── research.md         # Research findings
│   ├── requirements.md     # Requirements
│   ├── design.md           # Technical design
│   └── tasks.md            # Implementation tasks
```

## Multi-Directory Support

You can organize specs across multiple directories using the `specs_dirs` configuration.

### Configuration

Add `specs_dirs` to your settings file at `.claude/curdx.local.md`:

```yaml
---
specs_dirs:
  - ./specs
  - ./packages/api/specs
  - ./packages/web/specs
---
```

If not configured, defaults to `["./specs"]` for backward compatibility.

### Using --specs-dir Flag

The `start` and `new` commands accept `--specs-dir` to specify where to create a spec:

```bash
# Create spec in default directory (./specs/)
/curdx:start my-feature Some goal

# Create spec in a specific directory
/curdx:start my-feature Some goal --specs-dir ./packages/api/specs
/curdx:new api-auth --specs-dir ./packages/api/specs
```

The specified directory must be listed in `specs_dirs` configuration.

### Monorepo Example

For a monorepo with multiple packages:

```
my-monorepo/
├── .claude/
│   └── curdx.local.md    # specs_dirs config
├── packages/
│   ├── api/
│   │   └── specs/               # API-related specs
│   │       └── auth-feature/
│   └── web/
│       └── specs/               # Web-related specs
│           └── dashboard-feature/
└── specs/                       # Shared/root specs
    └── infrastructure-feature/
```

Settings file:
```yaml
---
specs_dirs:
  - ./specs
  - ./packages/api/specs
  - ./packages/web/specs
---
```

### Disambiguation

When the same spec name exists in multiple directories, commands will prompt for disambiguation:

```
Multiple specs named "auth-feature" found:
  1. ./specs/auth-feature
  2. ./packages/api/specs/auth-feature

Specify the full path to switch:
  /curdx:switch ./packages/api/specs/auth-feature
```

Use the full path to target a specific spec when names are ambiguous.

## Execution Loop

The implement command runs tasks one at a time:
1. Execute task from tasks.md
2. Verify completion
3. Commit changes
4. Update progress
5. Stop and restart with fresh context
6. Continue until all tasks done

This ensures each task has full context without accumulating irrelevant history.

## Sub-Agents

Each phase uses a specialized agent:
- **research-analyst**: Research and feasibility analysis
- **product-manager**: Requirements and user stories
- **architect-reviewer**: Technical design and architecture
- **task-planner**: POC-first task breakdown
- **spec-executor**: Autonomous task execution

## POC-First Workflow

Tasks follow a 4-phase structure:
1. **Phase 1: Make It Work** - POC validation, skip tests
2. **Phase 2: Refactoring** - Clean up code
3. **Phase 3: Testing** - Unit, integration, browser-flow verification (chrome-devtools-mcp)
4. **Phase 4: Quality Gates** - Lint, types, CI

## Troubleshooting

**Spec not found?**
- Run `/curdx:status` to see available specs
- Run `/curdx:switch <name>` to change active spec

**Task failing repeatedly?**
- After 5 attempts, hook blocks with error message
- Fix manually, then run `/curdx:implement` to resume

**Want to restart?**
- Run `/curdx:cancel` to cleanup state
- Progress file is preserved with completed tasks
