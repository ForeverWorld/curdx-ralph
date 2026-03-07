#!/usr/bin/env python3
"""Validate minimal SKILL.md frontmatter quality across skills/."""

from __future__ import annotations

import re
from pathlib import Path

SKILLS_DIR = Path('skills')
REQUIRED = ('name', 'description')
WARN_FIELDS = ('license', 'compatibility', 'metadata')


def extract_frontmatter(text: str) -> str | None:
    if not text.startswith('---\n'):
        return None
    end = text.find('\n---\n', 4)
    if end == -1:
        return None
    return text[4:end]


def has_key(frontmatter: str, key: str) -> bool:
    return re.search(rf'(?m)^{re.escape(key)}\s*:', frontmatter) is not None


def main() -> int:
    if not SKILLS_DIR.exists():
        print('ERROR: skills/ directory not found')
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    for skill_file in sorted(SKILLS_DIR.glob('*/SKILL.md')):
        text = skill_file.read_text(encoding='utf-8', errors='replace')
        fm = extract_frontmatter(text)
        if fm is None:
            errors.append(f'{skill_file}: missing or malformed YAML frontmatter')
            continue

        for key in REQUIRED:
            if not has_key(fm, key):
                errors.append(f'{skill_file}: missing required frontmatter key `{key}`')

        for key in WARN_FIELDS:
            if not has_key(fm, key):
                warnings.append(f'{skill_file}: missing recommended key `{key}`')

        name_match = re.search(r'(?m)^name:\s*["\']?([^"\'\n]+)', fm)
        if name_match:
            declared = name_match.group(1).strip()
            folder = skill_file.parent.name
            if declared != folder:
                warnings.append(
                    f'{skill_file}: name `{declared}` differs from folder `{folder}`'
                )

    for msg in warnings:
        print(f'WARN: {msg}')
    for msg in errors:
        print(f'ERROR: {msg}')

    if errors:
        return 1

    print(f'OK: validated {len(list(SKILLS_DIR.glob("*/SKILL.md")))} skills')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
