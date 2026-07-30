from pathlib import Path

path = Path("ai/factory/runtime.py")
text = path.read_text()

if "FactoryGapRepairController" in text:
    print({
        "status": "SKIPPED",
        "reason": "CONTROLLER_ALREADY_WIRED"
    })
    raise SystemExit

print({
    "status": "READY",
    "target": str(path),
    "next_action": "ADD_FACTORY_REPAIR_GATE"
})
