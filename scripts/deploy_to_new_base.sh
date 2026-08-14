#!/usr/bin/env bash
set -euo pipefail

# Deprecated compatibility wrapper. Use bootstrap_host.sh.
# No credentials are copied or requested and no financial process is started.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <ssh-host> [remote-repo-path]" >&2
  exit 2
fi

exec "$SCRIPT_DIR/bootstrap_host.sh" "$@"
