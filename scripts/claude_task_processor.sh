#!/bin/bash
# Compatibility entry point for legacy cron installations.
#
# IMPORTANT: this script no longer invokes Claude, ChatGPT, or any consumer
# session. Existing cron entries can safely remain while the persistent
# autonomous supervisor becomes the sole task executor.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec /usr/bin/python3 "$REPO_ROOT/tools/autonomy_liveness_supervisor.py" --once
