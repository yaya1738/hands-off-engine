from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

marker = "    def execute(self, goal):\n"

insert = '''
    def report_autonomy_state(self, objective, decision):

        report = {
            "objective": objective,
            "decision": decision,
            "status": "recorded",
        }

        self.emit_event(
            "autonomy.decision",
            report,
        )

        self._history.append(
            {
                "type": "autonomy",
                "report": report,
            }
        )

        return report


'''

if marker not in text:
    raise SystemExit("marker not found")

text = text.replace(
    marker,
    insert + marker
)

path.write_text(text)

print("autonomy reporting added")
