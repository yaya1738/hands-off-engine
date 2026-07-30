import ast
from pathlib import Path

for file in Path("ai/factory").rglob("*.py"):
    try:
        text = file.read_text()
    except:
        continue

    for line_no, line in enumerate(text.splitlines(), 1):
        if "feedback_engine" in line or "self.feedback" in line:
            print(f"{file}:{line_no}: {line.strip()}")
