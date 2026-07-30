from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

old = """    def run_autonomous_improvement(self):
"""

new = """    def run_autonomous_improvement(self):
        try:
"""

if old not in text:
    print({"status":"ERROR","reason":"method not found"})
    raise SystemExit

text = text.replace(old, new, 1)

p.write_text(text)

print({
    "status": "PATCHED",
    "note": "wrapper_start_added"
})
