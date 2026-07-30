from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

if '"learning_experience_count"' in text:
    print({
        "status": "SKIPPED",
        "reason": "LEARNING_METRIC_EXISTS"
    })
    raise SystemExit

needle = '''            "average_impact": (
                sum(impacts) / len(impacts)
                if impacts else 0
            ),
        }'''

replacement = '''            "average_impact": (
                sum(impacts) / len(impacts)
                if impacts else 0
            ),
            "learning_experience_count": (
                len(self.learning.experiences)
                if hasattr(self, "learning")
                else 0
            ),
        }'''

if needle not in text:
    print({
        "status": "BLOCKED",
        "reason": "METRIC_RETURN_SHAPE_NOT_FOUND"
    })
    raise SystemExit

p.write_text(
    text.replace(needle, replacement, 1)
)

print({
    "status": "PATCHED",
    "next_action": "VERIFY_METRIC_FLOW"
})
