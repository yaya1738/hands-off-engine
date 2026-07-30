from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

marker = "    def run_autonomous_improvement(self):"

insert = """
    def start(self):
        self._history.append(
            {
                "type": "runtime_started"
            }
        )

        return {
            "status": "STARTED"
        }


    def run(self, payload):
        return self.execute(payload)


    def stop(self):
        self._history.append(
            {
                "type": "runtime_stopped"
            }
        )

        return {
            "status": "STOPPED"
        }

"""

if "def start(self):" in text:
    raise SystemExit("lifecycle compatibility already exists")

if marker not in text:
    raise SystemExit("runtime insertion point not found")

text = text.replace(
    marker,
    insert + marker
)

path.write_text(text)

print({
    "status": "RUNTIME_LIFECYCLE_COMPAT_ADDED",
    "target": "ai/factory/runtime.py"
})
