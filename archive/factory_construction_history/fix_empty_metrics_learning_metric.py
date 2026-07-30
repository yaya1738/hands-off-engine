from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

old = '''            return {
                "success_rate": 0,
                "average_impact": 0,
            }'''

new = '''            return {
                "success_rate": 0,
                "average_impact": 0,
                "learning_experience_count": (
                    len(self.learning.experiences)
                    if hasattr(self, "learning")
                    else 0
                ),
            }'''

if old not in text:
    print({
        "status": "BLOCKED",
        "reason": "EMPTY_METRIC_RETURN_NOT_FOUND"
    })
    raise SystemExit

text = text.replace(old, new, 1)

p.write_text(text)

print({
    "status": "PATCHED",
    "next_action": "VERIFY"
})
