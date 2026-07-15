from typing import Any, Dict, List


class FactoryKnowledgeGraph:
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.relationships: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def add_node(
        self,
        node_id: str,
        data: Dict[str, Any],
    ):
        self.nodes[node_id] = data

        result = {
            "added": True,
            "node": node_id,
        }

        self._history.append(
            result
        )

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
            "connected": True,
            "relationship": relationship,
        }

        self._history.append(
            result
        )

        return result

    def find_connections(
        self,
        node_id: str,
    ):
        result = {
            "connections": [
                r
                for r in self.relationships
                if r["source"] == node_id
                or r["target"] == node_id
            ],
        }

        self._history.append(
            result
        )

        return result

    def query_graph(self):
        result = {
            "nodes": self.nodes,
            "relationships": self.relationships,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
