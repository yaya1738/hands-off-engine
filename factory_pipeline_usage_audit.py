import ast
import json
from pathlib import Path

ROOT = Path("ai/factory")
OUTPUT = Path("factory_pipeline_usage_audit.json")

TARGET = "FactoryDevelopmentPipeline"


def main():
    findings = []

    for path in ROOT.rglob("*.py"):
        if "__pycache__" in str(path):
            continue

        tree = ast.parse(path.read_text())

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if node.id == TARGET:
                    findings.append(
                        {
                            "file": str(path),
                            "line": node.lineno,
                            "type": "reference",
                        }
                    )

            if isinstance(node, ast.Attribute):
                if node.attr in [
                    "development_pipeline",
                    "advisor",
                    "approval",
                ]:
                    findings.append(
                        {
                            "file": str(path),
                            "line": node.lineno,
                            "attribute": node.attr,
                        }
                    )

    result = {
        "target": TARGET,
        "findings": findings,
        "count": len(findings),
    }

    OUTPUT.write_text(
        json.dumps(result, indent=2)
    )

    print(
        json.dumps(result, indent=2)
    )


if __name__ == "__main__":
    main()
