from pathlib import Path

path = Path("ai/factory/optimizer.py")
text = path.read_text()

old = '''        return {
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

new = '''        decision_value = (
            decision.get("decision")
            if isinstance(decision, dict)
            else decision
        )

        return {
            "decision": {
                "decision": decision_value,
                "action": (
                    "continue"
                    if decision_value == "CONTINUE"
                    else "optimize"
                ),
            },
            "policy": policy,
        }
'''

if old in text:
    text = text.replace(old, new)

path.write_text(text)

print({
    "status": "OPTIMIZER_ACTION_MAPPING_FIXED"
})
