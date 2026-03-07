#!/usr/bin/env python3
"""Behavior tests for PreToolUse hook outputs."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _run_python(
    script_rel: str, payload: dict, *, env: dict[str, str] | None = None, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / script_rel)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=cwd or ROOT,
        env=env,
        check=False,
    )


def _run_shell(script_rel: str, payload: dict, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(ROOT / script_rel)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=ROOT,
        env=env,
        check=False,
    )


class PreToolUseContractTest(unittest.TestCase):
    def test_util_pre_tool_use_deny_uses_hook_specific_output(self) -> None:
        sys.path.insert(0, str(ROOT / "hooks" / "scripts"))
        from _util import pre_tool_use_deny

        payload = json.loads(pre_tool_use_deny("blocked for policy"))
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("blocked for policy", payload["hookSpecificOutput"]["permissionDecisionReason"])

    def test_tool_redirect_websearch_blocks_with_reason(self) -> None:
        result = _run_python(
            "hooks/scripts/tool_redirect.py",
            {"tool_name": "WebSearch", "tool_input": {"query": "latest release"}},
        )
        self.assertEqual(result.returncode, 2, msg=result.stderr)
        self.assertTrue(result.stdout.strip())
        payload = json.loads(result.stdout)
        output = payload["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("WebSearch is blocked", output["permissionDecisionReason"])

    def test_tool_redirect_semantic_grep_adds_context(self) -> None:
        result = _run_python(
            "hooks/scripts/tool_redirect.py",
            {"tool_name": "Grep", "tool_input": {"pattern": "where is config loaded"}},
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(result.stdout.strip())
        payload = json.loads(result.stdout)
        output = payload["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertIn("Semantic pattern detected", output["additionalContext"])

    def test_tool_redirect_code_grep_passes_without_stdout(self) -> None:
        result = _run_python(
            "hooks/scripts/tool_redirect.py",
            {"tool_name": "Grep", "tool_input": {"pattern": "def save_user"}},
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_quick_mode_guard_denies_ask_user_question(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            spec_dir = workspace / "specs" / "demo-spec"
            spec_dir.mkdir(parents=True)
            (workspace / "specs" / ".current-spec").write_text("demo-spec\n", encoding="utf-8")
            (spec_dir / ".curdx-state.json").write_text(
                json.dumps({"quickMode": True}, ensure_ascii=True), encoding="utf-8"
            )

            home_dir = workspace / "home"
            home_dir.mkdir(parents=True)
            env = os.environ.copy()
            env["HOME"] = str(home_dir)
            env["CURDX_HOOK_LOG"] = "0"

            result = _run_shell(
                "hooks/scripts/quick-mode-guard.sh",
                {"cwd": str(workspace), "session_id": "s-quick"},
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(result.stdout.strip())
            payload = json.loads(result.stdout)
            output = payload["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("Quick mode active", output["permissionDecisionReason"])

    def test_quick_mode_guard_allows_when_quick_mode_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            spec_dir = workspace / "specs" / "demo-spec"
            spec_dir.mkdir(parents=True)
            (workspace / "specs" / ".current-spec").write_text("demo-spec\n", encoding="utf-8")
            (spec_dir / ".curdx-state.json").write_text(
                json.dumps({"quickMode": False}, ensure_ascii=True), encoding="utf-8"
            )

            env = os.environ.copy()
            env["CURDX_HOOK_LOG"] = "0"
            result = _run_shell(
                "hooks/scripts/quick-mode-guard.sh",
                {"cwd": str(workspace), "session_id": "s-normal"},
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_progress_path_guard_denies_root_progress_when_spec_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            spec_dir = workspace / "specs" / "demo-spec"
            spec_dir.mkdir(parents=True)
            (workspace / "specs" / ".current-spec").write_text("demo-spec\n", encoding="utf-8")
            root_progress = workspace / ".progress.md"

            env = os.environ.copy()
            env["CURDX_HOOK_LOG"] = "0"
            result = _run_python(
                "hooks/scripts/progress_path_guard.py",
                {
                    "cwd": str(workspace),
                    "session_id": "s-progress-root",
                    "tool_name": "Write",
                    "tool_input": {"file_path": str(root_progress), "content": "bad target"},
                },
                env=env,
                cwd=workspace,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(result.stdout.strip())

            payload = json.loads(result.stdout)
            output = payload["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("specs/demo-spec/.progress.md", output["permissionDecisionReason"])

    def test_progress_path_guard_allows_spec_progress_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            spec_dir = workspace / "specs" / "demo-spec"
            spec_dir.mkdir(parents=True)
            (workspace / "specs" / ".current-spec").write_text("demo-spec\n", encoding="utf-8")

            env = os.environ.copy()
            env["CURDX_HOOK_LOG"] = "0"
            result = _run_python(
                "hooks/scripts/progress_path_guard.py",
                {
                    "cwd": str(workspace),
                    "session_id": "s-progress-spec",
                    "tool_name": "Write",
                    "tool_input": {"file_path": str(spec_dir / ".progress.md"), "content": "ok target"},
                },
                env=env,
                cwd=workspace,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
