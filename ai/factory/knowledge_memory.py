from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryKnowledgeMemory:
    def __init__(self):
        self._memory: List[Dict[str, Any]] = []

    def store(
        self,
        lesson: str,
        source: str,
        confidence: float = 0,
        metadata=None,
    ):
        entry = {
            "lesson": lesson,
            "source": source,
            "confidence": confidence,
            "metadata": metadata or {},
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self._memory.append(entry)

        return entry

    def query(
        self,
        term: str,
    ):
        return [
            item
            for item in self._memory
            if term.lower()
            in item["lesson"].lower()
        ]

    def learn(
        self,
        entries,
    ):
        for entry in entries:
            self._memory.append(entry)

        return len(entries)

    def snapshot(self):
        return list(self._memory)
