#!/usr/bin/env bash
# Stop Hook for CURDX Specum — Loop controller for task execution continuation
# Exits silently (code 0) when no active spec, outputs block JSON when tasks remain.

# Read hook input from stdin
INPUT=$(cat)

# Source logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_log.sh"
curdx_timer_start

# Bail out cleanly if jq is unavailable
if ! command -v jq >/dev/null 2>&1; then
    curdx_log "stop-watcher" "Stop" "WARN" "jq not found, skipping" "decision=allow"
    exit 0
fi

# Set session id for log correlation when available
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null || true)
if [ -n "$SESSION_ID" ]; then
    export CURDX_SESSION_ID="$SESSION_ID"
fi
curdx_log "stop-watcher" "Stop" "DEBUG" "started"

# Get working directory (guard against parse failures)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty' 2>/dev/null || true)
if [ -z "$CWD" ]; then
    curdx_log "stop-watcher" "Stop" "WARN" "no cwd in input" "decision=allow"
    exit 0
fi

# Source path resolver for spec directory resolution
RALPH_CWD="$CWD"
export RALPH_CWD
source "$SCRIPT_DIR/path-resolver.sh"

# Check for settings file to see if plugin is enabled
SETTINGS_FILE="$CWD/.claude/curdx.local.md"
if [ -f "$SETTINGS_FILE" ]; then
    # Extract enabled setting from YAML frontmatter (normalize case and strip quotes)
    ENABLED=$(sed -n '/^---$/,/^---$/p' "$SETTINGS_FILE" 2>/dev/null \
        | awk -F: '/^enabled:/{val=$2; gsub(/[[:space:]"'"'"']/, "", val); print tolower(val); exit}')
    if [ "$ENABLED" = "false" ]; then
        curdx_log "stop-watcher" "Stop" "INFO" "plugin disabled via settings" "decision=allow"
        exit 0
    fi
fi

# Resolve current spec using path resolver (handles multi-directory support)
SPEC_PATH=$(curdx_resolve_current 2>/dev/null)
if [ -z "$SPEC_PATH" ]; then
    curdx_log "stop-watcher" "Stop" "DEBUG" "no active spec" "decision=allow"
    exit 0
fi

# Extract spec name from path (last component)
SPEC_NAME=$(basename "$SPEC_PATH")

STATE_FILE="$CWD/$SPEC_PATH/.curdx-state.json"
if [ ! -f "$STATE_FILE" ]; then
    curdx_log "stop-watcher" "Stop" "DEBUG" "no state file for $SPEC_NAME" "decision=allow"
    exit 0
fi

