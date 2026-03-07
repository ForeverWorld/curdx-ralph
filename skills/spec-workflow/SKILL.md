---
name: spec-workflow
description: This skill should be used when the user asks to "build a feature", "create a spec", "start spec-driven development", "run research phase", "generate requirements", "create design", "plan tasks", "implement spec", "check spec status", or needs guidance on the spec-driven development workflow.
version: 0.1.0
license: MIT
compatibility: Claude Code
metadata:
  author: curdx
  maintainer: curdx
---

# Spec Workflow Skill

Spec-driven development workflow for building features through research, requirements, design, and task phases.

## When to Use

Use these commands when user wants to:
- Build a new feature or system
- Create technical specifications
- Plan development work
- Track spec progress
- Execute spec-driven implementation

## Commands

### Starting Work
- `/curdx:start [name] [goal]` - Start or resume a spec (smart entry point)
- `/curdx:new <name> [goal]` - Create new spec and begin research

### Spec Phases
- `/curdx:research` - Run research phase
- `/curdx:requirements` - Generate requirements from research
- `/curdx:design` - Generate technical design
- `/curdx:tasks` - Generate implementation tasks

### Execution
- `/curdx:implement` - Start autonomous task execution

### Management
- `/curdx:status` - Show all specs and progress
- `/curdx:switch <name>` - Change active spec
- `/curdx:cancel` - Cancel active execution

### Help
- `/curdx:help` - Show plugin help

## Phase Flow

See `references/phase-transitions.md` for detailed phase flow documentation.
