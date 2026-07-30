from pathlib import Path

path = Path("ai/factory/runtime.py")
text = path.read_text()

if "self.gap_repair_controller" in text:
    print({
        "status": "SKIPPED",
        "reason": "RUNTIME_REFERENCE_EXISTS"
    })
    raise SystemExit

if "self.improvement_orchestrator" not in text:
    print({
        "status": "BLOCKED",
        "reason": "IMPROVEMENT_ORCHESTRATOR_NOT_FOUND"
    })
    raise SystemExit

print({
    "status": "READY",
    "action": "INSERT_CONTROLLER_INITIALIZATION"
})
