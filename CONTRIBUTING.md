# Contributing

Thanks for contributing to CURDX.

## Before You Start

- search existing issues/PRs first
- keep changes focused and small
- include verification steps in your PR

## Development Workflow

1. Fork and create a branch from `main`
2. Make focused changes
3. Run local checks
4. Open a PR with context and validation output

## Local Validation

Run these commands before opening a PR:

```bash
bash -n hooks/scripts/*.sh scripts/*.sh
python3 -m py_compile hooks/scripts/*.py hooks/scripts/_checkers/*.py scripts/ci/*.py
python3 scripts/ci/check_plugin_manifest.py
python3 scripts/ci/check_claude_plugin_contract.py
python3 scripts/ci/check_skills_frontmatter.py
python3 scripts/ci/check_local_links.py
python3 scripts/ci/check_forbidden_files.py
python3 scripts/ci/check_workflow_hardening.py
python3 -m unittest discover -s tests/hooks -p 'test_*.py'
```

## Pull Request Checklist

- what changed
- why the change is needed
- risk and rollback note
- exact commands you ran

## Commit Style

Conventional commits are recommended:

- `feat:`
- `fix:`
- `docs:`
- `refactor:`
- `test:`
- `chore:`
