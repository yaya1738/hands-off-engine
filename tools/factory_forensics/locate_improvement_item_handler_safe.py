from pathlib import Path

files = [
    Path("ai/factory/improvement_orchestrator.py"),
    Path("ai/factory"),
]

matches = []

for target in files:
    paths = [target] if target.is_file() else target.rglob("*.py")

    for path in paths:
        try:
            text = path.read_text()

            for i, line in enumerate(text.splitlines(), 1):
                low = line.lower()

                if (
                    "process(" in low
                    or "dequeue(" in low
                    or "queued" in low
                ) and (
                    "execute" in text.lower()
                    or "approve" in text.lower()
                    or "validate" in text.lower()
                    or "audit" in text.lower()
                ):
                    matches.append({
                        "file": str(path),
                        "line": i,
                        "line_text": line.strip()
                    })

        except Exception:
            pass

print({
    "status": "ANALYZED",
    "matches": matches[:20],
    "count": len(matches),
    "next_action": (
        "TRACE_HANDLER"
        if matches
        else "MISSING_HANDOFF"
    )
})
