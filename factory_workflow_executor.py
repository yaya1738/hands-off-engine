from pathlib import Path
import json
import sys
import subprocess


PATTERNS = Path("factory_workflow_patterns.json")
REGISTRY = Path("factory_artifact_registry.json")


def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def normalize(name):
    return (
        name.lower()
        .replace(".py", "")
        .replace("factory_", "")
        .replace("_", "")
    )


def resolve_tools(tool_names, registry):
    artifacts = registry.get("artifacts", [])

    resolved = []

    for tool in tool_names:
        target = normalize(tool)
        matches = []

        for artifact in artifacts:
            filename = normalize(
                artifact.get("file", "")
            )

            if target in filename or filename in target:
                matches.append(artifact)

        resolved.append(
            {
                "requested": tool,
                "matches": matches,
                "resolved": len(matches) > 0,
            }
        )

    return resolved


def record_workflow_result(workflow, ready):
    status = "ready" if ready else "failed"

    subprocess.run(
        [
            "python",
            "factory_workflow_execution_memory.py",
            workflow,
            status,
        ],
        capture_output=True,
        text=True,
    )


def execute_plan(workflow):
    patterns = load_json(PATTERNS)
    registry = load_json(REGISTRY)

    selected = None

    for pattern in patterns.get("patterns", []):
        if pattern["name"] == workflow:
            selected = pattern
            break

    if not selected:
        return {
            "workflow": workflow,
            "ready": False,
            "reason": "workflow not found",
        }

    resolved = resolve_tools(
        selected["tools"],
        registry,
    )

    ready = all(
        item["resolved"]
        for item in resolved
    )

    result = {
        "workflow": workflow,
        "purpose": selected["purpose"],
        "resolved_tools": resolved,
        "success_conditions": selected["success_conditions"],
        "mode": "dry_run",
        "ready": ready,
    }

    record_workflow_result(
        workflow,
        ready,
    )

    return result


def main():

    if len(sys.argv) < 2:
        print(
            "Usage: python factory_workflow_executor.py <workflow>"
        )
        sys.exit(1)

    result = execute_plan(
        sys.argv[1]
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
