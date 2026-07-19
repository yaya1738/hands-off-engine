from pathlib import Path

text = Path("ai/factory/runtime.py").read_text()

for line in text.splitlines():
    if "decision" in line.lower():
        print(line)
