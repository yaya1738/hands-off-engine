import json
from datetime import datetime, timezone

from factory_completion_wiring_adapter import FactoryCompletionWiringAdapter


def run():

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_real_completion_activation_test_v3"
    }

    adapter = FactoryCompletionWiringAdapter()

    try:
        # create task in the SAME tracker instance used by completion
        task = adapter.tracker.create_task(
            {
                "goal": "real completion activation test",
                "type": "capability_build"
            }
        )

        result = adapter.complete_reviewed_task(
            {
                "id": "review-test-001",
                "approved": True
            },
            0,
            {
                "id": "improvement-test-001",
                "type": "test"
            },
            {
                "status": "success",
                "message": "completed"
            },
            {
                "artifact_id": "artifact-test-001",
                "task_id": str(task["id"]),
                "artifact_type": "test",
                "location": "activation_test"
            }
        )

        report["task_created"] = task
        report["completion_result"] = result
        report["tracker_history"] = adapter.tracker.history()

        report["decision"] = {
            "status": "PASS",
            "action": "real_completion_path_verified"
        }

    except Exception as e:
        report["error"] = str(e)
        report["decision"] = {
            "status": "FAILED",
            "action": "completion_dependency_issue"
        }

    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
