"""Post-compact restore hook - restore CURDX state after compaction.

Restores .curdx-state.json and .progress.md from temporary location.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import HookTimer, read_hook_stdin


def _curdx_temp_dir() -> Path:
    """Get temp directory for pre-compact state."""
    return Path.home() / ".curdx" / "pre-compact-tmp"


def _resolve_restore_target(cwd: Path, rel_path: str, fallback_name: str) -> Path:
    """Resolve a safe restore target path inside current workspace."""
    if not rel_path:
        return cwd / fallback_name

    candidate = Path(rel_path)
    if candidate.is_absolute():
        return cwd / fallback_name

    target = (cwd / candidate).resolve()
    try:
        target.relative_to(cwd.resolve())
    except ValueError:
        return cwd / fallback_name

    return target


def run_post_compact_restore() -> int:
    """Restore .curdx-state.json and .progress.md after compaction."""
    with HookTimer("post_compact_restore", "PreCompact") as t:
        hook_data = read_hook_stdin()
        session_id = str(hook_data.get("session_id", "")).strip()
        if session_id:
            t.set(session_id=session_id)
        cwd = Path.cwd()
        tmp = _curdx_temp_dir()

        restored = []
        metadata_file = tmp / "metadata.json"
        metadata: dict[str, str] = {}
        if metadata_file.exists():
            try:
                metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                metadata = {}

        # Restore .curdx-state.json
        saved_state = tmp / "curdx-state.json"
        if saved_state.exists():
            target_state = _resolve_restore_target(cwd, metadata.get("state_rel", ""), ".curdx-state.json")
            target_state.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(saved_state, target_state)
            saved_state.unlink()
            restored.append(str(target_state.relative_to(cwd)))

        # Restore .progress.md
        saved_progress = tmp / "progress.md"
        if saved_progress.exists():
            target_progress = _resolve_restore_target(cwd, metadata.get("progress_rel", ""), ".progress.md")
            target_progress.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(saved_progress, target_progress)
            saved_progress.unlink()
            restored.append(str(target_progress.relative_to(cwd)))

        metadata_file.unlink(missing_ok=True)

        if restored:
            print(f"[CURDX Context Restored After Compaction]\nRestored: {', '.join(restored)}")
            t.set(message=f"restored {len(restored)} files: {', '.join(restored)}", decision="restore")
        else:
            t.set(message="no state files to restore", decision="skip")

        return 0


if __name__ == "__main__":
    sys.exit(run_post_compact_restore())
