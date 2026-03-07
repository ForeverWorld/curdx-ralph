# CURDX

[English](./README.md) | [简体中文](./README.zh-CN.md)

CURDX is a **Claude Code** plugin repository built to standardize the full path from idea to delivery:

- use specs to drive research, requirements, design, and task planning
- enforce quality guardrails with hooks during the coding session (TDD, security, context, tool usage)
- package repeatable engineering actions as commands (implementation, refactoring, review, PR workflow)
- bring reusable domain knowledge through skills

If you want a reusable and auditable engineering workflow inside Claude Code, this repo is designed for exactly that.

## When CURDX is a Good Fit

- You want consistent spec-driven development across projects.
- You want quality constraints during AI coding, not only after code is written.
- You need an extensible combination of commands, agents, and skills.
- You want to turn team practices into reusable plugin behavior.

## Core Capabilities

### 1) Spec Workflow (Main CURDX Path)

End-to-end flow: `research -> requirements -> design -> tasks -> implement`

- create new specs, resume execution, switch specs, and manage multi-directory specs
- execute task loops with progress tracking
- break down large initiatives with epic triage

### 2) Hook-Based Guardrails

CURDX wires multiple lifecycle hooks (see `hooks/hooks.json`):

- `SessionStart`: load context and run TDD guard
- `PreToolUse`: security reminder, tool routing, quick-mode guard
- `PostToolUse`: file checks and context monitoring
- `UserPromptSubmit`: TDD guard and hookify rules
- `PreCompact` / `Stop`: state persistence and shutdown checks

### 3) Command Set

The repo ships practical slash commands for day-to-day engineering:

- spec workflow commands
- Git/PR support commands
- hookify rule management commands
- review and refactor commands

### 4) Skills Library

`skills/` contains reusable skill packs for backend, frontend, and engineering topics (`nextjs`, `spring-boot`, `vitest`, `vue`, `typescript-core`, etc.).

## Quick Start

### Prerequisites

- Claude Code installed
- `bash` and `python3` available (used by hooks and validation scripts)
- recommended: run inside a Git repository

### Install and Load as Plugin

```bash
git clone https://github.com/ForeverWorld/curdx-ralph.git
cd curdx-ralph

claude --plugin-dir /absolute/path/to/curdx-ralph
```

### First Run

In Claude, run:

```text
/curdx:start my-feature your goal description
```

Then continue through the workflow:

```text
/curdx:requirements
/curdx:design
/curdx:tasks
/curdx:implement
```

## Command Reference

### Spec Workflow

| Command | Description |
| --- | --- |
| `/curdx:start [name] [goal]` | Smart entry (new or resume) |
| `/curdx:new <name> [goal]` | Create a new spec |
| `/curdx:research` | Research phase |
| `/curdx:requirements` | Requirements phase |
| `/curdx:design` | Design phase |
| `/curdx:tasks` | Task planning phase |
| `/curdx:implement` | Execution loop |
| `/curdx:status` | Show current status |
| `/curdx:switch <name>` | Switch active spec |
| `/curdx:cancel` | Cancel and clean state |
| `/curdx:triage` | Decompose a large goal into specs |
| `/curdx:refactor` | Sync spec docs after implementation |
| `/curdx:index` | Build index hints |
| `/curdx:feedback` | Submit feedback |
| `/curdx:help` | Help |

### Delivery and Review

| Command | Description |
| --- | --- |
| `/curdx:commit` | Create a commit |
| `/curdx:commit-push-pr` | Commit + push + open PR |
| `/curdx:review-pr` | PR review workflow |
| `/curdx:clean-gone` | Remove local branches deleted on remote |

### Hookify

| Command | Description |
| --- | --- |
| `/curdx:hookify` | Create hook rules |
| `/curdx:hookify-list` | List configured rules |
| `/curdx:hookify-configure` | Configure rules interactively |
| `/curdx:hookify-help` | Hookify help |

For detailed arguments and examples, see [commands/help.md](./commands/help.md).

## Repository Layout

```text
curdx/
├── .claude-plugin/         # plugin metadata (plugin.json)
├── commands/               # slash command definitions
├── agents/                 # sub-agent prompts
├── hooks/
│   ├── hooks.json          # hook event wiring
│   └── scripts/            # hook scripts
├── skills/                 # reusable skills
├── references/             # workflow references
├── templates/              # generation templates
└── scripts/ci/             # CI checks
```

## Hook Logs and Debugging

Default log locations:

- `~/.curdx/logs/hooks.log`
- `~/.curdx/logs/hooks.jsonl`
- `~/.curdx/logs/hooks.<hook_name>.log`
- `~/.curdx/logs/hooks.<hook_name>.jsonl`
- `~/.curdx/logs/sessions/<session>/...`

Useful env vars:

- `CURDX_HOOK_LOG=0`: disable hook logging
- `CURDX_HOOK_LOG_LEVEL=DEBUG|INFO|WARN|ERROR`: minimum log level
- `CURDX_HOOK_LOG_SPLIT=0`: disable per-hook split logs
- `CURDX_HOOK_LOG_JSONL=0`: disable JSONL output
- `CURDX_HOOK_LOG_SESSION_SPLIT=0`: disable per-session split logs

Live tail:

```bash
tail -f ~/.curdx/logs/hooks.log
tail -f ~/.curdx/logs/hooks.tool_redirect.log
```

Summarize logs:

```bash
python3 hooks/scripts/analyze_hook_logs.py --since-minutes 60
python3 hooks/scripts/analyze_hook_logs.py --session <session-id> --since-minutes 180
```

## CI and Local Validation

GitHub Actions (`.github/workflows/quality-gates.yml`) validates:

- shell/python syntax in hook scripts
- plugin manifest metadata
- skill frontmatter
- local markdown links

Run locally:

```bash
bash -n hooks/scripts/*.sh
python3 -m py_compile hooks/scripts/*.py hooks/scripts/_checkers/*.py scripts/ci/*.py
python3 scripts/ci/check_plugin_manifest.py
python3 scripts/ci/check_skills_frontmatter.py
python3 scripts/ci/check_local_links.py
```

## Development Notes

### Add a Command

1. Create a new `*.md` in `commands/`
2. Fill frontmatter (at least `description`)
3. Update README/help docs for discoverability

### Add a Hook

1. Register event + matcher in `hooks/hooks.json`
2. Add implementation script in `hooks/scripts/`
3. Run syntax checks locally
4. Verify log output and behavior

### Add a Skill

1. Create `skills/<skill-name>/SKILL.md`
2. Keep frontmatter complete
3. Validate with `scripts/ci/check_skills_frontmatter.py`

## FAQ

### `/curdx:start` stops and does not continue automatically

Run `/curdx:status` first. In most cases, CURDX is waiting for your confirmation before moving to the next phase.

### Task loop keeps failing

Use `/curdx:cancel` to clean current state, then resume with `/curdx:start` or `/curdx:implement`.

### Hooks feel too strict during exploration

Tune behavior with env vars first. Avoid deleting hooks directly unless you are intentionally removing policy.

## Contributing

Issues and PRs are welcome. In PR descriptions, include:

- motivation
- scope (`commands`, `hooks`, `skills`, etc.)
- verification steps (local commands or screenshots)

## License

`.claude-plugin/plugin.json` currently declares `MIT`.
For public distribution, add a root `LICENSE` file to remove ambiguity.
