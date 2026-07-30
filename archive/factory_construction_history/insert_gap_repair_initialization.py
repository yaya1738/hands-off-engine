from pathlib import Path

path = Path("ai/factory/runtime.py")
text = path.read_text()

if "self.gap_repair_controller" in text:
    print({
        "status": "SKIPPED",
        "reason": "ALREADY_INITIALIZED"
    })
    raise SystemExit

marker = "self.improvement_orchestrator"

if marker not in text:
    print({
        "status": "BLOCKED",
        "reason": "INIT_MARKER_NOT_FOUND"
    })
    raise SystemExit

print({
    "status": "READY",
    "action": "INSERT_AFTER_IMPROVEMENT_COMPONENTS"
})
