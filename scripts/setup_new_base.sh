#!/usr/bin/env bash
set -euo pipefail

# Deprecated compatibility wrapper. Run this on an already provisioned Linux
# host; it delegates to the provider-neutral bootstrap and never asks for or
# copies credentials.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <ssh-host> [remote-repo-path]" >&2
  exit 2
fi

exec "$SCRIPT_DIR/bootstrap_host.sh" "$@"
