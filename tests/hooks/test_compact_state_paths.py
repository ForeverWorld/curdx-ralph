#!/usr/bin/env python3
"""Behavior tests for compact state backup/restore paths."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _run_python(script_rel: str, payload: dict, *, env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / script_rel)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=cwd,
        env=env,
        check=False,
    )


class CompactStatePathTest(unittest.TestCase):
    def test_pre_compact_and_restore_use_spec_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            workspace = tmp_root / "repo"
            spec_dir = workspace / "specs" / "demo-spec"
            spec_dir.mkdir(parents=True)
            (workspace / "specs" / ".current-spec").write_text("demo-spec\n", encoding="utf-8")

            state_path = spec_dir / ".curdx-state.json"
            progress_path = spec_dir / ".progress.md"
            state_path.write_text('{"phase":"execution","taskIndex":1}', encoding="utf-8")
            progress_path.write_text("## Progress\n- sample\n", encoding="utf-8")

            env = os.environ.copy()
            env["HOME"] = str(tmp_root / "home")
            env["CURDX_HOOK_LOG"] = "0"
            payload = {"session_id": "compact-paths"}

            pre_result = _run_python("hooks/scripts/pre_compact.py", payload, env=env, cwd=workspace)
            self.assertEqual(pre_result.returncode, 0, msg=pre_result.stderr)

            backup_dir = Path(env["HOME"]) / ".curdx" / "pre-compact-tmp"
            metadata_path = backup_dir / "metadata.json"
            self.assertTrue((backup_dir / "curdx-state.json").exists())
            self.assertTrue((backup_dir / "progress.md").exists())
            self.assertTrue(metadata_path.exists())

            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata.get("state_rel"), "specs/demo-spec/.curdx-state.json")
            self.assertEqual(metadata.get("progress_rel"), "specs/demo-spec/.progress.md")

            state_path.unlink()
            progress_path.unlink()

            restore_result = _run_python("hooks/scripts/post_compact_restore.py", payload, env=env, cwd=workspace)
            self.assertEqual(restore_result.returncode, 0, msg=restore_result.stderr)

            self.assertTrue(state_path.exists())
            self.assertTrue(progress_path.exists())
            self.assertFalse((workspace / ".curdx-state.json").exists())
            self.assertFalse((workspace / ".progress.md").exists())


if __name__ == "__main__":
    unittest.main()
