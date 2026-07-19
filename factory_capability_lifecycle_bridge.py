import json
import sys
from datetime import datetime, timezone

from ai.factory.workflow_engine import FactoryWorkflowEngine
from ai.factory.development_orchestrator import FactoryDevelopmentOrchestrator
from ai.factory.development_executor import FactoryDevelopmentExecutor


def run(goal):

    workflow = FactoryWorkflowEngine()
    orchestrator = FactoryDevelopmentOrchestrator()
    executor = FactoryDevelopmentExecutor()

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "goal": goal
    }

    workflow_result = workflow.create_workflow(
        f"capability_build:{goal}",
        {
            "name": goal,
            "steps": ["design", "implement", "validate"]
        }
    )

    report["workflow"] = workflow_result

    task = orchestrator.create_development_task(goal)

    report["task"] = task

    execution = executor.execute(task)

    report["execution"] = execution

    validation = workflow.validate_workflow({
        "task": goal,
        "status": "executed"
    })

    report["validation"] = validation


    report["recording"] = {
        "task_record": orchestrator.record_validation(
            task,
            validation
        ),
        "execution_record": executor.record_validation(
            execution,
            validation
        )
    }

    return report


if __name__ == "__main__":
    goal=" ".join(sys.argv[1:])
    print(json.dumps(run(goal), indent=2, default=str))
