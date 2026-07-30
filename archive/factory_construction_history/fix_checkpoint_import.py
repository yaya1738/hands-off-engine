from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

target = "from ai.factory.checkpoint_executor import FactoryCheckpointExecutor"

# Remove all existing occurrences
text = text.replace(target, "")

lines = text.splitlines()

# Find the import section and insert after the last top-level import
insert_index = 0
for i, line in enumerate(lines):
    if (
        line.startswith("import ")
        or line.startswith("from ")
    ):
        insert_index = i + 1

lines.insert(insert_index, target)

path.write_text("\n".join(lines) + "\n")

print("CHECKPOINT_IMPORT_RELOCATED")
