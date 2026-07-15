from typing import Any, Dict, List


class FactoryKnowledgeRetrieval:
    def __init__(
        self,
        knowledge=None,
    ):
        self.knowledge = knowledge or []
        self._history: List[Dict[str, Any]] = []

    def search(
        self,
        query: Any,
    ):
        result = {
            "matches": [
                item
                for item in self.knowledge
                if query in str(item)
            ],
        }

        self._history.append(
            result
        )

        return result

    def match_context(
        self,
        context: Dict[str, Any],
    ):
        result = {
            "matched": True,
            "context": context,
        }

        self._history.append(
            result
        )

        return result

    def recommend(self):
        result = {
            "recommendation": (
                self.knowledge[0]
                if self.knowledge
                else None
            ),
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
