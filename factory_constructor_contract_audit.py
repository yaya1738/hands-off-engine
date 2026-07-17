import ast
import json
from pathlib import Path


ROOT = Path("ai/factory")
OUTPUT = Path("factory_constructor_contract_audit.json")


class ConstructorAudit(ast.NodeVisitor):
    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id.startswith("Factory"):
                self.calls.append(
                    {
                        "class": node.func.id,
                        "keywords": [
                            kw.arg
                            for kw in node.keywords
                        ],
                    }
                )

        self.generic_visit(node)


def main():
    findings = []

    for path in ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text())

        visitor = ConstructorAudit()
        visitor.visit(tree)

        if visitor.calls:
            findings.append(
                {
                    "file": str(path),
                    "calls": visitor.calls,
                }
            )

    OUTPUT.write_text(
        json.dumps(
            findings,
            indent=2,
        )
    )

    print(
        "Constructor audit complete"
    )


if __name__ == "__main__":
    main()
