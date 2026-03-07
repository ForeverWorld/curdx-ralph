#!/usr/bin/env python3
"""PreToolUse guard for .progress.md path correctness.

Blocks edits to workspace-root .progress.md when an active spec exists.
Writers should update the spec-scoped progress file instead.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import HookTimer, pre_tool_use_deny, read_hook_stdin


def _resolve_current_spec_dir(cwd: Path) -> Path | None:
    """Resolve active spec directory via path-resolver.sh."""
    resolver = Path(__file__).parent / "path-resolver.sh"
    if not resolver.exists():
        return None

    command = (
        f'source "{resolver}" >/dev/null 2>&1; '
        f'RALPH_CWD="{cwd}"; export RALPH_CWD; '
        "curdx_resolve_current"
    )
    result = subprocess.run(
        ["bash", "-lc", command],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None

    rel_path = result.stdout.strip().splitlines()[-1].strip() if result.stdout.strip() else ""
    if not rel_path:
        return None

    spec_dir = Path(rel_path)
    if not spec_dir.is_absolute():
        spec_dir = cwd / spec_dir

    try:
        spec_dir = spec_dir.resolve()
        spec_dir.relative_to(cwd.resolve())
    except (ValueError, OSError):
        return None

    return spec_dir if spec_dir.is_dir() else None


def _resolve_target_path(raw_path: str, cwd: Path) -> Path | None:
    """Resolve tool file path to an absolute path."""
    if not raw_path:
        return None
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = cwd / candidate
    try:
        return candidate.resolve()
    except OSError:
        return None


def main() -> int:
    """Entry point."""
    with HookTimer("progress_path_guard", "PreToolUse") as t:
        hook_data = read_hook_stdin()
        session_id = str(hook_data.get("session_id", "")).strip()
        if session_id:
            t.set(session_id=session_id)

        cwd_raw = str(hook_data.get("cwd", "")).strip()
        cwd = Path(cwd_raw).resolve() if cwd_raw else Path.cwd().resolve()
        tool_input = hook_data.get("tool_input", {})
        if not isinstance(tool_input, dict):
            t.set(message="no tool_input", decision="skip")
            return 0

        file_path = str(tool_input.get("file_path", "")).strip()
        target = _resolve_target_path(file_path, cwd)
        if target is None:
            t.set(message="no file_path", decision="skip")
            return 0

        root_progress = (cwd / ".progress.md").resolve()
        if target != root_progress:
            t.set(message="not root progress path", decision="skip")
            return 0

        spec_dir = _resolve_current_spec_dir(cwd)
        if spec_dir is None:
            t.set(message="no active spec, allow root progress", decision="allow")
            return 0

        spec_progress = spec_dir / ".progress.md"
        try:
            spec_progress_rel = spec_progress.resolve().relative_to(cwd)
            recommended = str(spec_progress_rel)
        except (ValueError, OSError):
            recommended = str(spec_progress)

        reason = (
            "Root .progress.md is reserved. "
            f"An active spec is selected, write progress to `{recommended}` instead."
        )
        print(pre_tool_use_deny(reason))
        t.set(message="blocked root progress write", decision="deny", file=file_path)
        return 0


if __name__ == "__main__":
    sys.exit(main())
