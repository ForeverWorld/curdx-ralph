#!/usr/bin/env python3
"""Validate Claude Code plugin contract for this repository."""

from __future__ import annotations

import json
import re
from pathlib import Path

PLUGIN_JSON = Path('.claude-plugin/plugin.json')
MCP_JSON = Path('.claude-plugin/.mcp.json')
HOOKS_JSON = Path('hooks/hooks.json')
COMMANDS_DIR = Path('commands')
SEMVER_RE = re.compile(r'^\d+\.\d+\.\d+$')
PLUGIN_ROOT_CMD_RE = re.compile(r'\$\{CLAUDE_PLUGIN_ROOT\}/([^\s"\'`]+)')
REQUIRED_MCP_SERVERS = {
    'context7',
    'chrome-devtools',
}
MATCHER_REQUIRED_EVENTS = {
    'PreToolUse',
    'PostToolUse',
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def check_plugin_manifest(errors: list[str]) -> None:
    if not PLUGIN_JSON.exists():
        errors.append(f'missing required file: {PLUGIN_JSON}')
        return

    try:
        manifest = load_json(PLUGIN_JSON)
    except Exception as exc:  # noqa: BLE001
        errors.append(f'invalid JSON in {PLUGIN_JSON}: {exc}')
        return

    name = manifest.get('name')
    version = manifest.get('version')

    if not isinstance(name, str) or not name.strip():
        errors.append(f'{PLUGIN_JSON}: name must be non-empty string')
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        errors.append(f'{PLUGIN_JSON}: version must be semver (x.y.z), got {version!r}')


def check_hook_commands(errors: list[str]) -> None:
    if not HOOKS_JSON.exists():
        errors.append(f'missing required file: {HOOKS_JSON}')
        return

    try:
        hooks_doc = load_json(HOOKS_JSON)
    except Exception as exc:  # noqa: BLE001
        errors.append(f'invalid JSON in {HOOKS_JSON}: {exc}')
        return

    hooks = hooks_doc.get('hooks')
    if not isinstance(hooks, dict) or not hooks:
        errors.append(f'{HOOKS_JSON}: "hooks" must be a non-empty object')
        return

    for event_name, event_entries in hooks.items():
        if not isinstance(event_name, str) or not event_name.strip():
            errors.append(f'{HOOKS_JSON}: found invalid event name {event_name!r}')
            continue
        if not isinstance(event_entries, list):
            errors.append(f'{HOOKS_JSON}: event "{event_name}" must be a list')
            continue

        for idx, entry in enumerate(event_entries):
            if not isinstance(entry, dict):
                errors.append(f'{HOOKS_JSON}: {event_name}[{idx}] must be an object')
                continue
            matcher = entry.get('matcher')
            if event_name in MATCHER_REQUIRED_EVENTS:
                if not isinstance(matcher, str) or not matcher.strip():
                    errors.append(f'{HOOKS_JSON}: {event_name}[{idx}] requires non-empty "matcher"')
            elif matcher is not None and (not isinstance(matcher, str) or not matcher.strip()):
                errors.append(f'{HOOKS_JSON}: {event_name}[{idx}] matcher must be a non-empty string')

            hooks_list = entry.get('hooks')
            if hooks_list is None:
                # matcher-only stanzas are invalid without hooks.
                errors.append(f'{HOOKS_JSON}: {event_name}[{idx}] missing "hooks" array')
                continue
            if not isinstance(hooks_list, list):
                errors.append(f'{HOOKS_JSON}: {event_name}[{idx}].hooks must be a list')
                continue

            for hook_idx, hook in enumerate(hooks_list):
                if not isinstance(hook, dict):
                    errors.append(
                        f'{HOOKS_JSON}: {event_name}[{idx}].hooks[{hook_idx}] must be an object'
                    )
                    continue
                if hook.get('type') != 'command':
                    continue
                command = hook.get('command')
                if not isinstance(command, str) or not command.strip():
                    errors.append(
                        f'{HOOKS_JSON}: {event_name}[{idx}].hooks[{hook_idx}] command must be non-empty'
                    )
                    continue

                for rel in PLUGIN_ROOT_CMD_RE.findall(command):
                    target = Path(rel)
                    if not target.exists():
                        errors.append(
                            f'{HOOKS_JSON}: missing referenced hook command path: {target}'
                        )


def check_mcp_config(errors: list[str]) -> None:
    if not MCP_JSON.exists():
        errors.append(f'missing required file: {MCP_JSON}')
        return

    try:
        mcp_doc = load_json(MCP_JSON)
    except Exception as exc:  # noqa: BLE001
        errors.append(f'invalid JSON in {MCP_JSON}: {exc}')
        return

    if isinstance(mcp_doc, dict) and isinstance(mcp_doc.get('mcpServers'), dict):
        # settings-style shape: {"mcpServers": {...}}
        servers = mcp_doc['mcpServers']
    elif isinstance(mcp_doc, dict):
        # plugin-local .mcp.json shape: {"server-name": {...}}
        servers = mcp_doc
    else:
        servers = None

    if not isinstance(servers, dict) or not servers:
        errors.append(f'{MCP_JSON}: must be a non-empty object (or contain non-empty "mcpServers")')
        return

    missing = REQUIRED_MCP_SERVERS - set(servers.keys())
    if missing:
        errors.append(f'{MCP_JSON}: missing required servers: {", ".join(sorted(missing))}')

    for server_name, server_cfg in servers.items():
        if not isinstance(server_cfg, dict):
            errors.append(f'{MCP_JSON}: server "{server_name}" config must be an object')
            continue
        command = server_cfg.get('command')
        if command is not None and (not isinstance(command, str) or not command.strip()):
            errors.append(f'{MCP_JSON}: server "{server_name}" command must be a non-empty string')
        args = server_cfg.get('args')
        if args is not None:
            if not isinstance(args, list) or any(not isinstance(item, str) for item in args):
                errors.append(f'{MCP_JSON}: server "{server_name}" args must be an array of strings')


def check_commands_frontmatter(errors: list[str]) -> None:
    if not COMMANDS_DIR.exists():
        errors.append(f'missing required directory: {COMMANDS_DIR}')
        return

    command_files = sorted(COMMANDS_DIR.glob('*.md'))
    if not command_files:
        errors.append(f'no command markdown files found in {COMMANDS_DIR}')
        return

    for command_file in command_files:
        content = command_file.read_text(encoding='utf-8', errors='replace')
        if not content.startswith('---\n'):
            errors.append(f'{command_file}: missing frontmatter block')
            continue
        marker = content.find('\n---\n', 4)
        if marker == -1:
            errors.append(f'{command_file}: unterminated frontmatter block')
            continue
        frontmatter = content[4:marker]
        if 'description:' not in frontmatter:
            errors.append(f'{command_file}: frontmatter missing description')


def main() -> int:
    errors: list[str] = []
    check_plugin_manifest(errors)
    check_mcp_config(errors)
    check_hook_commands(errors)
    check_commands_frontmatter(errors)

    if errors:
        print('ERROR: Claude plugin contract checks failed:')
        for item in errors:
            print(f'  - {item}')
        return 1

    print('OK: Claude plugin contract checks passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
