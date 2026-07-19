from pathlib import Path

text = Path("ai/factory/self_assessment.py").read_text()

start = text.find("def detect_gaps")
end = text.find("\n    def ", start + 10)

section = text[start:end]

lines = section.splitlines()

for i, line in enumerate(lines):
    if "metrics.get" in line:
        print("\nCONTEXT")
        for x in lines[max(0, i-1):i+3]:
            print(x)

print("\nDONE")
