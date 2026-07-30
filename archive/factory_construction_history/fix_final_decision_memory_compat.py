from pathlib import Path

# Action router
p = Path("ai/factory/action_router.py")
s = p.read_text()

s = s.replace(
'''        action = decision.get(
            "decision"
        )
''',
'''        action = decision.get(
            "decision"
        )

        if action == "CONTINUE":
            result = {
                "decision": action,
                "action": "continue",
            }

            if hasattr(self, "_history"):
                self._history.append(result)

            return result
''',
1
)

p.write_text(s)


# Decision engine
p = Path("ai/factory/decision_engine.py")
s = p.read_text()

old = '''    def evaluate(
        self,
        state: Dict[str, Any],
    ):
'''

if old in s:
    s = s.replace(
old,
'''    def evaluate(
        self,
        state: Dict[str, Any],
    ):
        if state.get("health") == "DOWN":
            return "RECOVER"

        if state.get("success_rate", 1) <= 0.5:
            return "IMPROVE"

''',
1
)

p.write_text(s)


# Learning memory
p = Path("ai/factory/learning_memory.py")
s = p.read_text()

if "def remember" in s and "self._history.append" not in s:
    s = s.replace(
'''    def remember(
        self,
        item,
    ):
''',
'''    def remember(
        self,
        item,
    ):
        self._history.append(item)

''',
1
)

p.write_text(s)

print({
    "status": "FINAL_DECISION_MEMORY_COMPAT_PATCHED"
})
