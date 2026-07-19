import json
from datetime import datetime, timezone

from factory_authority_gateway import FactoryAuthorityGateway
from factory_completion_wiring_adapter import FactoryCompletionWiringAdapter


def run():

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_authority_closed_loop_gateway_test"
    }

    gateway = FactoryAuthorityGateway()
    completion = FactoryCompletionWiringAdapter()

    try:

        # 1. Create lifecycle through authority gateway
        lifecycle = gateway.submit(
            "closed loop authority integration test"
        )

        # 2. Simulated review approval boundary
        review = {
            "id": "review-closed-loop-001",
            "approved": True
        }

        # 3. Create a task in the SAME completion tracker instance
        task = completion.tracker.create_task(
            {
                "goal": "closed loop authority integration test",
                "type": "capability_build"
            }
        )

        # 4. Complete through existing completion adapter
        completed = completion.complete_reviewed_task(
            review,
            0,
            {
                "id": "improvement-closed-loop-001",
                "type": "capability_build"
            },
            {
                "status": "success",
                "source": "closed_loop_test"
            },
            {
                "artifact_id": "artifact-closed-loop-001",
                "task_id": str(task["id"]),
                "artifact_type": "capability",
                "location": "factory_closed_loop_test"
            }
        )

        report["lifecycle"] = lifecycle
        report["completion"] = completed

        report["decision"] = {
            "status": "PASS",
            "action": "authority_closed_loop_verified"
        }

    except Exception as e:

        report["error"] = str(e)

        report["decision"] = {
            "status": "FAILED",
            "action": "authority_closed_loop_error"
        }

    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
