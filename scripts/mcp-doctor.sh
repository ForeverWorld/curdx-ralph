#!/usr/bin/env bash
# MCP doctor for CURDX: detect required MCP servers and optionally install missing ones.

set -euo pipefail

SCRIPT_NAME="$(basename "$0")"
INSTALL_MISSING=false
SCOPE="user"
CONTEXT7_TRANSPORT="stdio"
declare -a REQUIRED_SERVERS=("context7" "chrome-devtools")

usage() {
    cat <<'EOF'
Usage:
  bash scripts/mcp-doctor.sh [options]

Options:
  --install-missing           Install missing known servers (context7, chrome-devtools)
  --scope <local|user|project>
                              Scope passed to `claude mcp add` when installing
  --required <a,b,c>          Comma-separated required server names
                              (default: context7,chrome-devtools)
  --context7-transport <stdio|http>
                              Transport used when auto-installing context7 (default: stdio)
  -h, --help                  Show this help

Environment:
  CONTEXT7_API_KEY            Optional. Used during context7 installation.
                              For stdio transport, the key is passed via environment.
                              For http transport, the key is passed as an MCP header.
EOF
}

die() {
    echo "[$SCRIPT_NAME] ERROR: $*" >&2
    exit 1
}

log() {
    echo "[$SCRIPT_NAME] $*"
}

normalize_required() {
    local csv="$1"
    local item trimmed
    REQUIRED_SERVERS=()
    IFS=',' read -r -a items <<< "$csv"
    for item in "${items[@]}"; do
        trimmed="$(echo "$item" | xargs)"
        [ -n "$trimmed" ] && REQUIRED_SERVERS+=("$trimmed")
    done
    [ "${#REQUIRED_SERVERS[@]}" -gt 0 ] || die "--required resolved to an empty list"
}

while [ $# -gt 0 ]; do
    case "$1" in
        --install-missing)
            INSTALL_MISSING=true
            shift
            ;;
        --scope)
            [ $# -ge 2 ] || die "--scope requires a value"
            SCOPE="$2"
            shift 2
            ;;
        --required)
            [ $# -ge 2 ] || die "--required requires a value"
            normalize_required "$2"
            shift 2
            ;;
        --context7-transport)
            [ $# -ge 2 ] || die "--context7-transport requires a value"
            CONTEXT7_TRANSPORT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "unknown option: $1"
            ;;
    esac
done

case "$SCOPE" in
    local|user|project) ;;
    *) die "invalid --scope value: $SCOPE" ;;
esac

case "$CONTEXT7_TRANSPORT" in
    stdio|http) ;;
    *) die "invalid --context7-transport value: $CONTEXT7_TRANSPORT" ;;
esac

if ! command -v claude >/dev/null 2>&1; then
    die "claude CLI not found in PATH"
fi

list_output="$(claude mcp list 2>&1 || true)"
if ! grep -q "Checking MCP server health" <<< "$list_output"; then
    echo "$list_output" >&2
    die "failed to run 'claude mcp list'"
fi

installed_names=""
while IFS= read -r line; do
    # Example: context7: npx -y @upstash/context7-mcp - ✓ Connected
    if [[ "$line" =~ ^([A-Za-z0-9_.-]+): ]]; then
        installed_names+="${BASH_REMATCH[1]}"$'\n'
    fi
done <<< "$list_output"

log "Required MCP servers: ${REQUIRED_SERVERS[*]}"
if [ -z "$installed_names" ]; then
    log "Configured MCP servers: (none)"
else
    installed_inline="$(echo "$installed_names" | tr '\n' ' ' | xargs)"
    log "Configured MCP servers: $installed_inline"
fi

is_installed() {
    local needle="$1"
    grep -Fxq "$needle" <<< "$installed_names"
}

declare -a MISSING=()
for server in "${REQUIRED_SERVERS[@]}"; do
    if is_installed "$server"; then
        log "OK: $server"
    else
        log "MISSING: $server"
        MISSING+=("$server")
    fi
done

install_context7() {
    log "Installing context7 (scope=$SCOPE, transport=$CONTEXT7_TRANSPORT)"
    if [ "$CONTEXT7_TRANSPORT" = "http" ]; then
        if [ -n "${CONTEXT7_API_KEY:-}" ]; then
            claude mcp add --scope "$SCOPE" --transport http \
                --header "CONTEXT7_API_KEY: ${CONTEXT7_API_KEY}" \
                context7 https://mcp.context7.com/mcp
        else
            claude mcp add --scope "$SCOPE" --transport http \
                context7 https://mcp.context7.com/mcp
        fi
        return 0
    fi

    if ! command -v npx >/dev/null 2>&1; then
        die "npx is required for stdio install (install Node.js 18+), or use --context7-transport http"
    fi

    if [ -n "${CONTEXT7_API_KEY:-}" ]; then
        CONTEXT7_API_KEY="${CONTEXT7_API_KEY}" claude mcp add --scope "$SCOPE" \
            context7 -- npx -y @upstash/context7-mcp
    else
        claude mcp add --scope "$SCOPE" context7 -- npx -y @upstash/context7-mcp
    fi
}

install_chrome_devtools() {
    log "Installing chrome-devtools (scope=$SCOPE)"
    if ! command -v npx >/dev/null 2>&1; then
        die "npx is required for chrome-devtools install (install Node.js 20+)"
    fi
    claude mcp add --scope "$SCOPE" chrome-devtools -- npx -y chrome-devtools-mcp@latest
}

if [ "${#MISSING[@]}" -eq 0 ]; then
    log "All required MCP servers are available."
    exit 0
fi

if [ "$INSTALL_MISSING" != "true" ]; then
    log "Missing required MCP servers. Re-run with --install-missing to auto-install known servers."
    exit 1
fi

for server in "${MISSING[@]}"; do
    case "$server" in
        context7)
            install_context7
            ;;
        chrome-devtools)
            install_chrome_devtools
            ;;
        *)
            die "auto-install is not implemented for server: $server"
            ;;
    esac
done

post_install_output="$(claude mcp list 2>&1 || true)"
for server in "${MISSING[@]}"; do
    if ! grep -qE "^${server}:" <<< "$post_install_output"; then
        echo "$post_install_output" >&2
        die "post-install verification failed; ${server} not listed"
    fi
done

log "Installation complete. Missing servers are now configured."
exit 0
