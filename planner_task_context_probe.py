from pathlib import Path

text = Path("ai/factory/improvement_planner.py").read_text()

start = text.find("def plan")
end = text.find("\n    def ", start + 10)

section = text[start:end]

lines = section.splitlines()

for i, line in enumerate(lines):
    if "tasks =" in line:
        print("CONTEXT")
        for x in lines[max(0, i-3):i+8]:
            print(x)

print("DONE")
