from pathlib import Path

text = Path("ai/factory/self_assessment.py").read_text()

start = text.find("def detect_gaps")
end = text.find("\n    def ", start + 10)

section = text[start:end]

for line in section.splitlines():
    if "metrics.get" in line:
        print(line.strip())

print("DONE")
