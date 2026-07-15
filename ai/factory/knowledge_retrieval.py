from typing import Any, Dict, List


class FactoryKnowledgeRetrieval:
    def __init__(
        self,
        knowledge=None,
    ):
        self.knowledge = knowledge
        self._history: List[Dict[str, Any]] = []

    def retrieve_context(
        self,
        query: str = None,
    ):
        if self.knowledge:
            result = self.knowledge.query(
                query
            )

        else:
            result = []

        output = {
            "context": result,
        }

        self._history.append(
            output
        )

        return output

    def match(
        self,
        context: Dict[str, Any],
    ):
        result = {
            "matched": bool(
                context.get(
                    "context",
                    [],
                )
            ),
        }

        self._history.append(
            result
        )

        return result

    def enrich(
        self,
        decision: Dict[str, Any],
    ):
        result = {
            "decision": decision,
            "enriched": True,
        }

        self._history.append(
            result
        )

        return result

    def recommend(self):
        result = {
            "recommendation": "USE_KNOWLEDGE",
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
