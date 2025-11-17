#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
. "$HOME/hands-off/state/do.env"
api() {
  local method="$1"; shift
  local path="$1"; shift
  curl -sS -X "$method" "https://api.digitalocean.com/v2${path}" \
    -H "Authorization: Bearer $DO_TOKEN" \
    -H "Content-Type: application/json" "$@"
}
