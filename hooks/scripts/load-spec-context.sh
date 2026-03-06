#!/bin/bash
# SessionStart Hook for CURDX Specum
# Loads context for active spec on session start:
# 1. Detects active spec from .current-spec
# 2. Loads progress and state for context
# 3. Outputs summary for agent awareness

# Read hook input from stdin
INPUT=$(cat)

# Source logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_log.sh"
curdx_timer_start
curdx_log "load-spec-context" "SessionStart" "DEBUG" "started"

# Bail out cleanly if jq is unavailable
if ! command -v jq >/dev/null 2>&1; then
    curdx_log "load-spec-context" "SessionStart" "WARN" "jq not found, skipping" "decision=skip"
    exit 0
fi

# Get working directory (guard against parse failures)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty' 2>/dev/null || true)
if [ -z "$CWD" ]; then
    curdx_log "load-spec-context" "SessionStart" "WARN" "no cwd in input" "decision=skip"
    exit 0
fi

# Source path resolver for multi-directory support
if [ -f "$SCRIPT_DIR/path-resolver.sh" ]; then
    export RALPH_CWD="$CWD"
    # shellcheck source=path-resolver.sh
    source "$SCRIPT_DIR/path-resolver.sh"
else
    # Fallback if path-resolver.sh not found
    exit 0
fi

# Check for settings file to see if plugin is enabled
SETTINGS_FILE="$CWD/.claude/curdx.local.md"
if [ -f "$SETTINGS_FILE" ]; then
    # Extract enabled setting from YAML frontmatter (normalize case and strip quotes)
    ENABLED=$(sed -n '/^---$/,/^---$/p' "$SETTINGS_FILE" 2>/dev/null \
        | awk -F: '/^enabled:/{val=$2; gsub(/[[:space:]"'"'"']/, "", val); print tolower(val); exit}')
    if [ "$ENABLED" = "false" ]; then
        curdx_log "load-spec-context" "SessionStart" "INFO" "plugin disabled via settings" "decision=skip"
        exit 0
    fi
fi

# Resolve current spec using path resolver
SPEC_RELATIVE_PATH=$(curdx_resolve_current 2>/dev/null)
if [ -z "$SPEC_RELATIVE_PATH" ]; then
    curdx_log "load-spec-context" "SessionStart" "INFO" "no active spec" "decision=skip"
    exit 0
fi

SPEC_PATH="$CWD/$SPEC_RELATIVE_PATH"
if [ ! -d "$SPEC_PATH" ]; then
    curdx_log "load-spec-context" "SessionStart" "WARN" "spec dir not found: $SPEC_PATH (resolved: $SPEC_RELATIVE_PATH)" "decision=skip"
    exit 0
fi

# Extract spec name from path (last component)
SPEC_NAME=$(basename "$SPEC_RELATIVE_PATH")

# Read state file if exists
STATE_FILE="$SPEC_PATH/.curdx-state.json"
PROGRESS_FILE="$SPEC_PATH/.progress.md"

echo "[curdx] Active spec detected: $SPEC_NAME" >&2

# Output state summary if state file exists
if [ -f "$STATE_FILE" ] && jq empty "$STATE_FILE" 2>/dev/null; then
    PHASE=$(jq -r '.phase // "unknown"' "$STATE_FILE" 2>/dev/null)
    TASK_INDEX=$(jq -r '.taskIndex // 0' "$STATE_FILE" 2>/dev/null)
    TOTAL_TASKS=$(jq -r '.totalTasks // 0' "$STATE_FILE" 2>/dev/null)
    AWAITING=$(jq -r '.awaitingApproval // false' "$STATE_FILE" 2>/dev/null)

    echo "[curdx] Phase: $PHASE | Task: $((TASK_INDEX + 1))/$TOTAL_TASKS | Awaiting approval: $AWAITING" >&2

    if [ "$PHASE" = "execution" ] && [ "$AWAITING" = "false" ]; then
        echo "[curdx] Execution in progress. Run /curdx:implement to continue." >&2
    elif [ "$AWAITING" = "true" ]; then
        case "$PHASE" in
            research)
                echo "[curdx] Research complete. Run /curdx:requirements to continue." >&2
                ;;
            requirements)
                echo "[curdx] Requirements complete. Run /curdx:design to continue." >&2
                ;;
            design)
                echo "[curdx] Design complete. Run /curdx:tasks to continue." >&2
                ;;
            tasks)
                echo "[curdx] Tasks complete. Run /curdx:implement to start execution." >&2
                ;;
        esac
    fi
else
    # No state file - check what spec files exist
    if [ -f "$SPEC_PATH/tasks.md" ]; then
        echo "[curdx] Tasks defined but no execution state. Run /curdx:implement to start." >&2
    elif [ -f "$SPEC_PATH/design.md" ]; then
        echo "[curdx] Design exists. Run /curdx:tasks to generate tasks." >&2
    elif [ -f "$SPEC_PATH/requirements.md" ]; then
        echo "[curdx] Requirements exist. Run /curdx:design to continue." >&2
    elif [ -f "$SPEC_PATH/research.md" ]; then
        echo "[curdx] Research exists. Run /curdx:requirements to continue." >&2
    fi
fi

# Output original goal from progress file if exists
if [ -f "$PROGRESS_FILE" ]; then
    GOAL=$(grep -A1 "^## Original Goal" "$PROGRESS_FILE" 2>/dev/null | tail -1)
    if [ -n "$GOAL" ]; then
        echo "[curdx] Goal: $GOAL" >&2
    fi
fi

ELAPSED=$(curdx_timer_elapsed)
curdx_log "load-spec-context" "SessionStart" "INFO" "loaded context for $SPEC_NAME" "spec=$SPEC_NAME" "phase=${PHASE:-unknown}" "dur=${ELAPSED}ms" "decision=context"

exit 0
