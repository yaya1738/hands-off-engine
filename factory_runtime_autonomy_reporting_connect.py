from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

old = '''        if not ready:
            return {
                "status": "blocked",
                "decision": decision,
            }

        result = self.execute(
            objective
        )
'''

new = '''        autonomy_report = self.report_autonomy_state(
            objective,
            decision,
        )

        if not ready:
            return {
                "status": "blocked",
                "decision": decision,
                "autonomy_report": autonomy_report,
            }

        result = self.execute(
            objective
        )
'''

if old not in text:
    raise SystemExit("target block not found")

path.write_text(text.replace(old, new))

print("autonomy reporting connected")
