from typing import Any, Dict, List


class FactoryKnowledgeIntelligence:
    def __init__(self):
        self.knowledge: Dict[str, Dict[str, Any]] = {}
        self.links: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def store_knowledge(
        self,
        key: str,
        knowledge: Dict[str, Any],
    ):
        self.knowledge[key] = knowledge

        result = {
            "stored": True,
            "key": key,
        }

        self._history.append(result)

        return result

    def retrieve_knowledge(
        self,
        key: str,
    ):
        result = {
            "retrieved": True,
            "key": key,
            "knowledge": self.knowledge.get(
                key,
                {}
            ),
        }

        self._history.append(result)

        return result

    def link_knowledge(
        self,
        source: str,
        target: str,
    ):
        link = {
            "source": source,
            "target": target,
        }

        self.links.append(link)

        result = {
            "linked": True,
            "link": link,
        }

        self._history.append(result)

        return result

    def search_knowledge(
        self,
        query: str,
    ):
        matches = [
            key
            for key in self.knowledge
            if query in key
        ]

        result = {
            "searched": True,
            "matches": matches,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
