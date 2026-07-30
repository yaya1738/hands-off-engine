from pathlib import Path

path = Path("ai/factory/runtime.py")
text = path.read_text()

import_line = "from ai.factory.gap_repair_controller import FactoryGapRepairController"

if import_line in text:
    print({
        "status": "SKIPPED",
        "reason": "IMPORT_EXISTS"
    })
    raise SystemExit

print({
    "status": "READY",
    "action": "ADD_IMPORT_AND_RUNTIME_REFERENCE"
})
