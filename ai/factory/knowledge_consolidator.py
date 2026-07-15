from typing import Any, Dict, List


class FactoryKnowledgeConsolidator:
    def __init__(self):
        self._lessons: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def add_lesson(
        self,
        lesson: Dict[str, Any],
    ):
        self._lessons.append(
            lesson
        )

        return lesson

    def find_patterns(self):
        patterns: Dict[str, int] = {}

        for lesson in self._lessons:
            text = lesson.get(
                "lesson",
                "",
            )

            patterns[text] = (
                patterns.get(text, 0)
                + 1
            )

        return patterns

    def consolidate(self):
        patterns = self.find_patterns()

        result = {
            "patterns": patterns,
            "count": len(patterns),
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
