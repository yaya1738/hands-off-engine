from typing import Any, Dict, List


class FactoryTrendAnalyzer:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def analyze(
        self,
        reports: List[Dict[str, Any]],
    ):
        total = len(reports)

        healthy = sum(
            1
            for report in reports
            if report.get("factory_health") == "healthy"
        )

        result = {
            "reports_analyzed": total,
            "healthy_reports": healthy,
            "stability": (
                "healthy"
                if total and healthy == total
                else "needs_review"
            ),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
