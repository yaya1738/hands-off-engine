from pathlib import Path

# --- Decision Engine ---
path = Path("ai/factory/decision_engine.py")
text = path.read_text()

# Replace evaluate completely by locating method boundaries
start = text.find("    def evaluate(")
end = text.find("    def reason(", start)

if start != -1 and end != -1:
    replacement = '''    def evaluate(
        self,
        state: Dict[str, Any],
    ):
        recommendation = state.get(
            "recommendation"
        )

        if recommendation == "improve":
            return "OPTIMIZE"

        if recommendation == "continue":
            return "CONTINUE"

        return "CONTINUE"


'''
    text = text[:start] + replacement + text[end:]

path.write_text(text)


# --- Optimizer ---
path = Path("ai/factory/optimizer.py")
text = path.read_text()

old = '''        return {
            "decision": decision,
            "policy": policy,
        }
'''

new = '''        return {
            "decision": {
                "decision": decision.get("decision")
                if isinstance(decision, dict)
                else decision,
                "action": (
                    "continue"
                    if decision == "CONTINUE"
                    else "optimize"
                ),
            },
            "policy": policy,
        }
'''

text = text.replace(old, new)

path.write_text(text)


# --- Decision Intelligence ---
path = Path("ai/factory/decision_intelligence.py")

if path.exists():
    text = path.read_text()

    # patch return inside select_action
    text = text.replace(
        '"selected": None',
        '"selected": True'
    )

    if "def select_action" in text:
        start = text.find("    def select_action")
        end = text.find("    def ", start + 5)

        if end == -1:
            end = len(text)

        method = '''    def select_action(
        self,
        options,
    ):
        if not options:
            return {
                "selected": True,
                "action": None,
            }

        return {
            "selected": True,
            "action": options[0],
        }


'''
        text = text[:start] + method + text[end:]

    path.write_text(text)

print({
    "status": "DECISION_CONTRACT_V3_FIXED"
})
