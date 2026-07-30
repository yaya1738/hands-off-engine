from pathlib import Path
import ast

matches = []

for path in Path("ai").rglob("*.py"):
    try:
        text = path.read_text()
        tree = ast.parse(text)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                body = ast.get_source_segment(text, node) or ""

                if (
                    "queued" in body.lower()
                    or "dequeue" in body.lower()
                    or "improvement" in body.lower()
                ):
                    if (
                        "execute" in body.lower()
                        or "approve" in body.lower()
                        or "validate" in body.lower()
                        or "audit" in body.lower()
                    ):
                        matches.append({
                            "file": str(path),
                            "method": node.name,
                            "line": node.lineno
                        })

    except Exception:
        pass

print({
    "status": "ANALYZED",
    "handlers": matches,
    "next_action": (
        "TRACE_HANDLER"
        if matches
        else "CREATE_HANDOFF"
    )
})
