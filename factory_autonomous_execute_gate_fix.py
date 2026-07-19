from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

old = '''        if decision["status"] != "READY":
            return {
                "status": "blocked",
                "decision": decision,
            }

        result = self.execute(
            objective
        )
'''

new = '''        ready = (
            decision.get("status") == "READY"
            or decision.get("status") == "PASS"
            or decision.get("classification") == "factory_ready"
        )

        if not ready:
            return {
                "status": "blocked",
                "decision": decision,
            }

        result = self.execute(
            objective
        )
'''

if old not in text:
    raise SystemExit("gate block not found")

path.write_text(text.replace(old, new))

print("autonomous gate compatibility fixed")
