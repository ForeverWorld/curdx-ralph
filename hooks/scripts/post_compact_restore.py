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


def run_post_compact_restore() -> int:
    """Restore .curdx-state.json and .progress.md after compaction."""
    with HookTimer("post_compact_restore", "PreCompact") as t:
        hook_data = read_hook_stdin()
        cwd = Path.cwd()
        tmp = _curdx_temp_dir()

        restored = []

        # Restore .curdx-state.json
        saved_state = tmp / "curdx-state.json"
        if saved_state.exists():
            shutil.copy2(saved_state, cwd / ".curdx-state.json")
            saved_state.unlink()
            restored.append(".curdx-state.json")

        # Restore .progress.md
        saved_progress = tmp / "progress.md"
        if saved_progress.exists():
            shutil.copy2(saved_progress, cwd / ".progress.md")
            saved_progress.unlink()
            restored.append(".progress.md")

        if restored:
            print(f"[CURDX Context Restored After Compaction]\nRestored: {', '.join(restored)}")
            t.set(message=f"restored {len(restored)} files: {', '.join(restored)}", decision="restore")
        else:
            t.set(message="no state files to restore", decision="skip")

        return 0


if __name__ == "__main__":
    sys.exit(run_post_compact_restore())
