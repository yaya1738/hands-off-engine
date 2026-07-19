import json
import sys
import inspect
from datetime import datetime, timezone

from ai.factory.development_orchestrator import FactoryDevelopmentOrchestrator
from ai.factory.development_executor import FactoryDevelopmentExecutor


def inspect_method(obj, name):
    method = getattr(obj, name, None)

    if not method:
        return None

    return {
        "method": name,
        "signature": str(inspect.signature(method)),
        "parameters": [
            p for p in inspect.signature(method).parameters
        ]
    }


def adaptive_record(obj, name, goal, validation):

    method = getattr(obj, name, None)

    if not method:
        return {
            "available": False
        }

    attempts = [
        (goal, validation),
        ({
            "task_id": goal,
            "validation": validation
        },),
        (goal,),
    ]

    results = []

    for args in attempts:
        try:
            result = method(*args)
            return {
                "success": True,
                "args_used": str(args),
                "result": result
            }
        except TypeError as e:
            results.append(str(e))

    return {
        "success": False,
        "errors": results
    }


def run(goal):

    validation = {
        "validated": True,
        "task": goal
    }

    orchestrator = FactoryDevelopmentOrchestrator()
    executor = FactoryDevelopmentExecutor()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "goal": goal,
        "contracts": [
            inspect_method(orchestrator, "record_validation"),
            inspect_method(executor, "record_validation")
        ],
        "records": {
            "orchestrator": adaptive_record(
                orchestrator,
                "record_validation",
                goal,
                validation
            ),
            "executor": adaptive_record(
                executor,
                "record_validation",
                goal,
                validation
            )
        }
    }


if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) or "create automatic program builder"

    print(json.dumps(
        run(goal),
        indent=2,
        default=str
    ))
