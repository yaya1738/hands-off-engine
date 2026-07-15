from typing import Any, Dict, List


class FactoryRecoveryLearning:
    def analyze(
        self,
        history: List[Dict[str, Any]],
    ):
        total = len(history)

        recovered = len(
            [
                item
                for item in history
                if item.get("status")
                == "RECOVERED"
            ]
        )

        failed = total - recovered

        return {
            "total_recoveries": total,
            "successful": recovered,
            "failed": failed,
            "success_rate": (
                recovered / total
                if total
                else 0
            ),
        }

    def success_rate(
        self,
        history,
    ):
        return self.analyze(
            history
        )["success_rate"]

    def recommend(
        self,
        history,
    ):
        rate = self.success_rate(
            history
        )

        if rate >= 0.9:
            return "allow_auto_recovery"

        if rate >= 0.5:
            return "limited_recovery"

        return "require_review"
