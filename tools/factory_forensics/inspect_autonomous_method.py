from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

start = text.find("    def run_autonomous_improvement(self):")

end = text.find("\n    def ", start + 10)

print(text[start:end])
