from pathlib import Path

text = Path("ai/factory/action_orchestrator.py").read_text()

print("ACTION ORCHESTRATOR CONTRACT")
print("=" * 35)

for line in text.splitlines():
    if "def " in line or "register" in line or "action" in line.lower():
        print(line.strip())

print("DONE")
