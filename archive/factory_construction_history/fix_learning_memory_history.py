from pathlib import Path

p = Path("ai/factory/learning_memory.py")
s = p.read_text()

old = '''    def history(self):
        return getattr(
            self,
            "_memory",
            [],
        )
'''

new = '''    def history(self):
        return self._history
'''

if old not in s:
    raise SystemExit("target block not found")

p.write_text(s.replace(old, new))

print({
    "status": "LEARNING_MEMORY_HISTORY_FIXED",
    "target": "ai/factory/learning_memory.py",
})