curdx_has_completion_signal() {
    local text="$1"
    [ -n "$text" ] || return 1
    while IFS= read -r line; do
        local trimmed
        trimmed=$(printf "%s" "$line" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
        if [ "$trimmed" = "ALL_TASKS_COMPLETE" ]; then
            return 0
        fi
    done <<< "$text"
    return 1
}

curdx_mark_completion_side_effects() {
    # Update epic state if this spec belongs to an epic.
    local epic_name_val current_epic_file epic_state_file tmp_file
    epic_name_val=$(jq -r '.epicName // empty' "$STATE_FILE" 2>/dev/null || true)
    current_epic_file="$CWD/specs/.current-epic"
    if [ -n "$epic_name_val" ] && [ -f "$current_epic_file" ]; then
        epic_state_file="$CWD/specs/_epics/$epic_name_val/.epic-state.json"
        if [ -f "$epic_state_file" ]; then
            tmp_file=$(mktemp "${epic_state_file}.tmp.XXXXXX")
            if jq --arg spec "$SPEC_NAME" '
              .specs |= map(if .name == $spec then .status = "completed" else . end)
            ' "$epic_state_file" > "$tmp_file"; then
                mv "$tmp_file" "$epic_state_file"
            else
                rm -f "$tmp_file"
            fi
            echo "[curdx] Updated epic '$epic_name_val': spec '$SPEC_NAME' marked completed" >&2
        fi
    fi
    "$SCRIPT_DIR/update-spec-index.sh" --quiet 2>/dev/null || true
}

# Race condition safeguard: if state file was modified in last 2 seconds, wait briefly
# This allows the coordinator to finish writing before we read
if command -v stat >/dev/null 2>&1; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS stat
        MTIME=$(stat -f %m "$STATE_FILE" 2>/dev/null || echo "0")
    else
        # Linux stat
        MTIME=$(stat -c %Y "$STATE_FILE" 2>/dev/null || echo "0")
    fi
    NOW=$(date +%s)
    AGE=$((NOW - MTIME))
    if [ "$AGE" -lt 2 ]; then
        sleep 1
    fi
fi

# Check completion signal from latest assistant turn first.
# This avoids transcript-wide false positives when prompts mention ALL_TASKS_COMPLETE.
LAST_ASSISTANT_MESSAGE=$(echo "$INPUT" | jq -r '.last_assistant_message // empty' 2>/dev/null || true)
if curdx_has_completion_signal "$LAST_ASSISTANT_MESSAGE"; then
    echo "[curdx] ALL_TASKS_COMPLETE detected in last_assistant_message" >&2
    curdx_log "stop-watcher" "Stop" "INFO" "ALL_TASKS_COMPLETE detected" "spec=$SPEC_NAME" "source=last_assistant_message" "decision=allow"
    curdx_mark_completion_side_effects
    exit 0
fi

# Fallback for older clients without last_assistant_message.
# Match only exact standalone signal lines to avoid broad false positives.
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null || true)
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    if tail -120 "$TRANSCRIPT_PATH" 2>/dev/null | grep -qE '^[[:space:]]*ALL_TASKS_COMPLETE[[:space:]]*$'; then
        echo "[curdx] ALL_TASKS_COMPLETE detected in transcript (strict line match)" >&2
        curdx_log "stop-watcher" "Stop" "INFO" "ALL_TASKS_COMPLETE detected" "spec=$SPEC_NAME" "source=transcript_tail" "decision=allow"
        curdx_mark_completion_side_effects
        exit 0
    fi
fi

# Validate state file is readable JSON
if ! jq empty "$STATE_FILE" 2>/dev/null; then
    REASON=$(cat <<EOF
ERROR: Corrupt state file at $SPEC_PATH/.curdx-state.json

Recovery options:
1. Reset state: /curdx:implement (reinitializes from tasks.md)
2. Cancel spec: /curdx:cancel
EOF
)

    jq -n \
      --arg reason "$REASON" \
      --arg msg "CURDX: corrupt state file" \
      '{
        "decision": "block",
        "reason": $reason,
        "systemMessage": $msg
      }'
    exit 0
fi

# Read state
PHASE=$(jq -r '.phase // "unknown"' "$STATE_FILE" 2>/dev/null || echo "unknown")
TASK_INDEX=$(jq -r '.taskIndex // 0' "$STATE_FILE" 2>/dev/null || echo "0")
TOTAL_TASKS=$(jq -r '.totalTasks // 0' "$STATE_FILE" 2>/dev/null || echo "0")
TASK_ITERATION=$(jq -r '.taskIteration // 1' "$STATE_FILE" 2>/dev/null || echo "1")
QUICK_MODE=$(jq -r '.quickMode // false' "$STATE_FILE" 2>/dev/null || echo "false")
NATIVE_SYNC=$(jq -r '.nativeSyncEnabled // true' "$STATE_FILE" 2>/dev/null || echo "true")

# Check global iteration limit
GLOBAL_ITERATION=$(jq -r '.globalIteration // 1' "$STATE_FILE" 2>/dev/null || echo "1")
MAX_GLOBAL=$(jq -r '.maxGlobalIterations // 100' "$STATE_FILE" 2>/dev/null || echo "100")

