from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
CREDS = ROOT / "credentials.json"
TOKEN = ROOT / "data" / "secrets" / "gmail_token.json"

print("=== Gmail OAuth Readiness ===")

if CREDS.exists():
    try:
        data = json.loads(CREDS.read_text())
        if "installed" in data or "web" in data:
            print("credentials.json: OK")
        else:
            print("credentials.json: FOUND but unexpected format")
    except Exception as e:
        print("credentials.json: INVALID", e)
else:
    print("credentials.json: MISSING")
    print(f"Place Google OAuth desktop credentials here:")
    print(CREDS)

if TOKEN.exists():
    print("gmail token: EXISTS")
else:
    print("gmail token: NOT CONNECTED")

print("=============================")
