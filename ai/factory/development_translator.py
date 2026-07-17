from typing import Any, Dict, List


class FactoryDevelopmentTranslator:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def translate(
        self,
        result: Dict[str, Any],
    ):
        gaps = []

        if not result.get("success", True):
            gaps.append(
                "execution reliability"
            )

        steps = result.get(
            "steps_completed",
            [],
        )

        if "recovered" in steps:
            gaps.append(
                "failure recovery workflow"
            )

        translated = {
            "gaps": gaps,
        }

        self._history.append(
            translated
        )

        return translated

    def history(self):
        return self._history
