from pathlib import Path

text = Path("ai/factory/improvement_executor.py").read_text()

start = text.find("def execute")
end = text.find("\n    def ", start + 10)

section = text[start:end]

print("EXECUTOR ACTION LOGIC")
print("=" * 35)

for line in section.splitlines():
    if "action" in line or "call" in line or "()" in line:
        print(line.strip())

print("DONE")
