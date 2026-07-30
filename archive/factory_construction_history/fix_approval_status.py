from pathlib import Path

path = Path("ai/factory/improvement_approval.py")

text = path.read_text()

old = '''    def approve(
        self,
        request: Dict[str, Any],
    ):
        request["status"] = "APPROVED"

        return request
'''

new = '''    def approve(
        self,
        request: Dict[str, Any],
    ):
        request["status"] = "APPROVED"

        improvement = request.get(
            "improvement"
        )

        if improvement:
            improvement["status"] = "APPROVED"

        return request
'''

if old not in text:
    raise SystemExit("target block not found")

path.write_text(
    text.replace(old, new)
)

print("updated")
