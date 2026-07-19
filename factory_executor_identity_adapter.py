import json
import sys
import uuid
from datetime import datetime, timezone

from ai.factory.development_executor import FactoryDevelopmentExecutor


def run(goal):

    executor = FactoryDevelopmentExecutor()

    execution_id = str(uuid.uuid4())

    execution = {
        "execution_id": execution_id,
        "task": {
            "id": goal,
            "name": goal
        },
        "status": "executed",
        "validation": "pending"
    }

    validation = {
        "validated": True,
        "execution_id": execution_id,
        "goal": goal
    }

    record = executor.record_validation(
        execution_id,
        validation
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "execution": execution,
        "record": record
    }


if __name__ == "__main__":
    goal=" ".join(sys.argv[1:])
    print(json.dumps(run(goal), indent=2, default=str))
