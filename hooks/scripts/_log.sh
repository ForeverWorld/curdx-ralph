#!/usr/bin/env bash
# Shared logging for curdx shell hooks.
# Source this file: source "$SCRIPT_DIR/_log.sh"
#
# Usage: curdx_log <hook_name> <event> <level> <message> [key=value ...]
# Example: curdx_log "stop-watcher" "Stop" "INFO" "blocking stop" "spec=my-spec" "task=3/10"

_CURDX_LOG_DIR="$HOME/.curdx/logs"
_CURDX_LOG_FILE="$_CURDX_LOG_DIR/hooks.log"
_CURDX_LOG_MAX_BYTES=5242880  # 5MB

curdx_log() {
    # Check if logging is disabled
    [ "${CURDX_HOOK_LOG:-1}" = "0" ] && return 0

    local hook_name="$1" event="$2" level="$3" message="$4"
    shift 4

    # Ensure log dir exists
    mkdir -p "$_CURDX_LOG_DIR" 2>/dev/null || return 0

    # Rotate if too large
    if [ -f "$_CURDX_LOG_FILE" ]; then
        local size
        if [[ "$OSTYPE" == "darwin"* ]]; then
            size=$(stat -f%z "$_CURDX_LOG_FILE" 2>/dev/null || echo "0")
        else
            size=$(stat -c%s "$_CURDX_LOG_FILE" 2>/dev/null || echo "0")
        fi
        if [ "$size" -gt "$_CURDX_LOG_MAX_BYTES" ] 2>/dev/null; then
            mv "$_CURDX_LOG_FILE" "${_CURDX_LOG_FILE}.1" 2>/dev/null || true
        fi
    fi

    # Build timestamp
    local ts
    if date '+%Y-%m-%d %H:%M:%S.%3N' >/dev/null 2>&1; then
        ts=$(date '+%Y-%m-%d %H:%M:%S.%3N')
    else
        ts=$(date '+%Y-%m-%d %H:%M:%S.000')
    fi

    # Build extra key=value pairs
    local extra=""
    while [ $# -gt 0 ]; do
        extra="$extra $1"
        shift
    done

    # Write log line
    printf "[%s] [%s] [%s] [%s]%s | %s\n" \
        "$ts" "$level" "$hook_name" "$event" "$extra" "$message" \
        >> "$_CURDX_LOG_FILE" 2>/dev/null || true
}

# Timer helpers for shell hooks
_CURDX_TIMER_START=""

curdx_timer_start() {
    # Use epoch seconds — works across subprocesses unlike monotonic clocks
    _CURDX_TIMER_START=$(date +%s)
}

curdx_timer_elapsed() {
    if [ -z "$_CURDX_TIMER_START" ]; then
        echo "0"
        return
    fi
    local now=$(date +%s)
    echo "$(( (now - _CURDX_TIMER_START) * 1000 ))"
}
