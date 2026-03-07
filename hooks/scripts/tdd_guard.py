#!/usr/bin/env python3
"""TDD Guard — lightweight test-first enforcement hook.

Handles 3 hook events:
  SessionStart       → initialize guard state, clear transient data
  PreToolUse         → check TDD compliance for file edits
  UserPromptSubmit   → handle "tdd on/off" commands

Design inspired by tdd-guard (https://github.com/nicobailon/tdd-guard)
but adapted to curdx's Python hook architecture with rule-based checks
instead of AI-model validation for speed and zero-cost operation.

Key principles:
  - ONE test at a time (Red phase)
  - Minimal implementation (Green phase)
  - Refactor only after green (Yellow phase)
  - Non-code files are always ignored
  - Guard can be toggled via "tdd on" / "tdd off" in user prompt
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import HookTimer, hook_log, pre_tool_use_context, pre_tool_use_deny

# ── Configuration ────────────────────────────────────────────────────

_GUARD_DIR = Path.home() / ".curdx" / "tdd-guard"
_CONFIG_FILE = _GUARD_DIR / "config.json"

# File extensions that are never subject to TDD checks
IGNORE_EXTENSIONS = frozenset({
    ".md", ".txt", ".log", ".json", ".yml", ".yaml",
    ".xml", ".html", ".css", ".scss", ".less",
    ".rst", ".toml", ".ini", ".cfg", ".conf",
    ".svg", ".png", ".jpg", ".jpeg", ".gif", ".ico",
    ".lock", ".sum", ".mod",
})

# Path fragments that indicate non-code / config files
IGNORE_PATH_FRAGMENTS = frozenset({
    ".github/", ".vscode/", ".idea/", "__pycache__/",
    "node_modules/", ".git/", "dist/", "build/",
    ".claude/", ".curdx/",
})

# Extensions recognized as test files
TEST_INDICATORS = (
    ".test.", ".spec.", "_test.", "_spec.",
    "/test/", "/tests/", "/__tests__/",
    "/test_", "/spec_",
    "test/", "tests/",  # also match at path start (no leading /)
)


# ── Guard state management ───────────────────────────────────────────

def _load_config() -> dict:
    """Load guard config from persistent storage."""
    if _CONFIG_FILE.exists():
        try:
            return json.loads(_CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_config(config: dict) -> None:
    """Save guard config to persistent storage."""
    try:
        _GUARD_DIR.mkdir(parents=True, exist_ok=True)
        _CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n")
    except OSError:
        pass


def _is_guard_enabled() -> bool:
    """Check if TDD guard is enabled. Defaults to False (opt-in)."""
    config = _load_config()
    return config.get("guardEnabled", False)


def _set_guard_enabled(enabled: bool) -> None:
    """Toggle guard state persistently."""
    config = _load_config()
    config["guardEnabled"] = enabled
    _save_config(config)


def _get_ignore_patterns() -> list[str]:
    """Get user-configured extra ignore patterns (minimatch-style)."""
    config = _load_config()
    return config.get("ignorePatterns", [])


# ── File classification ──────────────────────────────────────────────

def _should_ignore_file(file_path: str) -> bool:
    """Check if a file should be ignored by TDD guard.

    Ignores non-code files (docs, config, assets) and paths inside
    tool/build directories.
    """
    if not file_path:
        return True

    path = Path(file_path)

    # Extension-based ignore
    if path.suffix.lower() in IGNORE_EXTENSIONS:
        return True

    # Path fragment ignore
    normalized = file_path.replace("\\", "/")
    for fragment in IGNORE_PATH_FRAGMENTS:
        if fragment in normalized:
            return True

    # User-configured patterns (simple glob matching)
    import fnmatch
    extra_patterns = _get_ignore_patterns()
    for pattern in extra_patterns:
        if fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(normalized, pattern):
            return True

    return False


def _is_test_file(file_path: str) -> bool:
    """Check if file is a test file based on naming conventions."""
    normalized = file_path.replace("\\", "/").lower()
    return any(indicator in normalized for indicator in TEST_INDICATORS)


def _is_implementation_file(file_path: str) -> bool:
    """Check if file is an implementation (non-test, non-config) source file."""
    if _should_ignore_file(file_path):
        return False
    return not _is_test_file(file_path)


# ── Hook event handlers ─────────────────────────────────────────────

def _handle_session_start(hook_data: dict) -> int:
    """SessionStart: initialize guard directory, clear transient data."""
    _GUARD_DIR.mkdir(parents=True, exist_ok=True)
    session_id = str(hook_data.get("session_id", "")).strip()

    # Clear transient data files (test results, modifications, etc.)
    transient_files = ["test.json", "modifications.json", "lint.json"]
    for fname in transient_files:
        fpath = _GUARD_DIR / fname
        if fpath.exists():
            try:
                fpath.unlink()
            except OSError:
                pass

    hook_log("tdd_guard", "SessionStart", "initialized guard directory", session_id=session_id)

    # Show guard status on session start
    enabled = _is_guard_enabled()
    if enabled:
        sys.stderr.write(
            "\033[0;32m[TDD Guard] Active — test-first enforcement ON. "
            'Say "tdd off" to disable.\033[0m\n'
        )
    return 0


def _handle_user_prompt(hook_data: dict) -> int:
    """UserPromptSubmit: handle 'tdd on' / 'tdd off' commands."""
    user_input = (
        str(hook_data.get("user_prompt", "")).strip()
        or str(hook_data.get("user_input", "")).strip()
    ).lower()

    if user_input in ("tdd on", "tdd-guard on", "tdd guard on"):
        _set_guard_enabled(True)
        sys.stderr.write(
            "\033[0;32m[TDD Guard] Enabled — test-first enforcement is now ON.\033[0m\n"
        )
        # Block the prompt so Claude doesn't try to interpret the command
        print(json.dumps({
            "decision": "block",
            "reason": "TDD Guard enabled. Write tests first, then implement.",
        }))
        return 0

    if user_input in ("tdd off", "tdd-guard off", "tdd guard off"):
        _set_guard_enabled(False)
        sys.stderr.write(
            "\033[0;33m[TDD Guard] Disabled — test-first enforcement is now OFF.\033[0m\n"
        )
        print(json.dumps({
            "decision": "block",
            "reason": "TDD Guard disabled.",
        }))
        return 0

    return 0


def _handle_pre_tool_use(hook_data: dict) -> int:
    """PreToolUse: enforce TDD compliance for file edits.

    Rules (inspired by tdd-guard):
    1. Editing a test file → always allowed (Red phase)
    2. Editing an implementation file → provide TDD context reminder
    3. Creating a new implementation file → remind to write test first
    """
    if not _is_guard_enabled():
        return 0

    tool_name = hook_data.get("tool_name", "")
    tool_input = hook_data.get("tool_input", {})
    session_id = str(hook_data.get("session_id", "")).strip()
    if not isinstance(tool_input, dict):
        return 0

    file_path = tool_input.get("file_path", "")
    if not file_path:
        return 0

    # Ignored files pass through silently
    if _should_ignore_file(file_path):
        return 0

    # Test files are always allowed (Red phase — writing tests first is good)
    if _is_test_file(file_path):
        hook_log(
            "tdd_guard", "PreToolUse",
            f"test file edit allowed: {Path(file_path).name}",
            tool=tool_name, file=file_path, decision="allow",
            session_id=session_id,
        )
        return 0

    # Implementation file edits get a TDD context reminder
    if _is_implementation_file(file_path):
        fname = Path(file_path).name

        # For Write (new file creation), give a stronger reminder
        if tool_name == "Write":
            context_msg = (
                f"[TDD Guard] Creating new file: {fname}\n"
                "Reminder: In TDD, write a failing test FIRST, then create "
                "the minimal implementation to make it pass.\n"
                "If this is a stub/interface/type definition, proceed."
            )
        else:
            context_msg = (
                f"[TDD Guard] Editing implementation: {fname}\n"
                "TDD discipline: ensure you have a failing test for this change. "
                "Implement only the minimum to make the current test pass."
            )

        print(pre_tool_use_context(context_msg))
        hook_log(
            "tdd_guard", "PreToolUse",
            f"TDD reminder for implementation edit: {fname}",
            tool=tool_name, file=file_path, decision="context",
            session_id=session_id,
        )
        return 0

    return 0


# ── Main dispatcher ──────────────────────────────────────────────────

def main() -> int:
    """Route to the appropriate handler based on hook event."""
    hook_name = os.environ.get("HOOK_EVENT_NAME", "")

    # Read stdin (may be empty for some events)
    try:
        raw = sys.stdin.read()
        hook_data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        hook_data = {}

    # Infer event from hook_data if env var not set
    if not hook_name:
        hook_name = hook_data.get("hook_event_name", "")

    # Also check for event field patterns
    if not hook_name:
        if (
            "session_id" in hook_data
            and "tool_name" not in hook_data
            and "user_input" not in hook_data
            and "user_prompt" not in hook_data
        ):
            hook_name = "SessionStart"
        elif "user_input" in hook_data or "user_prompt" in hook_data:
            hook_name = "UserPromptSubmit"
        elif "tool_name" in hook_data:
            hook_name = "PreToolUse"

    with HookTimer("tdd_guard", hook_name or "unknown") as t:
        session_id = str(hook_data.get("session_id", "")).strip()
        if session_id:
            t.set(session_id=session_id)
        if hook_name == "SessionStart":
            t.set(message="session start handler")
            return _handle_session_start(hook_data)
        elif hook_name == "UserPromptSubmit":
            t.set(message="user prompt handler")
            return _handle_user_prompt(hook_data)
        elif hook_name in ("PreToolUse", "PostToolUse"):
            t.set(message="pre-tool-use handler")
            return _handle_pre_tool_use(hook_data)
        else:
            t.set(message=f"unhandled event: {hook_name}", decision="skip")
            return 0


if __name__ == "__main__":
    sys.exit(main())
