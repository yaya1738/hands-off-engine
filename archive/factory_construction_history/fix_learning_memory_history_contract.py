from pathlib import Path

p = Path("ai/factory/learning_memory.py")

s = p.read_text()

old = """    def remember(
        self,
        item
    ):
"""

if old not in s:
    raise SystemExit("remember method not found")

# Find existing append behavior and inject history tracking if missing
if "self._history.append" not in s[s.index("def remember"):s.index("def history")]:
    start = s.index("def remember")
    end = s.index("def history", start)

    block = s[start:end]

    block = block.replace(
        "        return",
        "        self._history.append(item)\\n\\n        return",
        1
    )

    s = s[:start] + block + s[end:]

p.write_text(s)

print({
    "status": "LEARNING_MEMORY_HISTORY_COMPAT_FIXED",
    "target": "ai/factory/learning_memory.py"
})
