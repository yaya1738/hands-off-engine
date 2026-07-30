from pathlib import Path

text = Path("ai/factory/runtime.py").read_text()

needle = '''        state = decision.get("state")'''

if needle in text:
    print({
        "status": "READY",
        "location": "AFTER_DECISION_STATE",
        "next_action": "ADD_CHECKPOINT_OBSERVATION"
    })
else:
    print({
        "status": "BLOCKED",
        "reason": "DECISION_STATE_NOT_FOUND"
    })
