#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"

ssh "$REMOTE" "/usr/bin/python3 /usr/local/bin/ho_snapshot.py"
