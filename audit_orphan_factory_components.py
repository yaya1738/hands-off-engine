from pathlib import Path
import re

root = Path("ai/factory")

classes = {}

for p in root.glob("*.py"):
    text = p.read_text(errors="ignore")

    for match in re.finditer(r"class\s+(Factory\w+)", text):
        classes[match.group(1)] = p.name

referenced = set()

for p in root.glob("*.py"):
    text = p.read_text(errors="ignore")

    for cls in classes:
        if cls in text and p.name != classes[cls]:
            referenced.add(cls)

print("==== ORPHAN FACTORY COMPONENTS ====")

for cls, file in sorted(classes.items()):
    if cls not in referenced:
        print(f"{cls:40} | {file}")
