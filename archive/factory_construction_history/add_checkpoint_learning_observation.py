from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

if "checkpoint_cycle_decision" in text:
    print({
        "status": "SKIPPED",
        "reason": "OBSERVATION_ALREADY_EXISTS"
    })
    raise SystemExit

needle = '''        state = decision.get("state")
'''

insert = '''        state = decision.get("state")

        if hasattr(self, "learning"):
            self.learning.record_experience(
                {
                    "type": "checkpoint_cycle_decision",
                    "decision": decision,
                    "state": state,
                }
            )
'''

if needle not in text:
    print({
        "status": "BLOCKED",
        "reason": "INSERTION_POINT_MISSING"
    })
    raise SystemExit

text = text.replace(
    needle,
    insert,
    1
)

p.write_text(text)

print({
    "status": "PATCHED",
    "next_action": "VERIFY_CHECKPOINT_LEARNING"
})
