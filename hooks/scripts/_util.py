"""Shared utilities for hook scripts.

This module provides common constants, color codes, session path helpers,
and utility functions used across all hook scripts.
"""

from __future__ import annotations

import json
import os
import re
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
_LOG_JSONL_FILE = _LOG_DIR / "hooks.jsonl"
_LOG_ENABLED: bool | None = None  # lazy cache
_LOG_LEVEL_VALUE: int | None = None  # lazy cache
_LOG_SPLIT_ENABLED: bool | None = None  # lazy cache
_LOG_JSONL_ENABLED: bool | None = None  # lazy cache
_LOG_SESSION_SPLIT_ENABLED: bool | None = None  # lazy cache
_LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB auto-rotate
_LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARN": 30,
    "WARNING": 30,
    "ERROR": 40,
}


def _is_log_enabled() -> bool:
    """Check if hook logging is enabled. Cached after first call."""
    global _LOG_ENABLED
    if _LOG_ENABLED is None:
        _LOG_ENABLED = os.environ.get("CURDX_HOOK_LOG", "1") != "0"
    return _LOG_ENABLED


def _parse_bool_env(name: str, default: bool) -> bool:
    """Parse common boolean env representations."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _normalize_level(level: str) -> str:
    """Normalize log level values and aliases."""
    normalized = (level or "INFO").strip().upper()
    if normalized == "WARNING":
        return "WARN"
    if normalized not in _LOG_LEVELS:
        return "INFO"
    return normalized


def _min_log_level_value() -> int:
    """Get configured minimum log level as numeric value."""
    global _LOG_LEVEL_VALUE
    if _LOG_LEVEL_VALUE is None:
        raw = os.environ.get("CURDX_HOOK_LOG_LEVEL", "DEBUG").strip().upper()
        if raw == "WARNING":
            raw = "WARN"
        _LOG_LEVEL_VALUE = _LOG_LEVELS.get(raw, _LOG_LEVELS["DEBUG"])
    return _LOG_LEVEL_VALUE


def _is_split_log_enabled() -> bool:
    """Check whether per-hook log files are enabled."""
    global _LOG_SPLIT_ENABLED
    if _LOG_SPLIT_ENABLED is None:
        _LOG_SPLIT_ENABLED = _parse_bool_env("CURDX_HOOK_LOG_SPLIT", True)
    return _LOG_SPLIT_ENABLED


def _is_jsonl_enabled() -> bool:
    """Check whether JSONL output is enabled."""
    global _LOG_JSONL_ENABLED
    if _LOG_JSONL_ENABLED is None:
        _LOG_JSONL_ENABLED = _parse_bool_env("CURDX_HOOK_LOG_JSONL", True)
    return _LOG_JSONL_ENABLED


def _is_session_split_enabled() -> bool:
    """Check whether session-scoped log files are enabled."""
    global _LOG_SESSION_SPLIT_ENABLED
    if _LOG_SESSION_SPLIT_ENABLED is None:
        _LOG_SESSION_SPLIT_ENABLED = _parse_bool_env("CURDX_HOOK_LOG_SESSION_SPLIT", True)
    return _LOG_SESSION_SPLIT_ENABLED


def _should_log_level(level: str) -> bool:
    """Check level threshold against configured minimum."""
    normalized = _normalize_level(level)
    return _LOG_LEVELS[normalized] >= _min_log_level_value()


def _rotate_if_needed(log_file: Path) -> None:
    """Rotate log file if it exceeds size limit."""
    try:
        if log_file.exists() and log_file.stat().st_size > _LOG_MAX_BYTES:
            rotated = log_file.with_name(f"{log_file.name}.1")
            if rotated.exists():
                rotated.unlink()
            log_file.rename(rotated)
    except OSError:
        pass


def _resolve_session_id(session_id: str | None = None) -> str:
    """Resolve best-available session id for log correlation."""
    if session_id and session_id.strip():
        return session_id.strip()
    for env_name in ("CURDX_SESSION_ID", "CLAUDE_SESSION_ID", "ANTHROPIC_SESSION_ID"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    return "default"


def _hook_log_file(hook_name: str) -> Path:
    """Build per-hook log path with a filesystem-safe name."""
    safe_hook = _sanitize_component(hook_name, default="unknown")
    return _LOG_DIR / f"hooks.{safe_hook}.log"


def _hook_jsonl_file(hook_name: str) -> Path:
    """Build per-hook JSONL path with a filesystem-safe name."""
    safe_hook = _sanitize_component(hook_name, default="unknown")
    return _LOG_DIR / f"hooks.{safe_hook}.jsonl"


def _session_log_dir(session_id: str) -> Path:
    """Build session log directory path."""
    safe_session = _sanitize_component(session_id, default="default")
    return _LOG_DIR / "sessions" / safe_session


def _sanitize_component(value: str, default: str) -> str:
    """Sanitize a value for use in file names and directories."""
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    if not safe:
        return default
    return safe


def _build_text_line(
    *,
    ts: str,
    level: str,
    hook_name: str,
    event: str,
    session: str,
    pid: int,
    message: str,
    tool: str = "",
    file: str = "",
    decision: str = "",
    duration_ms: float | None = None,
    extra: dict | None = None,
) -> str:
    """Build text log line."""
    parts = [f"[{ts}]", f"[{level}]", f"[{hook_name}]", f"[{event}]", f"session={session}", f"pid={pid}"]
    if tool:
        parts.append(f"tool={tool}")
    if file:
        parts.append(f"file={file}")
    if decision:
        parts.append(f"decision={decision}")
    if duration_ms is not None:
        parts.append(f"dur={duration_ms:.1f}ms")
    if extra:
        parts.extend(f"{k}={v}" for k, v in extra.items())
    parts.append(f"| {message}")
    return " ".join(parts) + "\n"


def _build_event_payload(
    *,
    ts: str,
    level: str,
    hook_name: str,
    event: str,
    session: str,
    pid: int,
    message: str,
    tool: str = "",
    file: str = "",
    decision: str = "",
    duration_ms: float | None = None,
    extra: dict | None = None,
) -> dict:
    """Build structured event payload for JSONL."""
    payload: dict = {
        "ts": ts,
        "ts_unix_ms": int(time.time() * 1000),
        "level": level,
        "hook": hook_name,
        "event": event,
        "session": session,
        "pid": pid,
        "message": message,
    }
    if tool:
        payload["tool"] = tool
    if file:
        payload["file"] = file
    if decision:
        payload["decision"] = decision
    if duration_ms is not None:
        payload["duration_ms"] = round(duration_ms, 1)
    if extra:
        payload["extra"] = extra
    return payload


def _build_json_line(payload: dict) -> str:
    """Serialize payload to JSONL line."""
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n"


def _write_many(log_files: list[Path], content: str) -> None:
    """Write same content to multiple files."""
    for log_file in log_files:
        _write_log_line(log_file, content)


def _resolve_text_targets(hook_name: str, session_id: str) -> list[Path]:
    """Resolve target files for text output."""
    targets = [_LOG_FILE]
    if _is_split_log_enabled():
        targets.append(_hook_log_file(hook_name))
    if _is_session_split_enabled():
        session_dir = _session_log_dir(session_id)
        targets.append(session_dir / "hooks.log")
        if _is_split_log_enabled():
            targets.append(session_dir / f"hooks.{_sanitize_component(hook_name, 'unknown')}.log")
    return targets


def _resolve_jsonl_targets(hook_name: str, session_id: str) -> list[Path]:
    """Resolve target files for JSONL output."""
    if not _is_jsonl_enabled():
        return []
    targets = [_LOG_JSONL_FILE]
    if _is_split_log_enabled():
        targets.append(_hook_jsonl_file(hook_name))
    if _is_session_split_enabled():
        session_dir = _session_log_dir(session_id)
        targets.append(session_dir / "hooks.jsonl")
        if _is_split_log_enabled():
            targets.append(session_dir / f"hooks.{_sanitize_component(hook_name, 'unknown')}.jsonl")
    return targets


def _write_log_line(log_file: Path, line: str) -> None:
    """Append line to a log file with rotation."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    _rotate_if_needed(log_file)
    with log_file.open("a") as f:
        f.write(line)


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
    session_id: str | None = None,
) -> None:
    """Write structured hook logs to ~/.curdx/logs/."""
    level_norm = _normalize_level(level)
    if not _is_log_enabled() or not _should_log_level(level_norm):
        return

    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        session = _resolve_session_id(session_id)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        pid = os.getpid()
        text_line = _build_text_line(
            ts=ts,
            level=level_norm,
            hook_name=hook_name,
            event=event,
            session=session,
            pid=pid,
            message=message,
            tool=tool,
            file=file,
            decision=decision,
            duration_ms=duration_ms,
            extra=extra,
        )
        _write_many(_resolve_text_targets(hook_name, session), text_line)

        json_targets = _resolve_jsonl_targets(hook_name, session)
        if json_targets:
            payload = _build_event_payload(
                ts=ts,
                level=level_norm,
                hook_name=hook_name,
                event=event,
                session=session,
                pid=pid,
                message=message,
                tool=tool,
                file=file,
                decision=decision,
                duration_ms=duration_ms,
                extra=extra,
            )
            _write_many(json_targets, _build_json_line(payload))
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
        self._extra: dict = {}
        self._session_id: str | None = None

    def set(
        self,
        *,
        message: str = "",
        tool: str = "",
        file: str = "",
        decision: str = "",
        level: str = "",
        extra: dict | None = None,
        session_id: str = "",
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
            self._extra.update(extra)
        if session_id:
            self._session_id = session_id

    def __enter__(self) -> "HookTimer":
        self._start = time.monotonic()
        hook_log(self.hook_name, self.event, "started", level="DEBUG", session_id=self._session_id)
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
                session_id=self._session_id,
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
                extra=self._extra or None,
                session_id=self._session_id,
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
