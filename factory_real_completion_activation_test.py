import json
from datetime import datetime, timezone

from factory_completion_wiring_adapter import FactoryCompletionWiringAdapter


def run():

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_real_completion_activation_test"
    }

    adapter = FactoryCompletionWiringAdapter()

    test_request = {
        "id": "test-review-001",
        "approved": True
    }

    test_improvement = {
        "id": "test-improvement-001",
        "type": "capability_build"
    }

    test_result = {
        "status": "success",
        "message": "activation test"
    }

    test_artifact = {
        "artifact_id": "test-artifact-001",
        "task_id": "test-task-001",
        "artifact_type": "test_utility",
        "location": "test"
    }

    try:
        result = adapter.complete_reviewed_task(
            test_request,
            0,
            test_improvement,
            test_result,
            test_artifact
        )

        report["execution"] = {
            "status": "success",
            "result": result
        }

        report["decision"] = {
            "status": "PASS",
            "action": "real_completion_path_executed"
        }

    except Exception as e:

        report["execution"] = {
            "status": "failed",
            "error": str(e)
        }

        report["decision"] = {
            "status": "FAILED",
            "action": "completion_contract_issue"
        }

    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
