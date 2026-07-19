from pathlib import Path

text = Path("ai/factory/improvement_approval.py").read_text()

start = text.find("def approve")
end = text.find("\n    def ", start + 10)

section = text[start:end]

for line in section.splitlines():
    if "request.get" in line:
        print(line.strip())

print("DONE")
