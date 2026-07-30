from pathlib import Path

path = Path("ai/factory/action_router.py")

text = path.read_text()

old = """            if action not in {
                None,
                "RECOVER",
                "IMPROVE",
            }:
"""

new = """            if (
                action not in self.actions
                and action not in {
                    None,
                    "RECOVER",
                    "IMPROVE",
                }
            ):
"""

if old not in text:
    raise SystemExit("unknown action gate not found")

text = text.replace(old, new, 1)

path.write_text(text)

print({
    "status": "ACTION_ROUTER_CONTINUE_GATE_FIXED",
    "target": "ai/factory/action_router.py"
})
