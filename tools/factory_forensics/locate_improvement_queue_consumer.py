from pathlib import Path
import ast

root = Path("ai")

matches = []

for path in root.rglob("*.py"):
    try:
        text = path.read_text()
        tree = ast.parse(text)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "dequeue"
                ):
                    matches.append({
                        "file": str(path),
                        "line": node.lineno
                    })
    except Exception:
        pass

print({
    "status": "ANALYZED",
    "dequeue_consumers": matches,
    "next_action": (
        "TRACE_CONSUMER"
        if matches
        else "MISSING_QUEUE_CONSUMER"
    )
})
