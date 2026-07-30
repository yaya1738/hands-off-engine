from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

if '"action": "SAFE_STOP"' in text:
    print("SAFE_STOP_ALREADY_EXISTS")
    raise SystemExit(0)

target = '''        elif state == "REVIEW_REQUIRED":
            result = {
                "state": "COMPLETE",
                "action": "SAFE_STOP",
                "decision": decision,
            }
'''

# If branch is missing, insert before BLOCKED handling
marker = '''        elif state == "BLOCKED":'''

if marker not in text:
    raise SystemExit("BLOCKED_BRANCH_NOT_FOUND")

insert = '''        elif state == "REVIEW_REQUIRED":
            result = {
                "state": "COMPLETE",
                "action": "SAFE_STOP",
                "decision": decision,
            }

'''

text = text.replace(marker, insert + marker)

p.write_text(text)

print("SAFE_STOP_BRANCH_ADDED")
