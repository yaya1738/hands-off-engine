#!/usr/bin/env bash
set -euo pipefail

# Deprecated compatibility wrapper.
# Cloud-account signup/provisioning happens outside the repository. This script
# deliberately does not collect, copy, or print credentials and never starts
# financial execution.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -lt 1 ]]; then
  cat >&2 <<'EOF'
Usage: scripts/DEPLOY_NEW_BASE.sh <ssh-host> [remote-repo-path]

Provision the Linux host through your cloud provider first, configure SSH, then
use this provider-neutral bootstrap. It does not create cloud accounts, copy
.env files, collect trading credentials, or enable live financial execution.
EOF
  exit 2
fi

exec "$SCRIPT_DIR/bootstrap_host.sh" "$@"
