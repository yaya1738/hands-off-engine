from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

manager_import = "from ai.factory.checkpoint_manager import FactoryCheckpointManager"

if manager_import not in text:
    lines = text.splitlines()

    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            insert_at = i + 1

    lines.insert(insert_at, manager_import)
    text = "\n".join(lines) + "\n"

init_line = "        self.checkpoint_manager = FactoryCheckpointManager("

if init_line not in text:
    anchor = "        self.checkpoint_executor = FactoryCheckpointExecutor(\n            audit=self.improvement_audit,\n        )"

    if anchor not in text:
        raise SystemExit("checkpoint executor initialization anchor not found")

    text = text.replace(
        anchor,
        anchor + "\n        self.checkpoint_manager = FactoryCheckpointManager()",
    )

p.write_text(text)

print("CHECKPOINT_MANAGER_WIRED")
