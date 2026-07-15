from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryPostIncidentLearning:
    def __init__(self):
        self._lessons: List[Dict[str, Any]] = []

    def extract(
        self,
        incident: Dict[str, Any],
    ):
        lesson = {
            "lesson": incident.get(
                "lesson",
                "no lesson recorded",
            ),
            "source": "incident",
            "confidence": 0.9,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        return lesson

    def store(
        self,
        lesson: Dict[str, Any],
    ):
        self._lessons.append(
            lesson
        )

        return lesson

    def learn(
        self,
        incident: Dict[str, Any],
    ):
        lesson = self.extract(
            incident
        )

        return self.store(
            lesson
        )

    def history(self):
        return self._lessons
