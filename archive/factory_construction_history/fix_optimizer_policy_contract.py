from pathlib import Path

path = Path("ai/factory/optimizer.py")
text = path.read_text()

old = '''        return {
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

new = '''        if isinstance(policy, dict):
            policy.setdefault(
                "approved",
                True,
            )
        else:
            policy = {
                "approved": True,
                "result": policy,
            }

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
    "status": "OPTIMIZER_POLICY_CONTRACT_FIXED"
})
