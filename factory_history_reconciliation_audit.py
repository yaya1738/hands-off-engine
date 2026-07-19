import os
import json
from datetime import datetime, timezone

KEYWORDS = [
    "proposal",
    "executor",
    "approval",
    "approved",
    "verified",
    "handoff",
    "complete",
    "integration",
    "lifecycle",
]

SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
}

results = []

for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

    for file in files:
        path = os.path.join(root, file)

        try:
            if os.path.getsize(path) > 5_000_000:
                continue

            with open(path, "r", errors="ignore") as f:
                lines = f.readlines()

            matches = []

            for i, line in enumerate(lines, 1):
                lower = line.lower()

                for keyword in KEYWORDS:
                    if keyword in lower:
                        matches.append({
                            "line": i,
                            "keyword": keyword,
                            "text": line.strip()[:200]
                        })

            if matches:
                results.append({
                    "file": path,
                    "match_count": len(matches),
                    "matches": matches[:50]
                })

        except Exception:
            pass


report = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "purpose": "factory historical lifecycle reconciliation",
    "keywords": KEYWORDS,
    "artifact_count": len(results),
    "artifacts": results
}

with open("factory_history_reconciliation_audit.json", "w") as f:
    json.dump(report, f, indent=2)

print(json.dumps({
    "status": "complete",
    "output": "factory_history_reconciliation_audit.json",
    "artifacts_found": len(results)
}, indent=2))
