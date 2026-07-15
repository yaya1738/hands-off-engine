from typing import Any, Dict, List


class FactoryRecommendationEngine:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def recommend(
        self,
        patterns: Dict[str, int],
    ):
        if not patterns:
            result = {
                "recommendation": "NONE",
                "confidence": 0,
                "reason": "no_patterns",
            }

        else:
            pattern = max(
                patterns,
                key=patterns.get,
            )

            frequency = patterns[pattern]

            result = {
                "recommendation": (
                    f"automate: {pattern}"
                ),
                "confidence": min(
                    frequency / 10,
                    1,
                ),
                "reason": (
                    "repeated_pattern"
                ),
            }

        self._history.append(
            result
        )

        return result

    def rank(
        self,
        recommendations,
    ):
        return sorted(
            recommendations,
            key=lambda item: item.get(
                "confidence",
                0,
            ),
            reverse=True,
        )

    def history(self):
        return self._history
