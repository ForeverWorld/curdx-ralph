#!/usr/bin/env bash
# PreToolUse hook: Block AskUserQuestion in quick mode
# Reads .curdx-state.json and denies the call if quickMode is true.

set -euo pipefail

INPUT=$(cat)

# Source logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_log.sh"
curdx_timer_start

# Bail out if jq is unavailable
if ! command -v jq >/dev/null 2>&1; then
    curdx_log "quick-mode-guard" "PreToolUse" "WARN" "jq not found, skipping" "decision=skip"
    exit 0
fi

# Set session id for log correlation when available
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null || true)
if [ -n "$SESSION_ID" ]; then
    export CURDX_SESSION_ID="$SESSION_ID"
fi

# Get working directory
CWD=$(echo "$INPUT" | jq -r '.cwd // empty' 2>/dev/null || true)
if [ -z "$CWD" ]; then
    curdx_log "quick-mode-guard" "PreToolUse" "WARN" "no cwd in input" "decision=allow"
    exit 0
fi

# Source path resolver
RALPH_CWD="$CWD"
export RALPH_CWD
source "$SCRIPT_DIR/path-resolver.sh"

# Resolve current spec
SPEC_PATH=$(curdx_resolve_current 2>/dev/null) || true
if [ -z "$SPEC_PATH" ]; then
    curdx_log "quick-mode-guard" "PreToolUse" "DEBUG" "no active spec" "decision=allow"
    exit 0
fi

STATE_FILE="$CWD/$SPEC_PATH/.curdx-state.json"
if [ ! -f "$STATE_FILE" ]; then
    curdx_log "quick-mode-guard" "PreToolUse" "DEBUG" "no state file" "decision=allow"
    exit 0
fi

# Check quickMode flag
QUICK_MODE=$(jq -r '.quickMode // false' "$STATE_FILE" 2>/dev/null || echo "false")
if [ "$QUICK_MODE" != "true" ]; then
    curdx_log "quick-mode-guard" "PreToolUse" "DEBUG" "not in quick mode" "decision=allow"
    exit 0
fi

# Quick mode is active — block AskUserQuestion
ELAPSED=$(curdx_timer_elapsed)
curdx_log "quick-mode-guard" "PreToolUse" "INFO" "blocking AskUserQuestion in quick mode" "spec=$SPEC_PATH" "dur=${ELAPSED}ms" "decision=deny"
jq -n '{
  "hookSpecificOutput": {
    "permissionDecision": "deny"
  },
  "systemMessage": "Quick mode active: do NOT ask the user any questions. Make opinionated decisions autonomously. Choose the simplest, most conventional approach."
}'
