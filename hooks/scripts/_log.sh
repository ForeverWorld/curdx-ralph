#!/usr/bin/env bash
# Shared logging for curdx shell hooks.
# Source this file: source "$SCRIPT_DIR/_log.sh"
#
# Usage: curdx_log <hook_name> <event> <level> <message> [key=value ...]
# Example: curdx_log "stop-watcher" "Stop" "INFO" "blocking stop" "spec=my-spec" "task=3/10"

_CURDX_LOG_DIR="$HOME/.curdx/logs"
_CURDX_LOG_FILE="$_CURDX_LOG_DIR/hooks.log"
_CURDX_LOG_JSONL_FILE="$_CURDX_LOG_DIR/hooks.jsonl"
_CURDX_LOG_MAX_BYTES=5242880  # 5MB
_CURDX_LOG_MIN_LEVEL="${CURDX_HOOK_LOG_LEVEL:-DEBUG}"
_CURDX_LOG_SPLIT="${CURDX_HOOK_LOG_SPLIT:-1}"
_CURDX_LOG_JSONL="${CURDX_HOOK_LOG_JSONL:-1}"
_CURDX_LOG_SESSION_SPLIT="${CURDX_HOOK_LOG_SESSION_SPLIT:-1}"

_curdx_normalize_level() {
    local level
    level=$(printf "%s" "$1" | tr '[:lower:]' '[:upper:]')
    case "$level" in
        WARNING) echo "WARN" ;;
        DEBUG|INFO|WARN|ERROR) echo "$level" ;;
        *) echo "INFO" ;;
    esac
}

_curdx_level_value() {
    case "$(_curdx_normalize_level "$1")" in
        DEBUG) echo 10 ;;
        INFO) echo 20 ;;
        WARN) echo 30 ;;
        ERROR) echo 40 ;;
        *) echo 20 ;;
    esac
}

_curdx_should_log_level() {
    local level="$1"
    local current min
    current=$(_curdx_level_value "$level")
    min=$(_curdx_level_value "$_CURDX_LOG_MIN_LEVEL")
    [ "$current" -ge "$min" ]
}

_curdx_sanitize_component() {
    local value="$1"
    local fallback="${2:-unknown}"
    value=$(printf "%s" "$value" | tr -cs 'A-Za-z0-9_.-' '_')
    value=$(printf "%s" "$value" | sed -E 's/^[_\.]+//; s/[_\.]+$//')
    if [ -z "$value" ]; then
        value="$fallback"
    fi
    printf "%s" "$value"
}

_curdx_log_rotate_if_needed() {
    local log_file="$1"
    [ -f "$log_file" ] || return 0
    local size
    if [[ "$OSTYPE" == "darwin"* ]]; then
        size=$(stat -f%z "$log_file" 2>/dev/null || echo "0")
    else
        size=$(stat -c%s "$log_file" 2>/dev/null || echo "0")
    fi
    if [ "$size" -gt "$_CURDX_LOG_MAX_BYTES" ] 2>/dev/null; then
        mv "$log_file" "${log_file}.1" 2>/dev/null || true
    fi
}

_curdx_write_log_line() {
    local log_file="$1"
    local line="$2"
    local log_dir
    log_dir=$(dirname "$log_file")
    mkdir -p "$log_dir" 2>/dev/null || return 0
    _curdx_log_rotate_if_needed "$log_file"
    printf "%s\n" "$line" >> "$log_file" 2>/dev/null || true
}

_curdx_session_id() {
    local sid="${CURDX_SESSION_ID:-}"
    if [ -z "$sid" ]; then
        sid="${CLAUDE_SESSION_ID:-}"
    fi
    if [ -z "$sid" ]; then
        sid="${ANTHROPIC_SESSION_ID:-}"
    fi
    if [ -z "$sid" ]; then
        sid="default"
    fi
    printf "%s" "$sid"
}

_curdx_split_enabled() {
    case "$(printf "%s" "$_CURDX_LOG_SPLIT" | tr '[:upper:]' '[:lower:]')" in
        0|false|no|off) return 1 ;;
        *) return 0 ;;
    esac
}

_curdx_jsonl_enabled() {
    case "$(printf "%s" "$_CURDX_LOG_JSONL" | tr '[:upper:]' '[:lower:]')" in
        0|false|no|off) return 1 ;;
        *) return 0 ;;
    esac
}

_curdx_session_split_enabled() {
    case "$(printf "%s" "$_CURDX_LOG_SESSION_SPLIT" | tr '[:upper:]' '[:lower:]')" in
        0|false|no|off) return 1 ;;
        *) return 0 ;;
    esac
}

