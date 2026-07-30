from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

if "self.learning.record_experience" in text:
    print({
        "status": "SKIPPED",
        "reason": "ALREADY_CONNECTED"
    })
    raise SystemExit

needle = '''        result = self.checkpoint_executor.execute(
'''

if needle not in text:
    print({
        "status": "BLOCKED",
        "reason": "EXECUTION_POINT_NOT_FOUND"
    })
    raise SystemExit

insert = '''        result = self.checkpoint_executor.execute(
'''

replacement = '''        result = self.checkpoint_executor.execute(
'''

# We do not patch yet; only locate safely.
print({
    "status": "READY",
    "location": "checkpoint_executor_result",
    "next_action": "INSERT_AFTER_RESULT_FINALIZATION"
})
