from pathlib import Path

root = Path("ai/factory")

targets = [
    "create_task",
    "request(",
    "execute(",
    "execute_approved_improvement",
    "process_approved_improvement",
    "register_artifact",
]

print("IMPROVEMENT ENTRYPOINT MAP")
print("=" * 35)

for file in root.glob("*.py"):
    if "__pycache__" in str(file):
        continue

    text = file.read_text(errors="ignore")

    hits = []

    for target in targets:
        if target in text:
            hits.append(target)

    if hits:
        print(file.name, "=>", hits)

print("DONE")
