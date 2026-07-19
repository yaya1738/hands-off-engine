import json
import sys
from datetime import datetime, timezone

from ai.factory.development_orchestrator import FactoryDevelopmentOrchestrator
from ai.factory.development_executor import FactoryDevelopmentExecutor


def run(goal):

    o = FactoryDevelopmentOrchestrator()
    e = FactoryDevelopmentExecutor()

    task = o.create_development_task(goal)

    execution = e.execute(task)

    before = e.history()

    result = e.record_validation(
        goal,
        {
            "validated": True,
            "goal": goal
        }
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": task,
        "execution": execution,
        "history": before,
        "record_result": result
    }


if __name__ == "__main__":
    goal=" ".join(sys.argv[1:])
    print(json.dumps(run(goal), indent=2, default=str))
