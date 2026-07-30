from pathlib import Path
import ast

path = Path("ai/factory/runtime.py")
source = path.read_text()

tree = ast.parse(source)

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "get_assessment_metrics":
        lines = source.splitlines()
        body = "\n".join(lines[node.lineno-1:node.end_lineno])

        print({
            "status": "FOUND",
            "method_lines": node.end_lineno - node.lineno + 1,
            "body": body
        })
        break
else:
    print({
        "status": "NOT_FOUND"
    })
