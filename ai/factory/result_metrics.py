from typing import Any, Dict, List


class ResultMetrics:
    def calculate(
        self,
        results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        total = len(results)

        successful = len(
            [
                result
                for result in results
                if result.get("status") == "SUCCESS"
            ]
        )

        failed = len(
            [
                result
                for result in results
                if result.get("status") == "FAILED"
            ]
        )

        return {
            "jobs_total": total,
            "jobs_successful": successful,
            "jobs_failed": failed,
            "success_rate": (
                successful / total
                if total
                else 0
            ),
            "failure_rate": (
                failed / total
                if total
                else 0
            ),
        }

    def success_rate(
        self,
        results,
    ):
        return self.calculate(results)["success_rate"]

    def failure_rate(
        self,
        results,
    ):
        return self.calculate(results)["failure_rate"]
