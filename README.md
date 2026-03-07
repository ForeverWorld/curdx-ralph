# CURDX

Unified spec-driven development plugin for Claude Code.

Combines the best of:
- **curdx**: Spec workflow, research, requirements, design, tasks, implementation
- **tdd-guard**: AI-driven TDD compliance
- **pilot-shell**: Quality infrastructure (linting, formatting, context monitoring)
- **superpowers**: Systematic debugging, brainstorming, verification, parallel agents
- **claude-code plugins**: Git commands, PR review, frontend design, hookify, security

## Commands

| Command | Description |
|---------|-------------|
| `/curdx:start` | Smart entry point for spec-driven workflow |
| `/curdx:research` | Research phase |
| `/curdx:requirements` | Requirements generation |
| `/curdx:design` | Technical design |
| `/curdx:tasks` | Task generation |
| `/curdx:implement` | Execution loop |
| `/curdx:triage` | Epic decomposition |
| `/curdx:index` | Code indexing |
| `/curdx:status` | Status query |
| `/curdx:switch` | Switch spec |
| `/curdx:cancel` | Cancel and cleanup |
| `/curdx:feedback` | Feedback loop |
| `/curdx:refactor` | Refactoring workflow |
| `/curdx:help` | Help |
| `/curdx:commit` | Git commit |
| `/curdx:commit-push-pr` | Commit + Push + PR |
| `/curdx:clean-gone` | Clean deleted branches |
| `/curdx:review-pr` | PR review |
| `/curdx:hookify` | Custom hook creation |
| `/curdx:hookify-list` | List hooks |
| `/curdx:hookify-configure` | Configure hooks |
| `/curdx:hookify-help` | Hookify help |

## Usage

```bash
claude --plugin-dir /path/to/curdx
```

## Hook Logs

CURDX hook logs are written under:

- `~/.curdx/logs/hooks.log` (global)
- `~/.curdx/logs/hooks.jsonl` (global structured stream for AI)
- `~/.curdx/logs/hooks.<hook_name>.log` (per-hook split logs)
- `~/.curdx/logs/hooks.<hook_name>.jsonl` (per-hook structured stream)
- `~/.curdx/logs/sessions/<session>/...` (session-scoped copies)

Every line includes `session`, `pid`, decision, and duration metadata for easier tracing.

### Logging controls

- `CURDX_HOOK_LOG=0` disable hook logging completely
- `CURDX_HOOK_LOG_LEVEL=DEBUG|INFO|WARN|ERROR` set minimum log level (default: `DEBUG`)
- `CURDX_HOOK_LOG_SPLIT=0` disable per-hook split files (keep global `hooks.log`)
- `CURDX_HOOK_LOG_JSONL=0` disable JSONL output
- `CURDX_HOOK_LOG_SESSION_SPLIT=0` disable session-scoped file copies

### Quick debug commands

```bash
tail -f ~/.curdx/logs/hooks.log
tail -f ~/.curdx/logs/hooks.tool_redirect.log
```

### AI log analysis

Use the built-in analyzer to summarize blocks/errors/slow hooks without reading raw logs:

```bash
python3 hooks/scripts/analyze_hook_logs.py --since-minutes 60
python3 hooks/scripts/analyze_hook_logs.py --session <session-id> --since-minutes 180
```
