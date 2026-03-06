"""Shared utilities for hook scripts.

This module provides common constants, color codes, session path helpers,
and utility functions used across all hook scripts.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

RED = "\033[0;31m"
YELLOW = "\033[0;33m"
GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
BLUE = "\033[0;34m"
MAGENTA = "\033[0;35m"
NC = "\033[0m"

FILE_LENGTH_WARN = 400
FILE_LENGTH_CRITICAL = 600

_AUTOCOMPACT_BUFFER_TOKENS = 33_000

# ── Logging infrastructure ──────────────────────────────────────────

_LOG_DIR = Path.home() / ".curdx" / "logs"
_LOG_FILE = _LOG_DIR / "hooks.log"
_LOG_ENABLED: bool | None = None  # lazy cache
_LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB auto-rotate


def _is_log_enabled() -> bool:
    """Check if hook logging is enabled. Cached after first call."""
    global _LOG_ENABLED
    if _LOG_ENABLED is None:
        _LOG_ENABLED = os.environ.get("CURDX_HOOK_LOG", "1") != "0"
    return _LOG_ENABLED


def _rotate_if_needed() -> None:
    """Rotate log file if it exceeds size limit."""
    try:
        if _LOG_FILE.exists() and _LOG_FILE.stat().st_size > _LOG_MAX_BYTES:
            rotated = _LOG_FILE.with_suffix(".log.1")
            if rotated.exists():
                rotated.unlink()
            _LOG_FILE.rename(rotated)
    except OSError:
        pass


def hook_log(
    hook_name: str,
    event: str,
    message: str,
    *,
    level: str = "INFO",
    tool: str = "",
    file: str = "",
    decision: str = "",
    duration_ms: float | None = None,
    extra: dict | None = None,
) -> None:
    """Write a structured log entry to ~/.curdx/logs/hooks.log.

    Args:
        hook_name: Script name (e.g. "security_reminder", "stop-watcher")
        event: Hook event type (e.g. "PreToolUse", "Stop", "SessionStart")
        message: Human-readable description of what happened
        level: Log level — DEBUG, INFO, WARN, ERROR
        tool: Tool name if applicable (e.g. "Write", "Bash")
        file: File path if applicable
        decision: Decision taken (e.g. "allow", "deny", "block", "context")
        duration_ms: Execution time in milliseconds
        extra: Additional key-value pairs to include
    """
    if not _is_log_enabled():
        return
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        _rotate_if_needed()

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        parts = [f"[{ts}]", f"[{level}]", f"[{hook_name}]", f"[{event}]"]
        if tool:
            parts.append(f"tool={tool}")
        if file:
            parts.append(f"file={file}")
        if decision:
            parts.append(f"decision={decision}")
        if duration_ms is not None:
            parts.append(f"dur={duration_ms:.1f}ms")
        parts.append(f"| {message}")
        if extra:
            kv = " ".join(f"{k}={v}" for k, v in extra.items())
            parts.append(f"({kv})")

        line = " ".join(parts) + "\n"
        with _LOG_FILE.open("a") as f:
            f.write(line)
    except OSError:
        pass  # Never let logging break hooks


class HookTimer:
    """Context manager to measure hook execution time.

    Usage:
        with HookTimer("security_reminder", "PreToolUse") as t:
            ... do work ...
            t.set(tool="Write", decision="allow", message="no patterns matched")
    """

    def __init__(self, hook_name: str, event: str) -> None:
        self.hook_name = hook_name
        self.event = event
        self._start = 0.0
        self._tool = ""
        self._file = ""
        self._decision = ""
        self._message = "completed"
        self._level = "INFO"
        self._extra: dict | None = None

    def set(
        self,
        *,
        message: str = "",
        tool: str = "",
        file: str = "",
        decision: str = "",
        level: str = "",
        extra: dict | None = None,
    ) -> None:
        if message:
            self._message = message
        if tool:
            self._tool = tool
        if file:
            self._file = file
        if decision:
            self._decision = decision
        if level:
            self._level = level
        if extra:
            self._extra = extra

    def __enter__(self) -> "HookTimer":
        self._start = time.monotonic()
        hook_log(self.hook_name, self.event, "started", level="DEBUG")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        elapsed = (time.monotonic() - self._start) * 1000
        if exc_type and exc_type is not SystemExit:
            hook_log(
                self.hook_name,
                self.event,
                f"exception: {exc_type.__name__}: {exc_val}",
                level="ERROR",
                tool=self._tool,
                file=self._file,
                duration_ms=elapsed,
            )
        else:
            hook_log(
                self.hook_name,
                self.event,
                self._message,
                level=self._level,
                tool=self._tool,
                file=self._file,
                decision=self._decision,
                duration_ms=elapsed,
                extra=self._extra,
            )
        return None  # don't suppress exceptions


def _get_max_context_tokens() -> int:
    """Return context window size. Default 200K for standard Claude."""
    return 200_000


def _get_compaction_threshold_pct() -> float:
    """Return compaction threshold as percentage of total context window.

    Formula: (window_size - buffer) / window_size * 100
    - 200K context: 83.5%
    """
    window = _get_max_context_tokens()
    return (window - _AUTOCOMPACT_BUFFER_TOKENS) / window * 100


def _curdx_base() -> Path:
    """Get base curdx cache directory."""
    base = Path.home() / ".curdx"
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_session_cache_path() -> Path:
    """Get session-scoped context cache path."""
    session_id = os.environ.get("CURDX_SESSION_ID", "").strip() or "default"
    cache_dir = _curdx_base() / "sessions" / session_id
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "context-cache.json"


def find_git_root() -> Path | None:
    """Find git repository root."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:
        pass
    return None


