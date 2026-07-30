from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

text = text.replace(
"""    def run_autonomous_improvement(self):
        try:
        metrics = {}
""",
"""    def run_autonomous_improvement(self):
        try:
            metrics = {}
"""
)

p.write_text(text)

print({
    "status": "FIXED_INDENT",
    "next_action": "ADD_EXCEPTION_HANDLER"
})
