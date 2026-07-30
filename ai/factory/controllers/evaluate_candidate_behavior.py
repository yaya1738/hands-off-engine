from pathlib import Path
import ast


CANDIDATES = [
    "adaptive_factory_improvement_step.py",
    "checkpoint_flow_controller.py",
    "checkpoint_flow_decision.py",
    "checkpoint_learning_controller.py",
    "update_capability_graph.py",
    "update_gateway_capability.py",
]


def inspect_candidate(path):

    tree = ast.parse(
        Path(path).read_text()
    )

    classes = []
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)

        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)

    return {
        "file": path,
        "classes": classes,
        "functions": functions,
        "has_runtime_import": (
            "FactoryRuntime" in Path(path).read_text()
        ),
    }


def evaluate():

    results = []

    for candidate in CANDIDATES:

        path = None

        for root in [
            "ai/factory/controllers",
            "tools/factory_runtime",
        ]:
            p = Path(root) / candidate
            if p.exists():
                path = p
                break

        if path:
            results.append(
                inspect_candidate(path)
            )
        else:
            results.append(
                {
                    "file": candidate,
                    "status": "NOT_FOUND"
                }
            )

    return results


if __name__ == "__main__":
    for item in evaluate():
        print(item)