def read_hook_stdin() -> dict:
    """Read and parse JSON from stdin.

    Returns empty dict on error or invalid JSON.
    """
    try:
        content = sys.stdin.read()
        if not content:
            return {}
        return json.loads(content)
    except (json.JSONDecodeError, OSError):
        return {}


def get_edited_file_from_stdin() -> Path | None:
    """Get the edited file path from PostToolUse hook stdin."""
    try:
        import select

        if select.select([sys.stdin], [], [], 0)[0]:
            data = json.load(sys.stdin)
            tool_input = data.get("tool_input", {})
            file_path = tool_input.get("file_path")
            if file_path:
                return Path(file_path)
    except Exception:
        pass
    return None


def is_waiting_for_user_input(transcript_path: str) -> bool:
    """Check if Claude's last action was asking the user a question."""
    try:
        transcript = Path(transcript_path)
        if not transcript.exists():
            return False

        last_assistant_msg = None
        with transcript.open() as f:
            for line in f:
                try:
                    msg = json.loads(line)
                    if msg.get("type") == "assistant":
                        last_assistant_msg = msg
                except json.JSONDecodeError:
                    continue

        if not last_assistant_msg:
            return False

        message = last_assistant_msg.get("message", {})
        if not isinstance(message, dict):
            return False

        content = message.get("content", [])
        if not isinstance(content, list):
            return False

        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                if block.get("name") == "AskUserQuestion":
                    return True

        return False
    except OSError:
        return False


def check_file_length(file_path: Path) -> str:
    """Check if file exceeds length thresholds.

    Returns a plain-text warning message or empty string if OK.
    """
    try:
        line_count = len(file_path.read_text().splitlines())
    except Exception:
        return ""

    if line_count > FILE_LENGTH_CRITICAL:
        return (
            f"FILE TOO LONG: {file_path.name} has {line_count} lines (limit: {FILE_LENGTH_CRITICAL}). "
            f"Split into smaller, focused modules (<{FILE_LENGTH_WARN} lines each)."
        )
    elif line_count > FILE_LENGTH_WARN:
        return (
            f"FILE GROWING LONG: {file_path.name} has {line_count} lines (warn: {FILE_LENGTH_WARN}). "
            f"Consider splitting before it grows further."
        )
    return ""


def post_tool_use_block(reason: str) -> str:
    """Build PostToolUse block JSON (drops tool result, shows reason to Claude)."""
    return json.dumps({"decision": "block", "reason": reason})


def post_tool_use_context(context: str) -> str:
    """Build PostToolUse additionalContext JSON (adds context without blocking)."""
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": context,
            }
        }
    )


def pre_tool_use_deny(reason: str) -> str:
    """Build PreToolUse deny JSON (blocks tool call)."""
    return json.dumps({"permissionDecision": "deny", "reason": reason})


def pre_tool_use_context(context: str) -> str:
    """Build PreToolUse additionalContext JSON (hint without blocking)."""
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": context,
            }
        }
    )


def stop_block(reason: str) -> str:
    """Build Stop block JSON (prevents session stop)."""
    return json.dumps({"decision": "block", "reason": reason})
