from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

old = """    def heartbeat(self):
        return {
            "status": "HEALTHY"
        }
"""

new = """    def heartbeat(self):
        return {
            "running": True,
            "status": "HEALTHY"
        }
"""

if old not in text:
    raise SystemExit("heartbeat target not found")

path.write_text(text.replace(old, new))

print({
    "status": "RUNTIME_HEARTBEAT_COMPAT_FIXED",
    "target": "ai/factory/runtime.py"
})
