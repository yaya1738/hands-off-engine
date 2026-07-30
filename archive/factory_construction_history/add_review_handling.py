from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

old = '''        if state == "READY_TO_COMMIT":
            execution = self.checkpoint_executor.execute(
                decision
            )

            result = {
                "state": "COMPLETE",
                "action": "CHECKPOINT_EXECUTED",
                "decision": decision,
                "execution": execution,
            }
'''

new = '''        if state == "READY_TO_COMMIT":
            execution = self.checkpoint_executor.execute(
                decision
            )

            result = {
                "state": "COMPLETE",
                "action": "CHECKPOINT_EXECUTED",
                "decision": decision,
                "execution": execution,
            }

        elif state == "REVIEW_REQUIRED":
            result = {
                "state": "COMPLETE",
                "action": "SAFE_STOP",
                "decision": decision,
            }
'''

if old not in text:
    raise SystemExit(
        "READY_TO_COMMIT branch not found"
    )

if "action\": \"SAFE_STOP\"" in text:
    print("SAFE_STOP_ALREADY_PRESENT")
else:
    text = text.replace(old, new)
    p.write_text(text)
    print("REVIEW_HANDLING_ADDED")
