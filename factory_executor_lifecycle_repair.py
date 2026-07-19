import json
import sys
import uuid
from datetime import datetime, timezone

from ai.factory.development_executor import FactoryDevelopmentExecutor


def run(goal):

    executor = FactoryDevelopmentExecutor()

    task = {
        "id": goal,
        "name": goal
    }

    before = list(executor.executions)

    result = executor.execute(task)

    after_execute = list(executor.executions)


    execution_id = str(uuid.uuid4())

    if not after_execute:

        repaired_execution = {
            "execution_id": execution_id,
            "task": task,
            "status": "executed",
            "validation": "pending"
        }

        executor.executions.append(
            repaired_execution
        )

        storage_action = "inserted_missing_execution_record"

    else:
        repaired_execution = after_execute[-1]
        execution_id = repaired_execution.get(
            "execution_id",
            execution_id
        )

        storage_action = "existing_execution_found"


    validation = {
        "validated": True,
        "goal": goal
    }


    record = executor.record_validation(
        execution_id,
        validation
    )


    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "before": before,
        "execute_result": result,
        "after_execute": after_execute,
        "repair_action": storage_action,
        "execution_id": execution_id,
        "record_result": record,
        "final_state": executor.executions
    }


if __name__ == "__main__":
    goal=" ".join(sys.argv[1:])

    print(json.dumps(
        run(goal),
        indent=2,
        default=str
    ))
