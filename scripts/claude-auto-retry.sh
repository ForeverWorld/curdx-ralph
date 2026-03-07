#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  scripts/claude-auto-retry.sh [options]

Options:
  --prompt <text>            Prompt to send to Claude (default: /curdx:implement)
  --model <name>             Optional primary model (passed to --model)
  --fallback-model <name>    Fallback model for --print mode (default: sonnet)
  --no-fallback              Disable --fallback-model
  --min-sleep <sec>          Minimum backoff seconds (default: 5)
  --max-sleep <sec>          Maximum backoff seconds (default: 300)
  --success-sleep <sec>      Sleep after successful run in loop mode (default: 3)
  --jitter-max <sec>         Max random jitter seconds added to backoff (default: 3)
  --max-runs <n>             Stop after n runs, 0 means infinite (default: 0)
  --stop-on-success          Exit after first successful run
  --log-dir <path>           Log directory (default: ./.claude-loop)
  --preset <name>            Load preset pattern file from scripts/retry-presets/<name>.patterns
  --pattern-file <path>      Load custom pattern file (repeatable)
  --extra-transient <regex>  Extra retriable error regex (append to defaults)
  --extra-non-retriable <r>  Extra non-retriable error regex (append to defaults)
  -h, --help                 Show this help

Examples:
  scripts/claude-auto-retry.sh
  scripts/claude-auto-retry.sh --stop-on-success --prompt "/curdx:implement"
  scripts/claude-auto-retry.sh --model sonnet --fallback-model haiku
  scripts/claude-auto-retry.sh --preset relay-common
  scripts/claude-auto-retry.sh --pattern-file .claude/retry/my-relay.patterns
  scripts/claude-auto-retry.sh --extra-transient "upstream connect error|provider overloaded"
EOF
}

require_integer() {
    local value="$1"
    local name="$2"
    if ! [[ "$value" =~ ^[0-9]+$ ]]; then
        echo "[retry-loop] invalid ${name}: ${value} (must be non-negative integer)" >&2
        exit 2
    fi
}

trim_line() {
    local s="${1:-}"
    s="${s#"${s%%[![:space:]]*}"}"
    s="${s%"${s##*[![:space:]]}"}"
    printf "%s" "$s"
}

append_regex_union() {
    local current="$1"
    local add="$2"
    if [[ -z "$add" ]]; then
        printf "%s" "$current"
        return
    fi
    if [[ -z "$current" ]]; then
        printf "%s" "$add"
        return
    fi
    printf "%s|%s" "$current" "$add"
}

load_pattern_file() {
    local file_path="$1"
    local line raw key value

    if [[ ! -f "$file_path" ]]; then
        echo "[retry-loop] pattern file not found: $file_path" >&2
        exit 2
    fi

    while IFS= read -r raw || [[ -n "$raw" ]]; do
        line="$(trim_line "$raw")"
        [[ -z "$line" ]] && continue
        [[ "$line" =~ ^# ]] && continue

        if [[ "$line" == *:* ]]; then
            key="$(trim_line "${line%%:*}")"
            value="$(trim_line "${line#*:}")"
            case "$key" in
                transient)
                    EXTRA_TRANSIENT_REGEX="$(append_regex_union "$EXTRA_TRANSIENT_REGEX" "$value")"
                    ;;
                non_retriable|non-retriable|permanent)
                    EXTRA_NON_RETRIABLE_REGEX="$(append_regex_union "$EXTRA_NON_RETRIABLE_REGEX" "$value")"
                    ;;
                *)
                    echo "[retry-loop] invalid pattern key '$key' in $file_path" >&2
                    echo "[retry-loop] expected 'transient:' or 'non_retriable:'" >&2
                    exit 2
                    ;;
            esac
        else
            EXTRA_TRANSIENT_REGEX="$(append_regex_union "$EXTRA_TRANSIENT_REGEX" "$line")"
        fi
    done < "$file_path"
}

PROMPT="/curdx:implement"
MODEL=""
FALLBACK_MODEL="sonnet"
USE_FALLBACK=1
MIN_SLEEP=5
MAX_SLEEP=300
SUCCESS_SLEEP=3
JITTER_MAX=3
MAX_RUNS=0
STOP_ON_SUCCESS=0
LOG_DIR="./.claude-loop"
EXTRA_TRANSIENT_REGEX="${CLAUDE_RETRY_EXTRA_TRANSIENT_REGEX:-}"
EXTRA_NON_RETRIABLE_REGEX="${CLAUDE_RETRY_EXTRA_NON_RETRIABLE_REGEX:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRESET_DIR="$SCRIPT_DIR/retry-presets"
declare -a PATTERN_FILES=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prompt)
            PROMPT="${2:-}"
            shift 2
            ;;
        --model)
            MODEL="${2:-}"
            shift 2
            ;;
        --fallback-model)
            FALLBACK_MODEL="${2:-}"
            shift 2
            ;;
        --no-fallback)
            USE_FALLBACK=0
            shift
            ;;
        --min-sleep)
            MIN_SLEEP="${2:-}"
            shift 2
            ;;
        --max-sleep)
            MAX_SLEEP="${2:-}"
            shift 2
            ;;
        --success-sleep)
            SUCCESS_SLEEP="${2:-}"
            shift 2
            ;;
        --jitter-max)
            JITTER_MAX="${2:-}"
            shift 2
            ;;
        --max-runs)
            MAX_RUNS="${2:-}"
            shift 2
            ;;
        --stop-on-success)
            STOP_ON_SUCCESS=1
            shift
            ;;
        --log-dir)
            LOG_DIR="${2:-}"
            shift 2
            ;;
        --preset)
            PATTERN_FILES+=("$PRESET_DIR/${2:-}.patterns")
            shift 2
            ;;
        --pattern-file)
            PATTERN_FILES+=("${2:-}")
            shift 2
            ;;
        --extra-transient)
            EXTRA_TRANSIENT_REGEX="${2:-}"
            shift 2
            ;;
        --extra-non-retriable)
            EXTRA_NON_RETRIABLE_REGEX="${2:-}"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "[retry-loop] unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if ! command -v claude >/dev/null 2>&1; then
    echo "[retry-loop] 'claude' command not found in PATH" >&2
    exit 127
