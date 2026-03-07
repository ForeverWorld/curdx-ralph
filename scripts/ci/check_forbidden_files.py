#!/usr/bin/env python3
"""Fail if local-only state files or junk files are committed to the repo."""

from __future__ import annotations

from pathlib import Path

FORBIDDEN_PATHS = (
    Path('specs/.current-spec'),
    Path('specs/.current-epic'),
)
FORBIDDEN_GLOBS = (
    '**/.DS_Store',
)


def main() -> int:
    found: list[str] = []

    for forbidden in FORBIDDEN_PATHS:
        if forbidden.exists():
            found.append(str(forbidden))
    for pattern in FORBIDDEN_GLOBS:
        for matched in Path('.').glob(pattern):
            found.append(str(matched))

    if found:
        print('ERROR: forbidden local-state files found in repository:')
        for path in found:
            print(f'  - {path}')
        print('Remove these files from git history/state tracking before merging.')
        return 1

    print('OK: forbidden local-state files not present')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
