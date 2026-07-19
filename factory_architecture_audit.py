from pathlib import Path
import ast
import json


ROOT = Path("ai/factory")


TARGET_WORDS = [
    "router",
    "workflow",
    "orchestrator",
    "engine",
    "control",
    "manager",
]


def analyze_file(path):
    result = {
        "file": str(path),
        "classes": [],
        "methods": [],
        "signals": [],
    }

    try:
        tree = ast.parse(path.read_text())
    except Exception as e:
        result["error"] = str(e)
        return result

    for node in ast.walk(tree):

        if isinstance(node, ast.ClassDef):
            result["classes"].append(node.name)

            name = node.name.lower()

            for word in TARGET_WORDS:
                if word in name:
                    result["signals"].append(
                        f"class:{word}"
                    )

        if isinstance(node, ast.FunctionDef):
            result["methods"].append(node.name)

            name = node.name.lower()

            for word in [
                "route",
                "dispatch",
                "execute",
                "validate",
                "create",
                "run",
            ]:
                if word in name:
                    result["signals"].append(
                        f"method:{word}"
                    )

    return result


def score_component(item):

    score = 0

    for signal in item["signals"]:

        if "class:orchestrator" in signal:
            score += 5

        if "class:workflow" in signal:
            score += 5

        if "class:router" in signal:
            score += 4

        if "method:execute" in signal:
            score += 3

        if "method:validate" in signal:
            score += 2

        if "method:dispatch" in signal:
            score += 3

    return score


def audit():

    components = []

    for path in ROOT.glob("*.py"):
        result = analyze_file(path)
        result["authority_score"] = score_component(result)
        components.append(result)

    components.sort(
        key=lambda x: x["authority_score"],
        reverse=True,
    )

    return {
        "audit": "factory_architecture_authority_scan",
        "components": components[:20],
        "recommended": (
            components[0]
            if components
            else None
        ),
    }


if __name__ == "__main__":
    print(
        json.dumps(
            audit(),
            indent=2,
        )
    )
