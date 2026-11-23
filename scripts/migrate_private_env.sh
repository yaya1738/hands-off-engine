#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${HANDS_OFF_REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
PRIVATE_ROOT="${HANDS_OFF_PRIVATE_DIR:-$HOME/.config/hands-off-engine}"

mkdir -p "$PRIVATE_ROOT/security" "$PRIVATE_ROOT/termux" "$PRIVATE_ROOT/state" "$PRIVATE_ROOT/profile" "$PRIVATE_ROOT/finance"
chmod 700 "$PRIVATE_ROOT" "$PRIVATE_ROOT/security" "$PRIVATE_ROOT/termux" "$PRIVATE_ROOT/state" "$PRIVATE_ROOT/profile" "$PRIVATE_ROOT/finance" 2>/dev/null || true

copy_private() {
  local source="$1"
  local destination="$2"
  if [[ -f "$source" && ! -f "$destination" ]]; then
    cp -p "$source" "$destination"
    chmod 600 "$destination"
    echo "Copied $(basename "$source") to private storage."
  elif [[ -f "$destination" ]]; then
    echo "Private copy already exists for $(basename "$source"); left unchanged."
  fi
}

# Run this from the old checkout before switching to a branch that removes these files.
copy_private "$REPO_ROOT/security/yair_identity_profile.json" "$PRIVATE_ROOT/security/owner_identity_profile.json"
copy_private "$REPO_ROOT/security/yair_human_identity.json" "$PRIVATE_ROOT/security/owner_human_identity.json"
copy_private "$REPO_ROOT/termux-hands-off/state/auto_sources.env" "$PRIVATE_ROOT/termux/auto_sources.env"
copy_private "$REPO_ROOT/state/UNIFIED_SYSTEM_STATE.json" "$PRIVATE_ROOT/state/legacy_UNIFIED_SYSTEM_STATE.json"
copy_private "$REPO_ROOT/state/unified_system_state.json" "$PRIVATE_ROOT/state/legacy_unified_system_state.json"
copy_private "$REPO_ROOT/docs/claude/USER_PROFILE.md" "$PRIVATE_ROOT/profile/legacy_USER_PROFILE.md"
copy_private "$REPO_ROOT/finance/yair_finance_hub.json" "$PRIVATE_ROOT/finance/finance_hub.json"
copy_private "$REPO_ROOT/finance/dollar_access.json" "$PRIVATE_ROOT/finance/dollar_access.json"
copy_private "$REPO_ROOT/finance/partner_terms.json" "$PRIVATE_ROOT/finance/partner_terms.json"
copy_private "$REPO_ROOT/finance/cost_decisions.jsonl" "$PRIVATE_ROOT/finance/cost_decisions.jsonl"
copy_private "$REPO_ROOT/.claude/instructions.md" "$PRIVATE_ROOT/profile/legacy_instructions.md"

echo "Migration complete. Source files were not deleted."
echo "Treat all copied financial snapshots as historical/unverified until refreshed from authoritative sources."
