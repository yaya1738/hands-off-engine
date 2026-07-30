from pathlib import Path

p = Path("ai/factory/action_router.py")
s = p.read_text()

start = s.find('        if action == "CONTINUE":')
end = s.find('        if action == "RECOVER":')

if start == -1 or end == -1:
    raise SystemExit("Could not locate CONTINUE block")

new_block = '''        if action == "CONTINUE":
            result = {
                "decision": action,
                "action": "continue",
            }

            if action in self.actions:
                result["result"] = self.actions[action]()

            self._history.append(result)

            return result

'''

s = s[:start] + new_block + s[end:]

p.write_text(s)

print({
    "status": "FORCED_CONTINUE_ROUTE_FIX",
    "target": "ai/factory/action_router.py"
})
