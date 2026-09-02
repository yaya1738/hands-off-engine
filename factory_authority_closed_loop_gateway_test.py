import json
from datetime import datetime, timezone

from ai.factory.authority_gateway import FactoryAuthorityGateway
from factory_completion_wiring_adapter import FactoryCompletionWiringAdapter


def run():
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_authority_closed_loop_gateway_test",
    }

    gateway = FactoryAuthorityGateway()
    completion = gateway.completion

    try:
        lifecycle = gateway.submit_goal("closed loop authority integration test")

        review = {
            "id": "review-closed-loop-001",
            "approved": True,
        }

        task = completion.tracker.create_task(
            {
                "goal": "closed loop authority integration test",
                "type": "capability_build",
            }
        )

        completed = completion.complete_reviewed_task(
            review,
            0,
            {
                "id": "improvement-closed-loop-001",
                "type": "capability_build",
            },
            {
                "status": "success",
                "source": "closed_loop_test",
            },
            {
                "artifact_id": "artifact-closed-loop-001",
                "task_id": str(task["id"]),
                "artifact_type": "capability",
                "location": "factory_closed_loop_test",
            },
        )

        report["lifecycle"] = lifecycle
        report["completion"] = completed
        report["decision"] = {
            "status": "PASS",
            "action": "authority_closed_loop_verified",
        }
    except Exception as exc:
        report["error"] = str(exc)
        report["decision"] = {
            "status": "FAILED",
            "action": "authority_closed_loop_error",
        }

    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
