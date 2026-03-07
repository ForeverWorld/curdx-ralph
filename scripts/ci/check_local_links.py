#!/usr/bin/env python3
"""Check local markdown links (excluding vendored skills docs by default)."""

from __future__ import annotations

import re
from pathlib import Path

LINK_RE = re.compile(r'\[[^\]]+\]\(([^)]+)\)')
SKIP_TARGET_PREFIXES = ('http://', 'https://', 'mailto:', '#')
SKIP_TARGET_CHARS = ('{', '}', '*', '?', '<', '>', '|', '`')


def should_skip_target(target: str) -> bool:
    if not target:
        return True
    if target.startswith(SKIP_TARGET_PREFIXES):
        return True
    if any(ch in target for ch in SKIP_TARGET_CHARS):
        return True
    if target.startswith('?!'):
        return True
    return False


def resolve_target(md_file: Path, target: str) -> Path:
    clean = target.split('#', 1)[0].strip()
    if clean.startswith('/'):
        return (Path('.') / clean.lstrip('/')).resolve()
    return (md_file.parent / clean).resolve()


def format_repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path)


def main() -> int:
    unresolved: list[str] = []
    repo_root = Path('.').resolve()

    for md_file in sorted(Path('.').rglob('*.md')):
        md_file_abs = md_file.resolve()
        rel = md_file_abs.relative_to(repo_root)
        if 'skills' in rel.parts:
            # Imported third-party docs often contain site-root links.
            continue

        content = md_file_abs.read_text(encoding='utf-8', errors='replace')
        for match in LINK_RE.finditer(content):
            raw_target = match.group(1).strip()
            if should_skip_target(raw_target):
                continue

            resolved = resolve_target(md_file_abs, raw_target)
            if not resolved.exists():
                unresolved.append(
                    f'{rel}: `{raw_target}` -> {format_repo_relative(resolved, repo_root)}'
                )

    if unresolved:
        print('ERROR: unresolved local markdown links found:')
        for item in unresolved:
            print(f'  - {item}')
        return 1

    print('OK: local markdown links look good (excluding skills/)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
