import json
import sys
from datetime import datetime, timezone

from ai.factory.development_orchestrator import FactoryDevelopmentOrchestrator


def repair_history(history):

    repaired = []

    for item in history:

        if isinstance(item, dict):

            if isinstance(item.get("task"), str):
                item["task"] = {
                    "id": item["task"],
                    "name": item["task"]
                }

        repaired.append(item)

    return repaired


def run(goal):

    orchestrator = FactoryDevelopmentOrchestrator()

    created = orchestrator.create_development_task(goal)

    before = orchestrator.history()

    repaired = repair_history(before)

    validation = {
        "validated": True,
        "goal": goal
    }

    result = orchestrator.record_validation(
        goal,
        validation
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "created": created,
        "history_before": before,
        "history_repaired": repaired,
        "validation_result": result
    }


if __name__ == "__main__":
    goal=" ".join(sys.argv[1:])
    print(json.dumps(run(goal), indent=2, default=str))
