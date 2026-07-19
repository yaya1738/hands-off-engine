from pathlib import Path

text = Path("ai/factory/decision_option_adapter.py").read_text()

start = text.find("def build_options")
end = text.find("\n    def ", start + 10)

section = text[start:end]

print("BUILD OPTIONS LOGIC")
print("=" * 35)

for line in section.splitlines():
    if "get(" in line or "for " in line or "return" in line or "append" in line:
        print(line.strip())

print("DONE")
