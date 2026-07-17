import ast
import json
from pathlib import Path


ROOT = Path("ai/factory")
INPUT = Path("factory_constructor_contract_audit.json")
OUTPUT = Path("factory_constructor_contract_analysis.json")


def find_init_args(path, class_name):
    try:
        tree = ast.parse(path.read_text())
    except Exception:
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if node.name == class_name:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name == "__init__":
                            return [
                                arg.arg
                                for arg in item.args.args
                            ]

    return None


def locate_class(class_name):
    for path in ROOT.rglob("*.py"):
        if "__pycache__" not in str(path):
            args = find_init_args(
                path,
                class_name,
            )

            if args is not None:
                return {
                    "file": str(path),
                    "args": args,
                }

    return None


def main():
    audit = json.loads(
        INPUT.read_text()
    )

    findings = []

    for item in audit:
        for call in item.get("calls", []):
            class_name = call["class"]

            target = locate_class(
                class_name
            )

            if target:
                passed = set(
                    call.get(
                        "keywords",
                        []
                    )
                )

                accepted = set(
                    target["args"]
                )

                unknown = list(
                    passed - accepted
                )

                if unknown:
                    findings.append(
                        {
                            "caller": item["file"],
                            "class": class_name,
                            "constructor_file": target["file"],
                            "passed": list(passed),
                            "accepted": list(accepted),
                            "unknown_arguments": unknown,
                        }
                    )

    result = {
        "contract_mismatches": findings,
        "count": len(findings),
    }

    OUTPUT.write_text(
        json.dumps(
            result,
            indent=2,
        )
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
