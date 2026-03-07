---
description: Check required MCP servers and optionally auto-install missing ones.
argument-hint: [--install-missing] [--scope local|user|project] [--required a,b,c]
allowed-tools: [Bash, Read]
---

# MCP Doctor

Diagnose MCP readiness for CURDX and optionally auto-install missing servers.

Default required servers:
- `context7`
- `chrome-devtools`

## Behavior

1. Parse `$ARGUMENTS` and pass through supported flags:
   - `--install-missing`
   - `--scope <local|user|project>`
   - `--required <a,b,c>`
   - `--context7-transport <stdio|http>`
2. Run:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/mcp-doctor.sh" <parsed-args>
   ```
3. Return the output summary to the user.
4. If installation failed due to missing prerequisites, explain next steps:
   - `claude` CLI not found
   - `npx` not found (for stdio transport)
   - missing `CONTEXT7_API_KEY` when user expects authenticated access

## Examples

```text
/curdx:mcp-doctor
/curdx:mcp-doctor --install-missing
/curdx:mcp-doctor --install-missing --scope project
/curdx:mcp-doctor --required context7,my-mcp
/curdx:mcp-doctor --required context7,chrome-devtools
/curdx:mcp-doctor --install-missing --context7-transport http
```
