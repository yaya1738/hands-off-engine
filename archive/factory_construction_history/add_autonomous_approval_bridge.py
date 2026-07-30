from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

old = """        for item in queue:
            if hasattr(self, "improvement_executor"):
                result = self.improvement_executor.execute(
                    item,
                    item
                )
                executed.append(result)
"""

new = """        for item in queue:
            approved = item

            if hasattr(self, "improvement_approval"):
                approval_result = self.improvement_approval.approve(
                    item
                )

                if isinstance(approval_result, dict):
                    approved = approval_result

            if hasattr(self, "improvement_executor"):
                result = self.improvement_executor.execute(
                    approved,
                    approved
                )
                executed.append(result)
"""

if old not in text:
    print({
        "status": "ERROR",
        "reason": "execution bridge block not found"
    })
    raise SystemExit

text = text.replace(old, new)
p.write_text(text)

print({
    "status": "PATCHED",
    "next_action": "VERIFY_COMPILE"
})
