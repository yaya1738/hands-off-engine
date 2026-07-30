from pathlib import Path

path = Path("ai/factory/action_router.py")

text = path.read_text()

old = """        result = {
            "decision": action,
            "action": target,
            "capability_context": decision.get(
                "capability_context",
                {}
            ),
        }

        self._history.append(
            result
        )

        return result
"""

new = """        result = {
            "decision": action,
            "action": target,
            "capability_context": decision.get(
                "capability_context",
                {}
            ),
        }

        if action in self.actions:
            result["result"] = self.actions[action]()

        self._history.append(
            result
        )

        return result
"""

if old not in text:
    raise SystemExit("action router result block not found")

path.write_text(text.replace(old, new))

print({
    "status": "ACTION_ROUTER_RESULT_COMPAT_FIXED",
    "target": "ai/factory/action_router.py"
})
