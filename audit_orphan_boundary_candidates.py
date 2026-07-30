from pathlib import Path
import re

keywords = [
    "execute",
    "route",
    "decide",
    "approve",
    "create_goal",
    "create_task",
    "improve",
    "update",
    "record",
    "run_cycle",
    "handle",
]

root = Path("ai/factory")

for p in sorted(root.glob("*.py")):
    text = p.read_text(errors="ignore")

    classes = re.findall(r"class\s+(Factory\w+)", text)

    if not classes:
        continue

    hits = []

    for k in keywords:
        if re.search(r"def\s+\w*" + k + r"\w*\(", text):
            hits.append(k)

    if hits:
        print(
            f"{p.name:40} | {','.join(hits)} | {classes[0]}"
        )
