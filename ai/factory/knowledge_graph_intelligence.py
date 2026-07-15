from typing import Any, Dict, List


class FactoryKnowledgeGraphIntelligence:
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.relationships: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def add_node(
        self,
        name: str,
        data: Dict[str, Any],
    ):
        self.nodes[name] = data

        result = {
            "added": True,
            "node": name,
        }

        self._history.append(result)

        return result

    def add_relationship(
        self,
        source: str,
        target: str,
        relation: str,
    ):
        relationship = {
            "source": source,
            "target": target,
            "relation": relation,
        }

        self.relationships.append(
            relationship
        )

        result = {
            "linked": True,
            "relationship": relationship,
        }

        self._history.append(result)

        return result

    def traverse_graph(
        self,
        node: str,
    ):
        result = {
            "traversed": True,
            "node": node,
        }

        self._history.append(result)

        return result

    def find_connections(
        self,
        node: str,
    ):
        connections = [
            r
            for r in self.relationships
            if r["source"] == node
            or r["target"] == node
        ]

        result = {
            "found": True,
            "connections": connections,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
