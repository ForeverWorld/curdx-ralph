#!/usr/bin/env python3
"""Validate basic GitHub Actions hardening rules."""

from __future__ import annotations

import re
from pathlib import Path

USES_RE = re.compile(r'^\s*uses:\s*([^\s#]+)')
SHA_PIN_RE = re.compile(r'@[0-9a-f]{40}$')


def is_external_action(uses_target: str) -> bool:
    return not uses_target.startswith('./') and not uses_target.startswith('docker://')


def validate_workflow(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding='utf-8', errors='replace')
    lines = text.splitlines()

    if not re.search(r'^\s*permissions:\s*$', text, re.MULTILINE):
        errors.append(f'{path}: missing top-level permissions block')

    for lineno, line in enumerate(lines, start=1):
        match = USES_RE.match(line)
        if not match:
            continue
        target = match.group(1)
        if is_external_action(target) and not SHA_PIN_RE.search(target):
            errors.append(
                f'{path}:{lineno}: action is not pinned to full commit SHA: {target}'
            )

    return errors


def main() -> int:
    workflow_dir = Path('.github/workflows')
    if not workflow_dir.exists():
        print('OK: no workflows found')
        return 0

    issues: list[str] = []
    for file in sorted(workflow_dir.glob('*.yml')):
        issues.extend(validate_workflow(file))
    for file in sorted(workflow_dir.glob('*.yaml')):
        issues.extend(validate_workflow(file))

    if issues:
        print('ERROR: workflow hardening checks failed:')
        for issue in issues:
            print(f'  - {issue}')
        return 1

    print('OK: workflow hardening checks passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
