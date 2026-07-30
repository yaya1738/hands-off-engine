from pathlib import Path

p = Path("ai/factory/orchestration_intelligence.py")

text = p.read_text()

old = '''        result = {
            "dispatched": True,
            "count": len(tasks),
        }
'''

new = '''        capability_context_count = sum(
            1 for task in tasks
            if "capability_context" in task
        )

        result = {
            "dispatched": True,
            "count": len(tasks),
            "capability_context_count": capability_context_count,
        }
'''

if old not in text:
    raise SystemExit("TARGET_NOT_FOUND")

p.write_text(text.replace(old, new, 1))
print("UPDATED")
