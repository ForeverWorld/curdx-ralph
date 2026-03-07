#!/usr/bin/env python3
"""Behavior tests for stop-watcher hook script."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _run_stop_watcher(
    payload: dict, env: dict[str, str], *, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(ROOT / "hooks/scripts/stop-watcher.sh")],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=cwd or ROOT,
        env=env,
        check=False,
    )


def _prepare_workspace(tmp_root: Path) -> tuple[Path, Path]:
    workspace = tmp_root / "repo"
    spec_dir = workspace / "specs" / "demo-spec"
    spec_dir.mkdir(parents=True)
    (workspace / "specs" / ".current-spec").write_text("demo-spec\n", encoding="utf-8")
    return workspace, spec_dir


class StopWatcherBehaviorTest(unittest.TestCase):
    def test_blocks_stop_in_quick_mode_non_execution_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            workspace, spec_dir = _prepare_workspace(tmp_root)
            state_file = spec_dir / ".curdx-state.json"
            state_file.write_text(
                json.dumps(
                    {
                        "phase": "design",
                        "quickMode": True,
                        "taskIndex": 0,
                        "totalTasks": 3,
                    },
                    ensure_ascii=True,
                ),
                encoding="utf-8",
            )
            old = time.time() - 5
            os.utime(state_file, (old, old))

            env = os.environ.copy()
            env["HOME"] = str(tmp_root / "home")
            env["CURDX_HOOK_LOG"] = "0"
            result = _run_stop_watcher(
                {"cwd": str(workspace), "session_id": "stop-quick", "stop_hook_active": False},
                env,
                cwd=workspace,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(result.stdout.strip())
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("Quick mode active", payload["reason"])

    def test_allows_stop_when_stop_hook_active_flag_is_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            workspace, spec_dir = _prepare_workspace(tmp_root)
            state_file = spec_dir / ".curdx-state.json"
            state_file.write_text(
                json.dumps(
                    {
                        "phase": "design",
                        "quickMode": True,
                        "taskIndex": 0,
                        "totalTasks": 3,
                    },
                    ensure_ascii=True,
                ),
                encoding="utf-8",
            )
            old = time.time() - 5
            os.utime(state_file, (old, old))

            env = os.environ.copy()
            env["HOME"] = str(tmp_root / "home")
            env["CURDX_HOOK_LOG"] = "0"
            result = _run_stop_watcher(
                {"cwd": str(workspace), "session_id": "stop-loop", "stop_hook_active": True},
                env,
                cwd=workspace,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_does_not_false_positive_on_instructional_phrase_in_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            workspace, spec_dir = _prepare_workspace(tmp_root)
            state_file = spec_dir / ".curdx-state.json"
            state_file.write_text(
                json.dumps(
                    {
                        "phase": "execution",
                        "quickMode": False,
                        "taskIndex": 1,
                        "totalTasks": 3,
                        "taskIteration": 1,
                        "globalIteration": 2,
                        "maxGlobalIterations": 100,
                    },
                    ensure_ascii=True,
                ),
                encoding="utf-8",
            )
            (spec_dir / "tasks.md").write_text(
                "- [x] 1.1 done\n- [ ] 1.2 in progress\n- [ ] 1.3 pending\n",
                encoding="utf-8",
            )
            transcript = workspace / "session.log"
            transcript.write_text(
                "Instructions: Only output ALL_TASKS_COMPLETE when done.\n",
                encoding="utf-8",
            )
            old = time.time() - 5
            os.utime(state_file, (old, old))

            env = os.environ.copy()
            env["HOME"] = str(tmp_root / "home")
            env["CURDX_HOOK_LOG"] = "0"
            result = _run_stop_watcher(
                {
                    "cwd": str(workspace),
                    "session_id": "stop-transcript-phrase",
                    "transcript_path": str(transcript),
                    "stop_hook_active": False,
                },
                env,
                cwd=workspace,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(result.stdout.strip())
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")

    def test_allows_stop_when_last_assistant_message_has_exact_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            workspace, spec_dir = _prepare_workspace(tmp_root)
            state_file = spec_dir / ".curdx-state.json"
            state_file.write_text(
                json.dumps(
                    {
                        "phase": "execution",
                        "quickMode": False,
                        "taskIndex": 1,
                        "totalTasks": 3,
                        "taskIteration": 1,
                        "globalIteration": 2,
                        "maxGlobalIterations": 100,
                    },
                    ensure_ascii=True,
                ),
                encoding="utf-8",
            )
            old = time.time() - 5
            os.utime(state_file, (old, old))

            env = os.environ.copy()
            env["HOME"] = str(tmp_root / "home")
            env["CURDX_HOOK_LOG"] = "0"
            result = _run_stop_watcher(
                {
                    "cwd": str(workspace),
                    "session_id": "stop-last-assistant",
                    "last_assistant_message": "ALL_TASKS_COMPLETE\nPR: https://example.com/pr/1",
                    "stop_hook_active": False,
                },
                env,
                cwd=workspace,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
