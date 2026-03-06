"""File quality gate — auto-format + file length check.

Runs formatting (ruff/prettier/gofmt) and file length checks via additionalContext.
Warnings are non-blocking — they inform but never prevent edits.
TDD enforcement is handled separately by tdd-guard.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _checkers.go import check_go
from _checkers.python import check_python
from _checkers.typescript import TS_EXTENSIONS, check_typescript
from _util import HookTimer, find_git_root, post_tool_use_context


def main() -> int:
    """Single entry point — file quality check."""
    with HookTimer("file_checker", "PostToolUse") as t:
        try:
            hook_data = json.load(sys.stdin)
        except (json.JSONDecodeError, OSError):
            t.set(message="invalid JSON input", level="WARN", decision="allow")
            return 0

        tool_input = hook_data.get("tool_input", {})
        file_path_str = tool_input.get("file_path", "")
        if not file_path_str:
            t.set(message="no file_path in input", decision="skip")
            return 0

        target_file = Path(file_path_str)
        t.set(tool=hook_data.get("tool_name", ""), file=file_path_str)

        if not target_file.exists():
            t.set(message="file does not exist", decision="skip")
            return 0

        git_root = find_git_root()
        if git_root:
            os.chdir(git_root)

        file_reason = ""
        checker = "none"
        if target_file.suffix == ".py":
            checker = "python"
            _, file_reason = check_python(target_file)
        elif target_file.suffix in TS_EXTENSIONS:
            checker = "typescript"
            _, file_reason = check_typescript(target_file)
        elif target_file.suffix == ".go":
            checker = "go"
            _, file_reason = check_go(target_file)

        if file_reason:
            print(post_tool_use_context(file_reason))
            t.set(message=f"quality issue found", decision="context", extra={"checker": checker, "reason": file_reason[:80]})
        else:
            t.set(message=f"file OK", decision="allow", extra={"checker": checker})

        return 0


if __name__ == "__main__":
    sys.exit(main())
