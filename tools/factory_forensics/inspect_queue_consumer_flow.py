from pathlib import Path
import ast

path = Path("ai/factory/improvement_orchestrator.py")
source = path.read_text()

tree = ast.parse(source)

for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "dequeue"
        ):
            start = max(0, node.lineno - 15)
            end = node.lineno + 20

            lines = source.splitlines()

            print({
                "status": "FOUND",
                "context": "\n".join(
                    lines[start:end]
                ),
                "next_action": "IDENTIFY_POST_QUEUE_HANDLER"
            })
            raise SystemExit

print({
    "status": "NOT_FOUND"
})
