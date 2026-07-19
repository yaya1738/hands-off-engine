from pathlib import Path

text = Path("ai/factory/improvement_approval.py").read_text()

start = text.find("def approve")
end = text.find("\n    def ", start + 10)

section = text[start:end]

print("APPROVE LOGIC")
print("=" * 30)

for line in section.splitlines():
    if "request" in line or "get(" in line or "return" in line:
        print(line.strip())

print("DONE")
