#!/usr/bin/env python3
"""Summarize CURDX hook JSONL logs for AI-driven analysis."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

LOG_DIR = Path.home() / ".curdx" / "logs"
DEFAULT_LOG_FILE = LOG_DIR / "hooks.jsonl"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


def _sanitize_component(value: str, default: str = "default") -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return safe or default


def _event_ts_ms(event: dict[str, Any]) -> int:
    raw = event.get("ts_unix_ms")
    if isinstance(raw, (int, float)):
        return int(raw)

    ts = event.get("ts")
    if isinstance(ts, str) and ts:
        try:
            dt = datetime.strptime(ts, TIME_FORMAT)
            return int(dt.timestamp() * 1000)
        except ValueError:
            pass
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze CURDX hook JSONL logs.")
    parser.add_argument("--session", help="Session id (reads ~/.curdx/logs/sessions/<id>/hooks.jsonl)")
    parser.add_argument("--hook", help="Filter by hook name")
    parser.add_argument("--event", help="Filter by event name")
    parser.add_argument("--since-minutes", type=int, default=0, help="Only include events from last N minutes")
    parser.add_argument("--min-level", choices=["DEBUG", "INFO", "WARN", "ERROR"], help="Minimum level filter")
    parser.add_argument("--limit-errors", type=int, default=20, help="Max errors/warnings to include")
    parser.add_argument("--limit-blocks", type=int, default=20, help="Max block/deny events to include")
    parser.add_argument("--limit-slow", type=int, default=20, help="Max slow events to include")
    return parser.parse_args()


def _resolve_log_file(session_id: str | None) -> Path:
    if not session_id:
        return DEFAULT_LOG_FILE
    safe_session = _sanitize_component(session_id)
    return LOG_DIR / "sessions" / safe_session / "hooks.jsonl"


def _load_events(log_file: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not log_file.exists():
        return events

    try:
        with log_file.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    events.append(parsed)
    except OSError:
        return []
    return events


def _level_value(level: str) -> int:
    mapping = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}
    return mapping.get(level.upper(), 20)


def _filter_events(events: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    filtered = events
    if args.hook:
        filtered = [e for e in filtered if e.get("hook") == args.hook]
    if args.event:
        filtered = [e for e in filtered if e.get("event") == args.event]
    if args.min_level:
        min_value = _level_value(args.min_level)
        filtered = [e for e in filtered if _level_value(str(e.get("level", "INFO"))) >= min_value]
    if args.since_minutes and args.since_minutes > 0:
        cutoff = int(time.time() * 1000) - (args.since_minutes * 60 * 1000)
        filtered = [e for e in filtered if _event_ts_ms(e) >= cutoff]
    return filtered


def _event_excerpt(event: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "ts": event.get("ts"),
        "level": event.get("level"),
        "hook": event.get("hook"),
        "event": event.get("event"),
        "session": event.get("session"),
        "message": event.get("message"),
    }
    for key in ("decision", "tool", "file", "duration_ms", "extra"):
        if key in event:
            out[key] = event[key]
    return out


def _top_by_ts_desc(events: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return [_event_excerpt(e) for e in sorted(events, key=_event_ts_ms, reverse=True)[:limit]]


def _top_slow(events: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    with_duration = [e for e in events if isinstance(e.get("duration_ms"), (int, float))]
    ranked = sorted(with_duration, key=lambda e: float(e.get("duration_ms", 0.0)), reverse=True)
    return [_event_excerpt(e) for e in ranked[:limit]]


def main() -> int:
    args = _parse_args()
    log_file = _resolve_log_file(args.session)
    all_events = _load_events(log_file)
    events = _filter_events(all_events, args)

    by_level = Counter(str(e.get("level", "INFO")) for e in events)
    by_hook = Counter(str(e.get("hook", "unknown")) for e in events)
    by_event = Counter(str(e.get("event", "unknown")) for e in events)
    by_decision = Counter(str(e.get("decision", "none")) for e in events if e.get("decision"))

    error_like = [e for e in events if str(e.get("level", "")).upper() in {"ERROR", "WARN"}]
    blocked = [e for e in events if str(e.get("decision", "")).lower() in {"deny", "block"}]

    ts_values = sorted(ts for ts in (_event_ts_ms(e) for e in events) if ts > 0)
    time_range = {}
    if ts_values:
        time_range = {
            "from_unix_ms": ts_values[0],
            "to_unix_ms": ts_values[-1],
        }

    payload = {
        "source": str(log_file),
        "source_exists": log_file.exists(),
        "total_events": len(events),
        "total_events_before_filter": len(all_events),
        "filters": {
            "session": args.session or "",
            "hook": args.hook or "",
            "event": args.event or "",
            "since_minutes": args.since_minutes,
            "min_level": args.min_level or "",
        },
        "time_range": time_range,
        "counts": {
            "by_level": dict(by_level),
            "by_hook": dict(by_hook),
            "by_event": dict(by_event),
            "by_decision": dict(by_decision),
        },
        "latest_errors_or_warnings": _top_by_ts_desc(error_like, args.limit_errors),
        "latest_block_or_deny": _top_by_ts_desc(blocked, args.limit_blocks),
        "slowest_events": _top_slow(events, args.limit_slow),
    }
    json.dump(payload, sys.stdout, ensure_ascii=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
