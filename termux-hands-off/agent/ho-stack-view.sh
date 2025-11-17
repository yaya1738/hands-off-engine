#!/usr/bin/env bash
set -euo pipefail

echo "=== [1] Decision summary (hodec) ==="
hodec || echo "[warn] hodec failed"

echo
echo "=== [2] Execution preview (hoexec) ==="
hoexec || echo "[warn] hoexec failed"

echo
echo "=== [3] Execution plan (hoplan) ==="
hoplan || echo "[warn] hoplan failed"

echo
echo "=== [4] Client DRYRUN payloads (hosim) ==="
hosim || echo "[warn] hosim failed"
