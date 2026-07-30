from pathlib import Path

p = Path("ai/factory/action_router.py")
s = p.read_text()

old = '''        if action == "CONTINUE":
            result = {                                                             "decision": action,
                "action": "continue",                                          }

            if hasattr(self, "_history"):                                          self._history.append(result)

            return result
'''

new = '''        if action == "CONTINUE":
            result = {
                "decision": action,
                "action": "continue",
            }

            if action in self.actions:
                result["result"] = self.actions[action]()

            if hasattr(self, "_history"):
                self._history.append(result)

            return result
'''

if old not in s:
    raise SystemExit("CONTINUE branch not found")

p.write_text(s.replace(old, new, 1))

print({
    "status": "ACTION_ROUTER_CONTINUE_EARLY_RETURN_FIXED",
    "target": "ai/factory/action_router.py",
})
