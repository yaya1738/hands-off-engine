from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

old = """    def history(self):
        return self._history
"""

new = """    def history(self):
        return [
            entry
            for entry in self._history
            if entry.get("type")
            not in {
                "integrity_report",
                "runtime_started",
                "runtime_stopped",
            }
        ]
"""

if old not in text:
    raise SystemExit("history method target not found")

path.write_text(text.replace(old, new))

print({
    "status": "RUNTIME_HISTORY_COMPAT_FIXED",
    "target": "ai/factory/runtime.py"
})
