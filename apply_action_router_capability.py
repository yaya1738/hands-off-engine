from pathlib import Path

p = Path("ai/factory/action_router.py")

text = p.read_text()

old = '''        result = {
            "decision": action,
            "action": target,
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
'''

if old not in text:
    raise SystemExit("TARGET_NOT_FOUND")

p.write_text(text.replace(old, new, 1))
print("UPDATED")
