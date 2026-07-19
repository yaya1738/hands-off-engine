from pathlib import Path

text = Path("ai/factory/runtime.py").read_text()

start = text.find("def execute(")
end = text.find("\n    def ", start + 10)

section = text[start:end]

for line in section.splitlines():
    if "return" in line:
        print(line.strip())

print("DONE")