if [ "$GLOBAL_ITERATION" -ge "$MAX_GLOBAL" ]; then
    echo "[curdx] ERROR: Maximum global iterations ($MAX_GLOBAL) reached. Review .progress.md for failure patterns." >&2
    echo "[curdx] Recovery: fix issues manually, then run /curdx:implement or /curdx:cancel" >&2
    exit 0
fi

# Quick mode guard: block stop during ANY phase when quickMode is active
if [ "$QUICK_MODE" = "true" ] && [ "$PHASE" != "execution" ]; then
    STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false' 2>/dev/null || echo "false")
    if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
        echo "[curdx] stop_hook_active=true in quick mode, allowing stop to prevent loop" >&2
        curdx_log "stop-watcher" "Stop" "WARN" "stop_hook_active in quick mode, allowing to prevent loop" "spec=$SPEC_NAME" "phase=$PHASE" "decision=allow"
        exit 0
    fi

    curdx_log "stop-watcher" "Stop" "INFO" "blocking stop in quick mode" "spec=$SPEC_NAME" "phase=$PHASE" "decision=block"

    REASON=$(cat <<EOF
Quick mode active — do NOT stop. Continue spec phase: $PHASE for $SPEC_NAME.

You are running in quick mode. Do NOT stop, do NOT ask the user questions.
Continue generating artifacts for the current phase ($PHASE) and proceed to the next phase.
Make strong, opinionated decisions autonomously.
EOF
)
    jq -n \
      --arg reason "$REASON" \
      --arg msg "CURDX quick mode: continue $PHASE phase" \
      '{
        "decision": "block",
        "reason": $reason,
        "systemMessage": $msg
      }'
    exit 0
fi

# Log current state
if [ "$PHASE" = "execution" ]; then
    echo "[curdx] Session stopped during spec: $SPEC_NAME | Task: $((TASK_INDEX + 1))/$TOTAL_TASKS | Attempt: $TASK_ITERATION" >&2
fi

# Execution completion verification: cross-check state AND tasks.md
if [ "$PHASE" = "execution" ] && [ "$TASK_INDEX" -ge "$TOTAL_TASKS" ] && [ "$TOTAL_TASKS" -gt 0 ]; then
    TASKS_FILE="$CWD/$SPEC_PATH/tasks.md"
    if [ -f "$TASKS_FILE" ]; then
        UNCHECKED=$(grep -c '^\s*- \[ \]' "$TASKS_FILE" 2>/dev/null)
        UNCHECKED=${UNCHECKED:-0}
        if [ "$UNCHECKED" -gt 0 ]; then
            echo "[curdx] State says complete but tasks.md has $UNCHECKED unchecked items" >&2
            REASON=$(cat <<EOF
Tasks incomplete: state index ($TASK_INDEX) reached total ($TOTAL_TASKS), but tasks.md has $UNCHECKED unchecked items.

## Action Required
1. Read $SPEC_PATH/tasks.md and find unchecked tasks (- [ ])
2. Execute remaining unchecked tasks via spec-executor
3. Update .curdx-state.json totalTasks to match actual count
4. Only output ALL_TASKS_COMPLETE when every task in tasks.md is checked off
5. Do NOT add new tasks — complete existing ones only
EOF
)
            jq -n \
              --arg reason "$REASON" \
              --arg msg "CURDX: $UNCHECKED unchecked tasks remain in tasks.md" \
              '{
                "decision": "block",
                "reason": $reason,
                "systemMessage": $msg
              }'
            exit 0
        fi
    fi
    # All tasks verified complete — allow stop
    echo "[curdx] All tasks verified complete for $SPEC_NAME" >&2
    exit 0
fi

