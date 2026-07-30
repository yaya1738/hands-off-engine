from pathlib import Path

p = Path("ai/factory/action_router.py")

text = p.read_text()

old = '''        else:
            target = "continue"
'''

new = '''        else:
            capability_context = decision.get(
                "capability_context",
                {}
            )

            capability_values = str(
                capability_context
            )

            if "self_improvement" in capability_values:
                target = "improvement_pipeline"
            else:
                target = "continue"
'''

if old not in text:
    raise SystemExit("TARGET_NOT_FOUND")

p.write_text(text.replace(old, new, 1))
print("UPDATED")
