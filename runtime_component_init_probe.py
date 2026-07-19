from pathlib import Path

text = Path("ai/factory/runtime.py").read_text()

for line in text.splitlines():
    if "self." in line and "=" in line:
        if "executor" in line or "manager" in line or "adapter" in line or "orchestrator" in line:
            print(line.strip())

print("DONE")
