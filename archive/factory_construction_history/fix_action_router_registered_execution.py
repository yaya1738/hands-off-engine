from pathlib import Path

path = Path("ai/factory/action_router.py")

text = path.read_text()

old = """        self._history.append(
            result
        )

        return result
"""

new = """        if action in self.actions:
            result["result"] = self.actions[action]()

        self._history.append(
            result
        )

        return result
"""

if old not in text:
    raise SystemExit("return block not found")

path.write_text(text.replace(old, new, 1))

print({
    "status": "ACTION_ROUTER_REGISTERED_EXECUTION_ADDED",
    "target": "ai/factory/action_router.py"
})
