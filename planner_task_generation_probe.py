from pathlib import Path

text = Path("ai/factory/improvement_planner.py").read_text()

for line in text.splitlines():
    if "tasks" in line or "append" in line or "plan" in line:
        print(line.strip())

print("DONE")
