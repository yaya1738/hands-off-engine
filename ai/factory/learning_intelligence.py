from typing import Any, Dict, List


class FactoryLearningIntelligence:
    def __init__(self):
        self.experiences: List[Dict[str, Any]] = []
        self.models: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def record_experience(
        self,
        experience: Dict[str, Any],
    ):
        self.experiences.append(experience)

        result = {
            "recorded": True,
            "experience": experience,
        }

        self._history.append(result)

        return result

    def analyze_outcome(
        self,
        outcome: Dict[str, Any],
    ):
        result = {
            "analyzed": True,
            "outcome": outcome,
        }

        self._history.append(result)

        return result

    def extract_lesson(
        self,
        data: Dict[str, Any],
    ):
        result = {
            "extracted": True,
            "lesson": data,
        }

        self._history.append(result)

        return result

    def update_model(
        self,
        name: str,
        update: Dict[str, Any],
    ):
        self.models[name] = update

        result = {
            "updated": True,
            "model": name,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
