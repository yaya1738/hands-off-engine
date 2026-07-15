#!/data/data/com.termux/files/usr/bin/bash

set -e

ROOT="$HOME/hands-off-engine-forensic-jan9"

cd "$ROOT"

echo "=== Hands-Off Gmail Connect ==="

echo "[1/4] Checking Python dependencies..."

python - <<'PY'
import cryptography
import google_auth_oauthlib

print("cryptography:", cryptography.__version__)
print("google oauth: OK")
PY

echo "[2/4] Checking credentials..."

if [ ! -f "$ROOT/credentials.json" ]; then
    echo "Missing:"
    echo "$ROOT/credentials.json"
    echo ""
    echo "Add Google OAuth Desktop credentials first."
    exit 1
fi

echo "credentials.json found"

echo "[3/4] Starting OAuth flow..."

python -m autonomous.integrations.providers.gmail_oauth_setup

echo "[4/4] Checking connection..."

python scripts/gmail_check.py

echo "=== Gmail Connect Complete ==="
