from pathlib import Path

patches = {
    "ai/factory/bootstrap.py": [
        (
            "    def history(self):\n",
            """    def create_factory(self):
        result = self.initialize()
        self._history.append({
            "type": "factory_created",
            "result": result,
        })
        return {
            "status": "FACTORY_CREATED",
        }

    def start_factory(self):
        result = self.start()
        return {
            "status": "RUNNING",
            "result": result,
        }

    def get_runtime(self):
        return self.control_plane

""",
        ),
    ],
    "ai/factory/control_plane.py": [
        (
            "    def history(self):\n",
            """    def inspect(self):
        return {
            "running": self.running,
            "history_count": len(self._history),
        }

    def save_state(self, state):
        result = {
            "status": "STATE_SAVED",
            "state": state,
        }
        self._history.append(result)
        return result

    def optimize(self):
        return {
            "action": "continue",
        }

""",
        ),
    ],
}

for file, changes in patches.items():
    path = Path(file)
    text = path.read_text()

    for marker, insert in changes:
        if insert.strip() not in text:
            text = text.replace(marker, insert + marker)

    path.write_text(text)

print({
    "status": "COMPATIBILITY_ADAPTERS_ADDED",
    "targets": list(patches.keys()),
})
