from pathlib import Path

path = Path("ai/factory/runtime.py")
text = path.read_text()

import_line = "from ai.factory.gap_repair_controller import FactoryGapRepairController"

if import_line not in text:
    text = import_line + "\n" + text

if "self.gap_repair_controller" in text:
    print({
        "status": "SKIPPED",
        "reason": "CONTROLLER_EXISTS"
    })
    path.write_text(text)
    raise SystemExit

marker = "self.improvement_orchestrator"

idx = text.find(marker)

if idx == -1:
    print({
        "status": "BLOCKED",
        "reason": "IMPROVEMENT_COMPONENT_NOT_FOUND"
    })
    raise SystemExit

line_end = text.find("\n", idx)

insert = """
        self.gap_repair_controller = FactoryGapRepairController()
"""

text = (
    text[:line_end + 1]
    + insert
    + text[line_end + 1:]
)

path.write_text(text)

print({
    "status": "PATCHED",
    "next_action": "VERIFY_RUNTIME_LOAD"
})
