"""PreCompact hook - capture CURDX state before compaction.

Saves .curdx-state.json and .progress.md to a temporary location
for post-compaction restoration.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import HookTimer, read_hook_stdin


def _curdx_temp_dir() -> Path:
    """Get temp directory for pre-compact state."""
    tmp = Path.home() / ".curdx" / "pre-compact-tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    return tmp


def run_pre_compact() -> int:
    """Save .curdx-state.json and .progress.md before compaction."""
    with HookTimer("pre_compact", "PreCompact") as t:
        hook_data = read_hook_stdin()
        cwd = Path.cwd()
        tmp = _curdx_temp_dir()

        saved = []

        # Save .curdx-state.json
        state_file = cwd / ".curdx-state.json"
        if state_file.exists():
            shutil.copy2(state_file, tmp / "curdx-state.json")
            saved.append(".curdx-state.json")

        # Save .progress.md (look in specs dirs too)
        for candidate in [cwd / ".progress.md"]:
            if candidate.exists():
                shutil.copy2(candidate, tmp / "progress.md")
                saved.append(str(candidate.name))
                break

        if saved:
            print(f"CURDX: Pre-compact state saved ({', '.join(saved)})", file=sys.stderr)
            t.set(message=f"saved {len(saved)} files: {', '.join(saved)}", decision="backup")
        else:
            t.set(message="no state files to save", decision="skip")

        return 0


if __name__ == "__main__":
    sys.exit(run_pre_compact())
