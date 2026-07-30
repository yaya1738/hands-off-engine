from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

marker = "return checkpoint"

if marker not in text:
    print({
        "status": "BLOCKED",
        "reason": "CHECKPOINT_RETURN_MARKER_NOT_FOUND",
        "next_action": "TRACE_RUNTIME_PATH"
    })
    raise SystemExit

if "record_experience(" in text:
    print({
        "status": "SKIPPED",
        "reason": "BRIDGE_ALREADY_EXISTS",
        "next_action": "VERIFY"
    })
    raise SystemExit

replacement = """
if hasattr(self, "learning"):
    self.learning.record_experience(
        checkpoint
    )

return checkpoint
"""

text = text.replace(
    marker,
    replacement,
    1
)

path.write_text(text)

print({
    "status": "PATCHED",
    "next_action": "VERIFY_BRIDGE"
})
