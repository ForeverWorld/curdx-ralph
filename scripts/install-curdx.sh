#!/usr/bin/env bash
# CURDX one-click installer with preflight checks.

set -euo pipefail

SCOPE="user"
WITH_MCP=false
SKIP_AUTH=false
MIN_CLAUDE_VERSION="1.0.33"
MARKETPLACE_SOURCE="ForeverWorld/curdx-ralph"
MARKETPLACE_NAME="curdx-marketplace"
PLUGIN_REF="curdx@curdx-marketplace"

usage() {
    cat <<'EOF'
Usage:
  bash scripts/install-curdx.sh [options]

Options:
  --scope <user|project|local>   Installation scope for plugin/marketplace (default: user)
  --with-mcp                     Also run MCP installer (`scripts/mcp-doctor.sh --install-missing`)
  --skip-auth-check              Skip `claude auth status` check
  -h, --help                     Show help

What this script does:
1. Checks `claude` CLI exists and version >= 1.0.33
2. Checks Claude auth status (unless --skip-auth-check)
3. Adds CURDX marketplace if missing
4. Installs `curdx@curdx-marketplace` if not already installed
5. Enables installed CURDX plugin
6. Plugin-level MCP defaults come from `.claude-plugin/.mcp.json`
7. Optionally installs user/project MCP servers for explicit local entries
EOF
}

log() {
    echo "[install-curdx] $*"
}

die() {
    echo "[install-curdx] ERROR: $*" >&2
    exit 1
}

version_ge() {
    # returns 0 if $1 >= $2 (semver-like x.y.z)
    local a="$1" b="$2"
    local IFS=.
    local -a av=($a) bv=($b)
    local i ai bi
    for i in 0 1 2; do
        ai="${av[$i]:-0}"
        bi="${bv[$i]:-0}"
        if (( ai > bi )); then
            return 0
        fi
        if (( ai < bi )); then
            return 1
        fi
    done
    return 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --scope)
            [[ $# -ge 2 ]] || die "--scope requires a value"
            SCOPE="$2"
            shift 2
            ;;
        --with-mcp)
            WITH_MCP=true
            shift
            ;;
        --skip-auth-check)
            SKIP_AUTH=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
done

case "$SCOPE" in
    user|project|local) ;;
    *) die "Invalid --scope: $SCOPE (use user|project|local)" ;;
esac

command -v claude >/dev/null 2>&1 || die "claude CLI not found in PATH"

CLAUDE_VERSION_RAW="$(claude --version | awk '{print $1}')"
if [[ ! "$CLAUDE_VERSION_RAW" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    die "Unable to parse Claude version from: $(claude --version)"
fi
if ! version_ge "$CLAUDE_VERSION_RAW" "$MIN_CLAUDE_VERSION"; then
    die "Claude version $CLAUDE_VERSION_RAW is too old (need >= $MIN_CLAUDE_VERSION)"
fi
log "Claude version check passed: $CLAUDE_VERSION_RAW"

if [[ "$SKIP_AUTH" != "true" ]]; then
    AUTH_STATUS="$(claude auth status 2>/dev/null || true)"
    if ! grep -q '"loggedIn":[[:space:]]*true' <<< "$AUTH_STATUS"; then
        die "Not logged in. Run: claude auth login"
    fi
    log "Auth check passed"
fi

MARKETPLACE_JSON="$(claude plugin marketplace list --json 2>/dev/null || echo '[]')"
if grep -q "\"name\":[[:space:]]*\"$MARKETPLACE_NAME\"" <<< "$MARKETPLACE_JSON"; then
    log "Marketplace already present: $MARKETPLACE_NAME"
else
    log "Adding marketplace: $MARKETPLACE_SOURCE (scope=$SCOPE)"
    claude plugin marketplace add "$MARKETPLACE_SOURCE" --scope "$SCOPE"
fi

PLUGINS_JSON="$(claude plugin list --json 2>/dev/null || echo '[]')"
CURDX_ID="$(sed -n 's/.*"id":[[:space:]]*"\(curdx@[^"]*\)".*/\1/p' <<< "$PLUGINS_JSON" | head -1)"

if [[ -z "$CURDX_ID" ]]; then
    log "Installing plugin: $PLUGIN_REF (scope=$SCOPE)"
    claude plugin install "$PLUGIN_REF" --scope "$SCOPE"
    CURDX_ID="$PLUGIN_REF"
else
    log "CURDX already installed as: $CURDX_ID"
fi

log "Enabling plugin: $CURDX_ID"
claude plugin enable "$CURDX_ID"

if [[ "$WITH_MCP" == "true" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [[ -x "$SCRIPT_DIR/mcp-doctor.sh" || -f "$SCRIPT_DIR/mcp-doctor.sh" ]]; then
        log "Installing required MCP servers"
        bash "$SCRIPT_DIR/mcp-doctor.sh" --install-missing --scope "$SCOPE"
    else
        die "scripts/mcp-doctor.sh not found"
    fi
fi

log "Done. Verify with:"
echo "  claude plugin list --json"
echo "  claude plugin marketplace list --json"
