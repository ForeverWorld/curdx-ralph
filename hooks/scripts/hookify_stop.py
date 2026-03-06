#!/usr/bin/env python3
"""Stop hook executor for hookify plugin.

This script is called by Claude Code when agent wants to stop.
It reads .claude/hookify.*.local.md files and evaluates stop rules.
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import HookTimer

# CRITICAL: Add plugin root to Python path for imports
PLUGIN_ROOT = os.environ.get('CLAUDE_PLUGIN_ROOT')
if PLUGIN_ROOT:
    parent_dir = PLUGIN_ROOT
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    if PLUGIN_ROOT not in sys.path:
        sys.path.insert(0, PLUGIN_ROOT)

try:
    from hookify.core.config_loader import load_rules
    from hookify.core.rule_engine import RuleEngine
except ImportError as e:
    error_msg = {"systemMessage": f"Hookify import error: {e}"}
    print(json.dumps(error_msg), file=sys.stdout)
    sys.exit(0)


def main():
    """Main entry point for Stop hook."""
    with HookTimer("hookify_stop", "Stop") as t:
        try:
            input_data = json.load(sys.stdin)

            rules = load_rules(event='stop')
            t.set(extra={"rules_count": str(len(rules))})

            engine = RuleEngine()
            result = engine.evaluate_rules(rules, input_data)

            if result:
                t.set(message=f"stop rules evaluated, result has keys: {list(result.keys())}", decision="applied")
            else:
                t.set(message="no stop rules matched", decision="allow")

            print(json.dumps(result), file=sys.stdout)

        except Exception as e:
            error_output = {
                "systemMessage": f"Hookify error: {str(e)}"
            }
            print(json.dumps(error_output), file=sys.stdout)
            t.set(message=f"error: {e}", level="ERROR", decision="allow")

        finally:
            sys.exit(0)


if __name__ == '__main__':
    main()
