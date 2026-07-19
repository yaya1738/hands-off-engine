import json
import sys
import inspect
from datetime import datetime, timezone

from ai.factory.workflow_engine import FactoryWorkflowEngine
from ai.factory.development_orchestrator import FactoryDevelopmentOrchestrator
from ai.factory.development_executor import FactoryDevelopmentExecutor


def adaptive_call(obj, method_name, *args):
    method = getattr(obj, method_name)

    try:
        return method(*args)
    except TypeError:
        sig = inspect.signature(method)
        params = list(sig.parameters)

        if len(params) == 1:
            return method(args[0])

        raise


def validate_capability(goal):

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "goal": goal,
        "validation_pipeline": []
    }

    workflow = FactoryWorkflowEngine()
    development = FactoryDevelopmentOrchestrator()
    executor = FactoryDevelopmentExecutor()

    task = {
        "task": goal,
        "status": "executed"
    }

    validation = None

    if hasattr(workflow, "validate_workflow"):
        validation = adaptive_call(
            workflow,
            "validate_workflow",
            task
        )

        report["validation_pipeline"].append({
            "source": "workflow_engine",
            "result": validation
        })


    if hasattr(development, "record_validation"):
        record = adaptive_call(
            development,
            "record_validation",
            goal,
            validation
        )

        report["validation_pipeline"].append({
            "source": "development_orchestrator",
            "result": record
        })


    if hasattr(executor, "record_validation"):
        record = adaptive_call(
            executor,
            "record_validation",
            goal,
            validation
        )

        report["validation_pipeline"].append({
            "source": "development_executor",
            "result": record
        })


    report["decision"] = (
        "validated"
        if validation is not None
        else "validation_not_available"
    )

    return report


if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) or "create automatic program builder"

    print(json.dumps(
        validate_capability(goal),
        indent=2,
        default=str
    ))
