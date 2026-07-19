from pathlib import Path

text = Path("ai/factory/runtime.py").read_text()

start = text.find("def execute_approved_improvement")
end = text.find("\n    def ", start + 10)

section = text[start:end]

print("EXECUTE APPROVED LOGIC")
print("=" * 35)

for line in section.splitlines():
    if "improvement" in line or "action" in line or "get(" in line:
        print(line.strip())

print("DONE")
