"""Read-only workflow planning compatibility helper.

Legacy result persistence executed another Python module directly. Planning
remains available locally; persistence/execution is owned by the authority
layer.
"""
from pathlib import Path
import json
import sys

PATTERNS = Path("factory_workflow_patterns.json")
REGISTRY = Path("factory_artifact_registry.json")


def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def normalize(name):
    return name.lower().replace(".py", "").replace("factory_", "").replace("_", "")


def resolve_tools(tool_names, registry):
    artifacts = registry.get("artifacts", [])
    resolved = []
    for tool in tool_names:
        target = normalize(tool)
        matches = [
            artifact for artifact in artifacts
            if target in normalize(artifact.get("file", ""))
            or normalize(artifact.get("file", "")) in target
        ]
        resolved.append({"requested": tool, "matches": matches, "resolved": bool(matches)})
    return resolved


def record_workflow_result(workflow, ready):
    """Return a governed persistence handoff without performing I/O mutation."""
    return {
        "workflow": workflow,
        "status": "ready" if ready else "failed",
        "persisted": False,
        "authority_required": True,
        "next_step": "FactoryAuthorityGateway",
    }


def execute_plan(workflow):
    patterns = load_json(PATTERNS)
    registry = load_json(REGISTRY)
    selected = next(
        (pattern for pattern in patterns.get("patterns", []) if pattern.get("name") == workflow),
        None,
    )
    if not selected:
        return {"workflow": workflow, "ready": False, "reason": "workflow not found"}

    resolved = resolve_tools(selected.get("tools", []), registry)
    ready = all(item["resolved"] for item in resolved)
    result = {
        "workflow": workflow,
        "purpose": selected.get("purpose", ""),
        "resolved_tools": resolved,
        "success_conditions": selected.get("success_conditions", []),
        "mode": "dry_run",
        "ready": ready,
        "authority_required": True,
        "next_step": "FactoryAuthorityGateway",
        "persistence": record_workflow_result(workflow, ready),
    }
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python factory_workflow_executor.py <workflow>")
        return 1
    print(json.dumps(execute_plan(sys.argv[1]), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
