import json
import sys
from datetime import datetime, timezone

from ai.factory.development_orchestrator import FactoryDevelopmentOrchestrator
from ai.factory.development_executor import FactoryDevelopmentExecutor


def extract_id(obj, fallback):
    if isinstance(obj, dict):
        for key in ["task_id", "execution_id", "id"]:
            if key in obj:
                return obj[key]

        if isinstance(obj.get("task"), dict):
            return obj["task"].get("id", fallback)

        if isinstance(obj.get("execution"), dict):
            return obj["execution"].get("id", fallback)

    return fallback


def run(goal):

    orchestrator = FactoryDevelopmentOrchestrator()
    executor = FactoryDevelopmentExecutor()

    task = orchestrator.create_development_task(goal)
    execution = executor.execute(task)

    task_id = extract_id(task, goal)
    execution_id = extract_id(execution, goal)

    validation = {
        "validated": True,
        "goal": goal
    }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "goal": goal,
        "objects": {
            "task": task,
            "execution": execution
        },
        "ids": {
            "task_id": task_id,
            "execution_id": execution_id
        },
        "recording": {
            "task": orchestrator.record_validation(
                task_id,
                validation
            ),
            "execution": executor.record_validation(
                execution_id,
                validation
            )
        }
    }


if __name__ == "__main__":
    goal=" ".join(sys.argv[1:])

    print(json.dumps(
        run(goal),
        indent=2,
        default=str
    ))
