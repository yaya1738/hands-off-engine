from pathlib import Path
import ast

targets = [
    Path("ai/factory/improvement_orchestrator.py"),
    Path("ai/factory/runtime.py"),
    Path("ai/factory/development_pipeline.py"),
]

results = []

for path in targets:
    text = path.read_text()

    if "development_pipeline" in text or "process(" in text:
        lines = text.splitlines()

        for i, line in enumerate(lines, 1):
            if (
                "development_pipeline" in line
                or "process(" in line
                or "queue" in line.lower()
            ):
                results.append({
                    "file": str(path),
                    "line": i,
                    "text": line.strip()
                })

print({
    "status": "ANALYZED",
    "references": results,
    "next_action": "MAP_FINAL_HANDOFF"
})