fi

require_integer "$MIN_SLEEP" "min-sleep"
require_integer "$MAX_SLEEP" "max-sleep"
require_integer "$SUCCESS_SLEEP" "success-sleep"
require_integer "$JITTER_MAX" "jitter-max"
require_integer "$MAX_RUNS" "max-runs"

if (( MAX_SLEEP < MIN_SLEEP )); then
    echo "[retry-loop] max-sleep must be >= min-sleep" >&2
    exit 2
fi

for pattern_file in "${PATTERN_FILES[@]-}"; do
    [[ -z "$pattern_file" ]] && continue
    load_pattern_file "$pattern_file"
done

mkdir -p "$LOG_DIR"
RUN_LOG="$LOG_DIR/loop.log"

TRANSIENT_REGEX='relay: 当前模型负载过高|overloaded|server_error|rate[_ -]?limit|429|500|502|503|504|529|connection error|timed out|timeout|request was aborted|socket hang up|ECONN|ENOTFOUND|EAI_AGAIN'
NON_RETRIABLE_REGEX='access denied|invalid user|authentication|api key|auth token|authorization|permission denied|forbidden|401|403|invalid[_ -]?request|unsupported'

if [[ -n "$EXTRA_TRANSIENT_REGEX" ]]; then
    TRANSIENT_REGEX="${TRANSIENT_REGEX}|${EXTRA_TRANSIENT_REGEX}"
fi
if [[ -n "$EXTRA_NON_RETRIABLE_REGEX" ]]; then
    NON_RETRIABLE_REGEX="${NON_RETRIABLE_REGEX}|${EXTRA_NON_RETRIABLE_REGEX}"
fi

backoff="$MIN_SLEEP"
run_index=0

echo "[$(date '+%F %T')] [retry-loop] start prompt='$PROMPT'" | tee -a "$RUN_LOG"

while true; do
    run_index=$((run_index + 1))
    if (( MAX_RUNS > 0 && run_index > MAX_RUNS )); then
        echo "[$(date '+%F %T')] [retry-loop] reached max runs: $MAX_RUNS" | tee -a "$RUN_LOG"
        exit 0
    fi

    tmp_file="$(mktemp "$LOG_DIR/run.${run_index}.XXXXXX")"
    start_ts="$(date '+%F %T')"
    echo "[$start_ts] [retry-loop] run #$run_index begin" | tee -a "$RUN_LOG"

    claude_cmd=(claude -c -p --output-format stream-json)
    if [[ -n "$MODEL" ]]; then
        claude_cmd+=(--model "$MODEL")
    fi
    if (( USE_FALLBACK == 1 )) && [[ -n "$FALLBACK_MODEL" ]]; then
        claude_cmd+=(--fallback-model "$FALLBACK_MODEL")
    fi
    claude_cmd+=("$PROMPT")

    if "${claude_cmd[@]}" 2>&1 | tee "$tmp_file"; then
        run_rc=0
    else
        run_rc=${PIPESTATUS[0]}
    fi
    cat "$tmp_file" >> "$RUN_LOG"

    if (( run_rc == 0 )); then
        echo "[$(date '+%F %T')] [retry-loop] run #$run_index success" | tee -a "$RUN_LOG"
        backoff="$MIN_SLEEP"
        if (( STOP_ON_SUCCESS == 1 )); then
            rm -f "$tmp_file"
            exit 0
        fi
        sleep "$SUCCESS_SLEEP"
        rm -f "$tmp_file"
        continue
    fi

    if rg -qi -- "$NON_RETRIABLE_REGEX" "$tmp_file"; then
        echo "[$(date '+%F %T')] [retry-loop] non-retriable error, stop (code=$run_rc)" | tee -a "$RUN_LOG"
        rm -f "$tmp_file"
        exit "$run_rc"
    fi

    retry_reason="unknown-failure"
    if rg -qi -- "$TRANSIENT_REGEX" "$tmp_file"; then
        retry_reason="transient-failure"
    fi

    jitter=0
    if (( JITTER_MAX > 0 )); then
        jitter=$((RANDOM % (JITTER_MAX + 1)))
    fi
    sleep_for=$((backoff + jitter))

    echo "[$(date '+%F %T')] [retry-loop] run #$run_index failed (code=$run_rc, reason=$retry_reason), retry in ${sleep_for}s" | tee -a "$RUN_LOG"
    sleep "$sleep_for"

    backoff=$((backoff * 2))
    if (( backoff > MAX_SLEEP )); then
        backoff="$MAX_SLEEP"
    fi
    rm -f "$tmp_file"
done
