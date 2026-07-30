from pathlib import Path

path = Path("ai/factory/action_router.py")

text = path.read_text()

text = text.replace(
"""        self._history: List[Dict[str, Any]] = []
""",
"""        self._history: List[Dict[str, Any]] = []
        self.actions = {}
""",
1,
)

insert_marker = """    def route(
"""

insert = """
    def register_action(
        self,
        name,
        handler,
    ):
        self.actions[name] = handler

        return {
            "registered": True,
            "action": name,
        }


"""

if "def register_action(" not in text:
    text = text.replace(
        insert_marker,
        insert + insert_marker,
        1,
    )

# Add legacy unknown_action response
old = """        else:
            capability_context = decision.get(
"""

new = """        else:
            if action not in {
                None,
                "RECOVER",
                "IMPROVE",
            }:
                result = {
                    "error": "unknown_action",
                    "decision": action,
                }

                self._history.append(result)

                return result

            capability_context = decision.get(
"""

if old not in text:
    raise SystemExit("route compatibility target not found")

text = text.replace(old, new, 1)

path.write_text(text)

print({
    "status": "ACTION_ROUTER_COMPAT_FIXED",
    "target": "ai/factory/action_router.py"
})
