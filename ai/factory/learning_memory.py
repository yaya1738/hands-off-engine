from typing import Any, Dict, List


class FactoryLearningMemory:
    def __init__(self):
        self._memory: List[Dict[str, Any]] = []

    def store(
        self,
        experience: Dict[str, Any],
    ):
        self._memory.append(
            experience
        )

        return experience

    def recall(
        self,
        key: str,
        value: Any,
    ):
        return [
            item
            for item in self._memory
            if item.get(key) == value
        ]

    def patterns(self):
        patterns = {}

        for item in self._memory:
            action = item.get(
                "action",
                "unknown",
            )

            patterns[action] = (
                patterns.get(
                    action,
                    0,
                ) + 1
            )

        return patterns

    def history(self):
        return self._memory
