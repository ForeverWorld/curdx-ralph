#!/usr/bin/env python3
"""Validate .claude-plugin/plugin.json core metadata."""

from __future__ import annotations

import json
from pathlib import Path

PLUGIN_PATH = Path('.claude-plugin/plugin.json')
REQUIRED_KEYS = ('name', 'version', 'description', 'author', 'repository', 'license', 'keywords')


def main() -> int:
    if not PLUGIN_PATH.exists():
        print(f'ERROR: missing {PLUGIN_PATH}')
        return 1

    try:
        manifest = json.loads(PLUGIN_PATH.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        print(f'ERROR: invalid JSON in {PLUGIN_PATH}: {exc}')
        return 1

    missing = [k for k in REQUIRED_KEYS if k not in manifest]
    if missing:
        print(f"ERROR: {PLUGIN_PATH} missing keys: {', '.join(missing)}")
        return 1

    if not isinstance(manifest.get('keywords'), list) or not manifest['keywords']:
        print('ERROR: plugin.json keywords must be a non-empty array')
        return 1

    if not isinstance(manifest.get('author'), dict) or not manifest['author'].get('name'):
        print('ERROR: plugin.json author must include non-empty name')
        return 1

    print('OK: plugin manifest metadata looks good')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
