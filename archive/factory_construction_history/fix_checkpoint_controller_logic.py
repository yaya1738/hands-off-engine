from pathlib import Path

p = Path("verify_runtime_checkpoint_control.py")
text = p.read_text()

text = text.replace(
'''if output.get("state") in [
        "COMPLETE",
        "ERROR",
    ]:''',
'''if output.get("status") in [
        "COMPLETE",
        "ERROR",
    ] or output.get("decision", {}).get("state") in [
        "REVIEW_REQUIRED",
        "READY_TO_COMMIT",
        "BLOCKED",
    ]:''')

p.write_text(text)

print("CHECKPOINT_CONTROLLER_DECISION_LOGIC_FIXED")