_curdx_json_escape() {
    local s="$1"
    s=${s//\\/\\\\}
    s=${s//\"/\\\"}
    s=${s//$'\n'/\\n}
    s=${s//$'\r'/\\r}
    s=${s//$'\t'/\\t}
    printf "%s" "$s"
}

_curdx_parse_duration_ms() {
    local value="$1"
    case "$value" in
        *ms) value="${value%ms}" ;;
    esac
    if [[ "$value" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
        printf "%s" "$value"
    fi
}

curdx_log() {
    # Check if logging is disabled
    [ "${CURDX_HOOK_LOG:-1}" = "0" ] && return 0

    local hook_name="$1" event="$2" level="$3" message="$4"
    shift 4
    level=$(_curdx_normalize_level "$level")
    _curdx_should_log_level "$level" || return 0

    # Ensure log dir exists
    mkdir -p "$_CURDX_LOG_DIR" 2>/dev/null || return 0

    # Build timestamp
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S.%3N' 2>/dev/null || true)
    # BSD date may print literal 'N' even with exit 0; detect and fallback.
    case "$ts" in
        ""|*N*) ts=$(date '+%Y-%m-%d %H:%M:%S.000') ;;
    esac
    if [ -z "$ts" ]; then
        ts=$(date '+%Y-%m-%d %H:%M:%S.000')
    fi

    local session pid
    session=$(_curdx_session_id)
    pid=$$

    local safe_hook
    safe_hook=$(_curdx_sanitize_component "$hook_name" "unknown")

    # Build extra key=value pairs and parse structured fields
    local extra=""
    local extra_json=""
    local tool=""
    local file=""
    local decision=""
    local duration_ms=""
    local kv key val key_safe dur_candidate
    for kv in "$@"; do
        extra="$extra $kv"
        key="${kv%%=*}"
        if [ "$key" = "$kv" ]; then
            continue
        fi
        val="${kv#*=}"
        key_safe=$(_curdx_sanitize_component "$key" "")
        if [ -z "$key_safe" ]; then
            continue
        fi
        if [ -n "$extra_json" ]; then
            extra_json="$extra_json,"
        fi
        extra_json="$extra_json\"$(_curdx_json_escape "$key_safe")\":\"$(_curdx_json_escape "$val")\""

        case "$key_safe" in
            tool)
                [ -z "$tool" ] && tool="$val"
                ;;
            file)
                [ -z "$file" ] && file="$val"
                ;;
            decision)
                [ -z "$decision" ] && decision="$val"
                ;;
            dur|duration|duration_ms)
                if [ -z "$duration_ms" ]; then
                    dur_candidate=$(_curdx_parse_duration_ms "$val")
                    if [ -n "$dur_candidate" ]; then
                        duration_ms="$dur_candidate"
                    fi
                fi
                ;;
        esac
    done

    local line
    line=$(printf "[%s] [%s] [%s] [%s] session=%s pid=%s%s | %s" \
        "$ts" "$level" "$hook_name" "$event" "$session" "$pid" "$extra" "$message")

    _curdx_write_log_line "$_CURDX_LOG_FILE" "$line"

    if _curdx_split_enabled; then
        local hook_file
        hook_file="$_CURDX_LOG_DIR/hooks.${safe_hook}.log"
        _curdx_write_log_line "$hook_file" "$line"
    fi

    if _curdx_session_split_enabled; then
        local safe_session session_dir
        safe_session=$(_curdx_sanitize_component "$session" "default")
        session_dir="$_CURDX_LOG_DIR/sessions/$safe_session"
        _curdx_write_log_line "$session_dir/hooks.log" "$line"
        if _curdx_split_enabled; then
            _curdx_write_log_line "$session_dir/hooks.${safe_hook}.log" "$line"
        fi
    fi

    if _curdx_jsonl_enabled; then
        local epoch_seconds ts_unix_ms json_line
        epoch_seconds=$(date +%s 2>/dev/null || echo "0")
        ts_unix_ms=$((epoch_seconds * 1000))
        json_line="{\"ts\":\"$(_curdx_json_escape "$ts")\",\"ts_unix_ms\":$ts_unix_ms,\"level\":\"$(_curdx_json_escape "$level")\",\"hook\":\"$(_curdx_json_escape "$hook_name")\",\"event\":\"$(_curdx_json_escape "$event")\",\"session\":\"$(_curdx_json_escape "$session")\",\"pid\":$pid,\"message\":\"$(_curdx_json_escape "$message")\""

        if [ -n "$tool" ]; then
            json_line="$json_line,\"tool\":\"$(_curdx_json_escape "$tool")\""
        fi
        if [ -n "$file" ]; then
            json_line="$json_line,\"file\":\"$(_curdx_json_escape "$file")\""
        fi
        if [ -n "$decision" ]; then
            json_line="$json_line,\"decision\":\"$(_curdx_json_escape "$decision")\""
        fi
        if [ -n "$duration_ms" ]; then
            json_line="$json_line,\"duration_ms\":$duration_ms"
        fi
        if [ -n "$extra_json" ]; then
            json_line="$json_line,\"extra\":{$extra_json}"
        fi
        json_line="$json_line}"

        _curdx_write_log_line "$_CURDX_LOG_JSONL_FILE" "$json_line"
        if _curdx_split_enabled; then
            _curdx_write_log_line "$_CURDX_LOG_DIR/hooks.${safe_hook}.jsonl" "$json_line"
        fi
        if _curdx_session_split_enabled; then
            local safe_session_json session_dir_json
            safe_session_json=$(_curdx_sanitize_component "$session" "default")
            session_dir_json="$_CURDX_LOG_DIR/sessions/$safe_session_json"
            _curdx_write_log_line "$session_dir_json/hooks.jsonl" "$json_line"
            if _curdx_split_enabled; then
                _curdx_write_log_line "$session_dir_json/hooks.${safe_hook}.jsonl" "$json_line"
            fi
        fi
    fi
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
