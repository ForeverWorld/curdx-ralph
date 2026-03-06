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
