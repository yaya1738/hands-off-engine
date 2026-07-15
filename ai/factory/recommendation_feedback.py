from typing import Any, Dict, List


class FactoryRecommendationFeedback:
    def __init__(self):
        self.recommendations: List[Dict[str, Any]] = []
        self.improvements: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def collect_recommendations(
        self,
        recommendations: Dict[str, Any],
    ):
        self.recommendations.append(recommendations)

        result = {
            "collected": True,
            "recommendations": recommendations,
        }

        self._history.append(result)

        return result

    def evaluate_recommendations(
        self,
        recommendations: Dict[str, Any],
    ):
        result = {
            "evaluated": True,
            "recommendations": recommendations,
        }

        self._history.append(result)

        return result

    def apply_improvement(
        self,
        improvement: Dict[str, Any],
    ):
        self.improvements.append(improvement)

        result = {
            "applied": True,
            "improvement": improvement,
        }

        self._history.append(result)

        return result

    def track_effect(
        self,
        effect: Dict[str, Any],
    ):
        result = {
            "tracked": True,
            "effect": effect,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
