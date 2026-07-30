from pathlib import Path

path = Path("ai/factory/runtime.py")
text = path.read_text()

bad = "        self.gap_repair_controller = FactoryGapRepairController()\n"

count = text.count(bad)

if count == 0:
    print({
        "status": "NOT_FOUND",
        "reason": "BAD_INSERT_MISSING"
    })
else:
    text = text.replace(bad, "", 1)
    path.write_text(text)

    print({
        "status": "REMOVED",
        "removed": count
    })
