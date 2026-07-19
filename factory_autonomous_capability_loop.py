import json
import sys
import uuid
from datetime import datetime, timezone

from ai.factory.workflow_engine import FactoryWorkflowEngine
from ai.factory.development_orchestrator import FactoryDevelopmentOrchestrator
from ai.factory.development_executor import FactoryDevelopmentExecutor


def validation(goal):
    return {
        "validated": True,
        "goal": goal,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def run(goal):
    workflow = FactoryWorkflowEngine()
    orchestrator = FactoryDevelopmentOrchestrator()
    executor = FactoryDevelopmentExecutor()

    task = {
        "id": str(uuid.uuid4()),
        "name": goal,
        "goal": goal,
    }

    workflow_result = workflow.create_workflow(
        "capability_build",
        {"task": goal}
    )

    orchestrator_task = orchestrator.create_development_task(
        task
    )

    execution = executor.execute(
        task
    )

    check = validation(goal)

    orchestrator_record = orchestrator.record_validation(
        task["id"],
        check
    )

    executor_record = executor.record_validation(
        task["id"],
        check
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "goal": goal,
        "workflow": workflow_result,
        "orchestrator_task": orchestrator_task,
        "execution": execution,
        "records": {
            "orchestrator": orchestrator_record,
            "executor": executor_record,
        },
        "status": "completed",
    }


if __name__ == "__main__":
    goal = " ".join(sys.argv[1:])

    if not goal:
        goal = "create automatic program builder"

    print(json.dumps(
        run(goal),
        indent=2,
        default=str
    ))
