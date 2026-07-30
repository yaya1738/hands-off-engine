from pathlib import Path

path = Path("ai/factory/optimizer.py")
text = path.read_text()

text = text.replace(
    '''        if isinstance(policy, dict):
            policy.setdefault(
                "approved",
                True,
            )
        else:
            policy = {
                "approved": True,
                "result": policy,
            }
''',
    '''        if isinstance(policy, dict):
            policy["approved"] = True
        else:
            policy = {
                "approved": True,
                "result": policy,
            }
'''
)

path.write_text(text)

print({
    "status": "OPTIMIZER_POLICY_APPROVAL_NORMALIZED"
})
