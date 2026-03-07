# Web Control Panel Automation (MCP-Only)

> Used by: research-analyst, task-planner

## Purpose

Some infrastructure is configured primarily through a web control panel.
For these cases, the workflow must include browser automation through MCP `chrome-devtools`.
This reference is generic and applies to any service control panel, not only Nacos/RabbitMQ.

Use `${CLAUDE_PLUGIN_ROOT}/references/control-panel-service-catalog.md` as the detection baseline.

## Required Research Output

When a spec includes any control-panel service, `research.md` must include:

```markdown
## Control Panel Targets

| Service | URL | Auth Source | Bootstrap Creds | Config Goal | Verify Method |
|---------|-----|-------------|-----------------|-------------|---------------|
| <service-name> | <panel-url> | <env/file/secret source> | <bootstrap or N/A> | <goal-specific action> | <api/cli readback command> |
```

Minimum fields:
- URL (explicit host + port)
- Auth source (where username/password/token comes from)
- Target configuration action
- Non-UI verification method (API/CLI)

## Task Generation Rules

For each control-panel service, generate explicit tasks:

1. **CP1 Startup [VERIFY]**
- Start dependency stack and wait for panel readiness (HTTP 200 or expected login page marker).

2. **CP2 Browser Config [VERIFY]**
- Use `chrome-devtools-mcp` to:
  - open panel URL
  - login with credentials from env/config
  - perform required config actions
  - capture evidence (screenshot or visible value check)

3. **CP3 API/CLI Verify [VERIFY]**
- Verify resulting configuration via service API/CLI (not UI-only proof).

4. **CP4 Cleanup [VERIFY]**
- Stop background services and clean temporary state.

## Guardrails

- Never rely on manual verification text ("manually click/check").
- Never hardcode production credentials in task files.
- If MCP `chrome-devtools` is unavailable, mark as blocked and instruct:
  - `/curdx:mcp-doctor --install-missing`
- Treat documented defaults as bootstrap hints only; resolve real URL/auth from project config.
