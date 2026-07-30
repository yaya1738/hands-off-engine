from pathlib import Path
import ast

path = Path("ai/factory/runtime.py")

try:
    tree = ast.parse(path.read_text())

    found = False
    lines = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "get_assessment_metrics":
            found = True

            start = node.lineno
            end = getattr(node, "end_lineno", start)

            source_lines = path.read_text().splitlines()

            body = "\n".join(
                source_lines[start-1:end]
            )

            lines = [
                x.strip()
                for x in body.splitlines()
                if (
                    "learning" in x.lower()
                    or "experience" in x.lower()
                    or "history" in x.lower()
                    or "return" in x.lower()
                )
            ]

    print({
        "status": "ANALYZED",
        "method_found": found,
        "references": lines,
        "next_action": (
            "VERIFY_METRIC_FLOW"
            if any(
                "learning" in x.lower()
                or "experience" in x.lower()
                for x in lines
            )
            else "ADD_LEARNING_METRIC"
        )
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e)
    })
