from pathlib import Path

path = Path("ai/factory/runtime.py")

target = "from ai.factory.checkpoint_executor import FactoryCheckpointExecutor"

text = path.read_text()

# Remove misplaced copies
lines = [
    line
    for line in text.splitlines()
    if line.strip() != target
]

# Find first class/function definition after imports
insert_at = None

for i, line in enumerate(lines):
    if line.startswith("class ") or line.startswith("def "):
        insert_at = i
        break

if insert_at is None:
    raise SystemExit("Could not find insertion point")

lines.insert(insert_at, target)

path.write_text("\n".join(lines) + "\n")

print("SAFE_CHECKPOINT_IMPORT_REPAIRED")