# Loop control: output continuation prompt if more tasks remain
if [ "$PHASE" = "execution" ] && [ "$TASK_INDEX" -lt "$TOTAL_TASKS" ]; then
    # Respect user approval gates (e.g. PR creation, manual review steps)
    AWAITING=$(jq -r '.awaitingApproval // false' "$STATE_FILE" 2>/dev/null || echo "false")
    if [ "$AWAITING" = "true" ]; then
        echo "[curdx] awaitingApproval=true, allowing stop for user gate" >&2
        curdx_log "stop-watcher" "Stop" "INFO" "awaitingApproval, allowing stop" "spec=$SPEC_NAME" "task=$((TASK_INDEX+1))/$TOTAL_TASKS" "decision=allow"
        exit 0
    fi

    # Read recovery mode for prompt customization
    RECOVERY_MODE=$(jq -r '.recoveryMode // false' "$STATE_FILE" 2>/dev/null || echo "false")
    MAX_TASK_ITER=$(jq -r '.maxTaskIterations // 5' "$STATE_FILE" 2>/dev/null || echo "5")

    # Safety guard: prevent infinite re-invocation loop
    # If a stop event fires while already processing a stop-hook continuation,
    # re-blocking would cause infinite loops. Allow Claude to stop; the next
    # session start will detect remaining tasks via .curdx-state.json.
    # Claude Code sets stop_hook_active: true in Stop hook input when a stop
    # fires during an existing stop-hook continuation.
    STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false' 2>/dev/null || echo "false")
    if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
        echo "[curdx] stop_hook_active=true, skipping continuation to prevent re-invocation loop" >&2
        curdx_log "stop-watcher" "Stop" "WARN" "stop_hook_active, preventing re-invocation loop" "spec=$SPEC_NAME" "task=$((TASK_INDEX+1))/$TOTAL_TASKS" "decision=allow"
        exit 0
    fi

    # Extract current task block from tasks.md for inline continuation
    TASKS_FILE="$CWD/$SPEC_PATH/tasks.md"
    TASK_BLOCK=""
    if [ -f "$TASKS_FILE" ]; then
        # Extract task at TASK_INDEX (0-based) by counting unchecked+checked task lines
        # If TASK_INDEX exceeds number of tasks, awk outputs nothing (TASK_BLOCK stays empty)
        # and the coordinator falls back to reading tasks.md directly
        # Note: awk count variable starts at 0 (default) to match 0-based TASK_INDEX
        TASK_BLOCK=$(awk -v idx="$TASK_INDEX" '
            /^- \[[ x]\]/ {
                if (found) { exit }
                if (count == idx) { found=1; print; next }
                count++
            }
            found && /^  / { print; next }
            found && /^$/ { print; next }
            found && !/^  / && !/^$/ { exit }
        ' "$TASKS_FILE" | sed -e :a -e '/^[[:space:]]*$/{' -e '$d' -e N -e ba -e '}')
    fi

    # Parallel group detection: if current task has [P] marker, scan for consecutive [P] tasks and include all in continuation prompt
    IS_PARALLEL="false"
    if echo "$TASK_BLOCK" | head -1 | grep -q '\[P\]'; then
        IS_PARALLEL="true"
    fi

    # When parallel marker detected, scan for all consecutive [P] tasks from TASK_INDEX
    if [ "$IS_PARALLEL" = "true" ] && [ -f "$TASKS_FILE" ]; then
        PARALLEL_TASKS=$(awk -v idx="$TASK_INDEX" -v max_group=5 '
            /^- \[[ x]\]/ {
                if (count >= idx) {
                    if (/\[P\]/ && pcount < max_group) { found=1; pcount++; block=block $0 "\n"; next }
                    else if (found) { exit }
                }
                count++
            }
            found && /^  / { block=block $0 "\n"; next }
            found && /^$/ { block=block $0 "\n"; next }
            found && !/^  / && !/^$/ { exit }
            END { printf "%s", block }
        ' "$TASKS_FILE")
        if [ -n "$PARALLEL_TASKS" ]; then
            TASK_BLOCK="$PARALLEL_TASKS"
        fi
    fi

    # DESIGN NOTE: Prompt Duplication
    # This continuation prompt is intentionally abbreviated compared to implement.md.
    # - implement.md = full specification (source of truth for coordinator behavior)
    # - stop-watcher.sh = abbreviated resume prompt (minimal context for loop continuation)
    # This is an intentional design choice, not accidental duplication. The full
    # specification lives in implement.md; this prompt provides just enough context
    # for the coordinator to resume execution efficiently.

    # Build task section header and instructions based on parallel mode
    if [ "$IS_PARALLEL" = "true" ]; then
        TASK_HEADER="## Current Task Group (PARALLEL)"
        PARALLEL_INSTRUCTIONS="
PARALLEL: These are [P] tasks -- dispatch ALL in ONE message via Task tool. Each gets progressFile: .progress-task-\$INDEX.md. After all complete: merge progress, advance taskIndex past group."
    else
        TASK_HEADER="## Current Task"
        PARALLEL_INSTRUCTIONS=""
    fi

    REASON=$(cat <<STOP_WATCHER_REASON_EOF
Continue spec: $SPEC_NAME (Task $((TASK_INDEX + 1))/$TOTAL_TASKS, Iter $GLOBAL_ITERATION)

## State
Path: $SPEC_PATH | Index: $TASK_INDEX | Iteration: $TASK_ITERATION/$MAX_TASK_ITER | Recovery: $RECOVERY_MODE | NativeSync: $NATIVE_SYNC

$TASK_HEADER
$TASK_BLOCK
$PARALLEL_INSTRUCTIONS

## Resume
1. Read $SPEC_PATH/.curdx-state.json for current state
2. Native sync (if NativeSync != false): (a) if nativeTaskMap is empty, rebuild from tasks.md (TaskCreate all, store IDs in state), (b) TaskUpdate current task to in_progress with activeForm
3. Delegate the task above to spec-executor (or qa-engineer for [VERIFY])
4. On TASK_COMPLETE: verify, update state, advance. Then TaskUpdate task to completed (if NativeSync != false)
5. If taskIndex >= totalTasks: finalize all native tasks to completed (if NativeSync != false), read $SPEC_PATH/tasks.md to verify all [x], delete state file, output ALL_TASKS_COMPLETE

## Critical
- Delegate via Task tool - do NOT implement yourself
- Verify all 3 layers before advancing (see verification-layers.md)
- Do NOT push after every commit - batch pushes per phase or every 5 commits (see coordinator-pattern.md § 'Git Push Strategy')
- On failure: increment taskIteration, retry or generate fix task if recoveryMode
- On TASK_MODIFICATION_REQUEST: validate, insert tasks, update state (see coordinator-pattern.md § 'Modification Request Handler')
STOP_WATCHER_REASON_EOF
)

    SYSTEM_MSG="CURDX iteration $GLOBAL_ITERATION | Task $((TASK_INDEX + 1))/$TOTAL_TASKS"
    if [ "$IS_PARALLEL" = "true" ]; then
        SYSTEM_MSG="$SYSTEM_MSG (PARALLEL GROUP)"
    fi

    ELAPSED=$(curdx_timer_elapsed)
    curdx_log "stop-watcher" "Stop" "INFO" "blocking stop, continuing execution" "spec=$SPEC_NAME" "task=$((TASK_INDEX+1))/$TOTAL_TASKS" "iter=$GLOBAL_ITERATION" "parallel=$IS_PARALLEL" "recovery=$RECOVERY_MODE" "dur=${ELAPSED}ms" "decision=block"

    jq -n \
      --arg reason "$REASON" \
      --arg msg "$SYSTEM_MSG" \
      '{
        "decision": "block",
        "reason": $reason,
        "systemMessage": $msg
      }'
fi

# Cleanup orphaned temp progress files (from interrupted parallel batches)
# Only remove files older than 60 minutes to avoid race conditions with active executors
find "$CWD/$SPEC_PATH" -name ".progress-task-*.md" -mmin +60 -delete 2>/dev/null || true

# Note: .progress.md and .curdx-state.json are preserved for loop continuation
# Use /curdx:cancel to explicitly stop execution and cleanup state

exit 0
