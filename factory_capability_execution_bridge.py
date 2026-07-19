import json
import sys
from datetime import datetime, timezone

from ai.factory.workflow_engine import FactoryWorkflowEngine
from ai.factory.development_orchestrator import FactoryDevelopmentOrchestrator
from ai.factory.development_executor import FactoryDevelopmentExecutor


def run(goal):

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "goal": goal,
        "stages": []
    }

    workflow = FactoryWorkflowEngine()
    development = FactoryDevelopmentOrchestrator()
    executor = FactoryDevelopmentExecutor()

    workflow_result = workflow.create_workflow(
        f"capability_build:{goal}",
        {
            "name": f"capability_build:{goal}",
            "goal": goal,
            "steps": [
                "design",
                "implement",
                "validate"
            ]
        }
    )

    report["stages"].append({
        "workflow": workflow_result
    })

    task = development.create_development_task(goal)

    report["stages"].append({
        "task": task
    })


    if workflow_result and task:

        report["decision"] = "execute"

        execution = executor.execute(task)

        report["execution"] = execution

    else:

        report["decision"] = "halt_missing_dependency"


    return report


if __name__ == "__main__":
    goal = " ".join(sys.argv[1:])
    print(json.dumps(run(goal), indent=2, default=str))
