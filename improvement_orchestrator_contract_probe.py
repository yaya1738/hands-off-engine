from pathlib import Path

text = Path("ai/factory/improvement_orchestrator.py").read_text()

print("IMPROVEMENT ORCHESTRATOR CONTRACT")
print("=" * 40)

for line in text.splitlines():
    if "def " in line or "execute" in line.lower() or "action" in line.lower():
        print(line.strip())

print("DONE")
