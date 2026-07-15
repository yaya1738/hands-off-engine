from typing import Any, Dict, List


class FactoryKnowledgeBase:
    def __init__(
        self,
        memory=None,
    ):
        self.memory = memory
        self.knowledge: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def extract(self):
        if self.memory:
            source = self.memory.retrieve()

        else:
            source = []

        result = {
            "patterns_found": len(source),
        }

        self.knowledge.append(
            result
        )

        self._history.append(
            result
        )

        return result

    def summarize(self):
        result = {
            "knowledge_items": len(
                self.knowledge
            ),
        }

        self._history.append(
            result
        )

        return result

    def query(
        self,
        term: str = None,
    ):
        if term is None:
            result = self.knowledge

        else:
            result = [
                item
                for item in self.knowledge
                if term in str(item)
            ]

        self._history.append(
            {
                "query": term,
                "results": result,
            }
        )

        return result

    def confidence(self):
        result = {
            "confidence": (
                len(self.knowledge) > 0
            ),
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
