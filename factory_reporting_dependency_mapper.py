from pathlib import Path
import ast
import json


ROOT = Path("ai/factory")
OUTPUT = Path("factory_reporting_dependency_graph.json")

TARGET_WORDS = [
    "report",
    "status",
    "dashboard",
    "summary",
    "snapshot",
    "history",
]


def extract_calls(path):
    result = {
        "file": str(path),
        "calls": [],
    }

    try:
        tree = ast.parse(path.read_text())
    except Exception:
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                name = node.func.attr.lower()

                if any(
                    word in name
                    for word in TARGET_WORDS
                ):
                    result["calls"].append(
                        node.func.attr
                    )

    result["calls"] = sorted(
        list(set(result["calls"]))
    )

    return result


def build_graph():
    graph = []

    for path in ROOT.rglob("*.py"):
        if "__pycache__" not in str(path):
            item = extract_calls(path)

            if item["calls"]:
                graph.append(item)

    return {
        "nodes": graph,
        "node_count": len(graph),
    }


def main():
    result = build_graph()

    OUTPUT.write_text(
        json.dumps(
            result,
            indent=2,
        )
    )

    print("Reporting dependency graph complete")
    print(
        json.dumps(
            result,
            indent=2,
        )[:5000]
    )


if __name__ == "__main__":
    main()
