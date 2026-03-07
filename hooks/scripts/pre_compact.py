"""PreCompact hook - capture CURDX state before compaction.

Saves .curdx-state.json and .progress.md to a temporary location
for post-compaction restoration.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import HookTimer, read_hook_stdin


def _curdx_temp_dir() -> Path:
    """Get temp directory for pre-compact state."""
    tmp = Path.home() / ".curdx" / "pre-compact-tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    return tmp


def _resolve_current_spec_dir(cwd: Path) -> Path | None:
    """Resolve active spec directory via path-resolver.sh."""
    resolver = Path(__file__).parent / "path-resolver.sh"
    if not resolver.exists():
        return None

    # Resolve through the same shell helpers used by hooks/commands.
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
        # Only allow specs inside current workspace.
        spec_dir = spec_dir.resolve()
        spec_dir.relative_to(cwd.resolve())
    except (ValueError, OSError):
        return None

    return spec_dir if spec_dir.is_dir() else None


def run_pre_compact() -> int:
    """Save .curdx-state.json and .progress.md before compaction."""
    with HookTimer("pre_compact", "PreCompact") as t:
        hook_data = read_hook_stdin()
        session_id = str(hook_data.get("session_id", "")).strip()
        if session_id:
            t.set(session_id=session_id)
        cwd = Path.cwd()
        tmp = _curdx_temp_dir()

        # Clear stale backup artifacts from prior runs.
        for name in ("curdx-state.json", "progress.md", "metadata.json"):
            (tmp / name).unlink(missing_ok=True)

        saved = []
        metadata: dict[str, str] = {}

        spec_dir = _resolve_current_spec_dir(cwd)
        state_candidates = []
        progress_candidates = []
        if spec_dir:
            state_candidates.append(spec_dir / ".curdx-state.json")
            progress_candidates.append(spec_dir / ".progress.md")
        state_candidates.append(cwd / ".curdx-state.json")
        progress_candidates.append(cwd / ".progress.md")

        for candidate in state_candidates:
            if candidate.exists():
                shutil.copy2(candidate, tmp / "curdx-state.json")
                rel = str(candidate.resolve().relative_to(cwd.resolve()))
                metadata["state_rel"] = rel
                saved.append(rel)
                break

        for candidate in progress_candidates:
            if candidate.exists():
                shutil.copy2(candidate, tmp / "progress.md")
                rel = str(candidate.resolve().relative_to(cwd.resolve()))
                metadata["progress_rel"] = rel
                saved.append(rel)
                break

        if saved:
            (tmp / "metadata.json").write_text(
                json.dumps(metadata, ensure_ascii=True),
                encoding="utf-8",
            )
            print(f"CURDX: Pre-compact state saved ({', '.join(saved)})", file=sys.stderr)
            t.set(message=f"saved {len(saved)} files: {', '.join(saved)}", decision="backup")
        else:
            t.set(message="no state files to save", decision="skip")

        return 0


if __name__ == "__main__":
    sys.exit(run_pre_compact())
