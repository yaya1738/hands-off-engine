from pathlib import Path

p = Path("ai/factory/action_router.py")
s = p.read_text()

needle = '''        result = {
            "decision": action,
            "action": target,
            "capability_context": decision.get(
                "capability_context",
                {}
            ),
        }
'''

if needle not in s:
    raise SystemExit("route result block not found")

replacement = '''        result = {
            "decision": action,
            "action": target,
            "capability_context": decision.get(
                "capability_context",
                {}
            ),
        }

        if action in self.actions:
            result["result"] = self.actions[action]()
'''

s = s.replace(needle, replacement, 1)

# remove any broken duplicate blocks after insertion
while s.count('''        if action in self.actions:
            result["result"] = self.actions[action]()
''') > 1:
    first = s.find('''        if action in self.actions:
            result["result"] = self.actions[action]()
''')
    second = s.find('''        if action in self.actions:
            result["result"] = self.actions[action]()
''', first + 1)
    s = s[:second] + s[second + len('''        if action in self.actions:
            result["result"] = self.actions[action]()
'''):]

p.write_text(s)

print("ACTION_ROUTER_CONTINUE_CONTRACT_FIXED")
