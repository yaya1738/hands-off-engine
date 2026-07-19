from pathlib import Path
import json
from datetime import datetime, timezone


INPUT = Path("factory_capability_execution_request.json")
OUTPUT = Path("factory_capability_execution_plan.json")


def build_execution_plan(request):
    actions = []

    for item in request.get("execution_requests", []):
        actions.append(
            {
                "capability": item.get("capability"),
                "action": item.get("planned_action"),
                "risk": item.get("risk"),
                "execution_status": item.get("status"),
                "validation_required": True,
                "audit_event": {
                    "type": "capability_integration_request",
                    "timestamp": datetime.now(
                        timezone.utc
                    ).isoformat(),
                    "capability": item.get("capability"),
                },
            }
        )

    return {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "actions": actions,
        "total_actions": len(actions),
    }


def main():
    request = json.loads(
        INPUT.read_text()
    )

    result = build_execution_plan(
        request
    )

    OUTPUT.write_text(
        json.dumps(
            result,
            indent=2,
        )
    )

    print("Execution adapter complete")
    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
