from pathlib import Path

text = Path("ai/factory/improvement_approval.py").read_text()

start = text.find("def approve")
end = text.find("\n    def ", start + 10)

section = text[start:end]

idx = section.find("request.get")

print("APPROVAL GET CONTEXT")
print("=" * 30)

print(section[idx:idx+80])

print("DONE")
