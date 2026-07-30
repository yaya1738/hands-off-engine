from pathlib import Path

p = Path("ai/factory/action_router.py")
s = p.read_text()

old = '''        result = {
            "decision": action,
            "action": target,
            "capability_context": decision.get(
                "capability_context",
                {}
            ),
        }
'''

new = '''        result = {
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

if old not in s:
    raise SystemExit("target route result block not found")

s = s.replace(old, new, 1)

# remove duplicate execution blocks if they exist
s = s.replace(
'''        if action in self.actions:
            result["result"] = self.actions[action]()

        if action in self.actions:
            result["result"] = self.actions[action]()
''',
'''        if action in self.actions and "result" not in result:
            result["result"] = self.actions[action]()
'''
)

p.write_text(s)

print({
    "status": "ACTION_ROUTER_CONTINUE_EXECUTION_FIXED",
    "target": "ai/factory/action_router.py"
})
