from pathlib import Path

p = Path("ai/factory/action_router.py")
s = p.read_text()

# Ensure handler execution happens before history append
needle = '''        self._history.append(
            result
        )

        return result
'''

replacement = '''        if action in self.actions and "result" not in result:
            result["result"] = self.actions[action]()

        self._history.append(
            result
        )

        return result
'''

if needle not in s:
    raise SystemExit("history return block not found")

s = s.replace(needle, replacement, 1)

p.write_text(s)

print({
    "status": "ACTION_ROUTER_RESULT_CONTRACT_FIXED",
    "target": "ai/factory/action_router.py",
})
