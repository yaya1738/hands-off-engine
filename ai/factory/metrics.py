from typing import Any, Dict, List


class FactoryMetrics:
    def calculate(
        self,
        tasks: List[Dict[str, Any]],
        artifacts: List[Dict[str, Any]],
        verifications: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        total_tasks = len(tasks)

        completed = len(
            [
                task
                for task in tasks
                if task.get("status") == "COMPLETE"
            ]
        )

        passed = len(
            [
                item
                for item in verifications
                if item.get("status") == "PASS"
            ]
        )

        total_verifications = len(verifications)

        return {
            "tasks_total": total_tasks,
            "tasks_completed": completed,
            "artifact_count": len(artifacts),
            "verification_pass_rate": (
                passed / total_verifications
                if total_verifications
                else 0
            ),
        }
