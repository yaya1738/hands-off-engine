from typing import Any, Dict, List


class FactoryKnowledgeRetrieval:
    def __init__(
        self,
        memory,
    ):
        self.memory = memory

    def retrieve(
        self,
        query: str,
    ):
        return self.memory.query(
            query
        )

    def rank(
        self,
        entries: List[Dict[str, Any]],
    ):
        return sorted(
            entries,
            key=lambda item: item.get(
                "confidence",
                0,
            ),
            reverse=True,
        )

    def recommend(
        self,
        query: str,
    ):
        matches = self.retrieve(
            query
        )

        ranked = self.rank(
            matches
        )

        return ranked[0] if ranked else None
