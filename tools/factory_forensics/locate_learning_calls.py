from pathlib import Path

text = Path("ai/factory/runtime.py").read_text()

for i, line in enumerate(text.splitlines(), 1):
    if "record_experience" in line or "learning" in line:
        print(f"{i}: {line.strip()}")
