#!/data/data/com.termux/files/usr/bin/bash

echo "=== HO QUICK CHECK ==="

STATUS=$(python -m autonomous.integrations.supervisor 2>/dev/null)

python - <<'PY'
import json, subprocess

try:
    d=json.loads(subprocess.check_output(
        ["python","-m","autonomous.integrations.supervisor"],
        text=True
    ))

    print("")
    print("SYSTEM:", "OK" if d.get("healthy") else "ISSUE")

    for name, info in d.get("integrations", {}).items():
        print("CONNECTOR:", name)
        print("  Connected:", "YES" if info.get("connected") else "NO")
        print("  Token:", "YES" if info.get("token_present") else "NO")

    actions=d.get("credential_sync",{}).get("actions",[])
    if actions:
        print("NEXT ACTION:")
        for a in actions:
            print(" ", a.get("identity"), "->", a.get("action"))
    else:
        print("NEXT ACTION: NONE")

except Exception as e:
    print("SYSTEM: ERROR")
    print("ERROR TYPE:", type(e).__name__)

PY

echo
echo "GIT:"
git status --short | head -5 || true

echo "=== END ==="
