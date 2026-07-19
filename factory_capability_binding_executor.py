import json
import sys
import inspect
from datetime import datetime, timezone

from ai.factory.workflow_engine import FactoryWorkflowEngine
from ai.factory.development_orchestrator import FactoryDevelopmentOrchestrator
from ai.factory.development_executor import FactoryDevelopmentExecutor


def adaptive_call(obj, method_name, payload):
    method = getattr(obj, method_name)
    signature = inspect.signature(method)

    params = list(signature.parameters.values())

    if len(params) == 1:
        return method(payload)

    if len(params) == 2:
        return method(
            payload.get("name", "factory_capability_task"),
            payload
        )

    raise RuntimeError(
        f"Unsupported contract {method_name}: {signature}"
    )


def bind_capability(goal):

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "goal": goal,
        "decision": None,
        "pipeline": [],
        "execution": None
    }

    workflow = FactoryWorkflowEngine()
    development = FactoryDevelopmentOrchestrator()
    executor = FactoryDevelopmentExecutor()

    workflow_definition = {
        "name": f"capability_build:{goal}",
        "goal": goal,
        "steps": [
            "analyze_capability",
            "create_development_task",
            "validate",
            "execute"
        ]
    }

    result["decision"] = "reuse_existing_pipeline"

    workflow_id = adaptive_call(
        workflow,
        "create_workflow",
        workflow_definition
    )

    result["pipeline"].append({
        "stage": "workflow_created",
        "workflow_id": workflow_id
    })

    task = development.create_development_task(goal)

    result["pipeline"].append({
        "stage": "development_task_created",
        "task": task
    })

    result["execution"] = {
        "status": "bound",
        "executor": executor.__class__.__name__
    }

    return result


if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) or "create automatic program builder"

    print(json.dumps(
        bind_capability(goal),
        indent=2,
        default=str
    ))
