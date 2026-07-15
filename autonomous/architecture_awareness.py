#!/usr/bin/env python3
"""
🏗️ ARCHITECTURE AWARENESS - System Self-Understanding
Serving: Yair Siegel

The system understands its own architecture and can explain
how components relate to each other.

This module provides runtime introspection of:
- What components exist
- How they connect
- What data flows between them
- Current state of each component
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = BASE_DIR / "state"
ARCH_FILE = STATE_DIR / "SYSTEM_ARCHITECTURE.json"


class ArchitectureMap:
    """
    Runtime map of system architecture.
    Used by all components to understand their context.
    """

    def __init__(self):
        self.architecture = self._load_architecture()

    def _load_architecture(self) -> Dict:
        if ARCH_FILE.exists():
            return json.loads(ARCH_FILE.read_text())
        return {}

    def get_component_role(self, component_name: str) -> str:
        """What does this component do?"""
        layers = self.architecture.get("architecture", {}).get("layers", {})
        for layer_name, layer in layers.items():
            if component_name in layer.get("component", ""):
                return layer.get("role", "Unknown role")

        processes = self.architecture.get("architecture", {}).get("processes", {})
        for category, procs in processes.items():
            if component_name in procs:
                return procs[component_name].get("purpose", "Unknown purpose")

        return "Component not found in architecture"

    def get_component_connections(self, component_name: str) -> Dict:
        """What does this component connect to?"""
        connections = self.architecture.get("architecture", {}).get("connections", {})
        return connections.get(component_name, {})

    def get_data_flow(self, flow_name: str) -> List[str]:
        """How does data flow for this process?"""
        flows = self.architecture.get("architecture", {}).get("data_flows", {})
        return flows.get(flow_name, [])

    def get_endpoint_for_action(self, action: str) -> Dict:
        """What endpoint handles this action?"""
        processes = self.architecture.get("architecture", {}).get("processes", {})
        for category, procs in processes.items():
            if action in procs:
                return {"category": category, **procs[action]}
        return {}

    def get_external_connection(self, name: str) -> Dict:
        """Get details about an external connection."""
        return self.architecture.get("external_connections", {}).get(name, {})

    def explain_system(self) -> str:
        """Generate a natural language explanation of the system."""
        arch = self.architecture

        explanation = []
        explanation.append(f"SYSTEM ARCHITECTURE - Serving {arch.get('master', 'Unknown')}")
        explanation.append(f"Purpose: {arch.get('purpose', 'Unknown')}")
        explanation.append("")

        # Layers
        explanation.append("LAYERS:")
        layers = arch.get("architecture", {}).get("layers", {})
        for name, layer in layers.items():
            explanation.append(f"  {name.upper()}: {layer.get('role', '')}")
            explanation.append(f"    Component: {layer.get('component', '')}")

        explanation.append("")

        # Data flows
        explanation.append("DATA FLOWS:")
        flows = arch.get("architecture", {}).get("data_flows", {})
        for name, steps in flows.items():
            explanation.append(f"  {name}: {' → '.join(steps) if isinstance(steps, list) else steps}")

        explanation.append("")

        # External connections
        explanation.append("EXTERNAL CONNECTIONS:")
        external = arch.get("external_connections", {})
        for name, conn in external.items():
            explanation.append(f"  {name}: {conn.get('purpose', '')} via {conn.get('endpoint', '')}")

        return "\n".join(explanation)

    def get_component_state(self, component_name: str) -> Dict:
        """Get current state of a component from its state file."""
        # Find state file for this component
        layers = self.architecture.get("architecture", {}).get("layers", {})
        for layer in layers.values():
            if component_name in layer.get("component", ""):
                state_file = BASE_DIR / layer.get("state_file", "")
                if state_file.exists():
                    try:
                        return json.loads(state_file.read_text())
                    except:
                        pass

        processes = self.architecture.get("architecture", {}).get("processes", {})
        for category, procs in processes.items():
            for name, proc in procs.items():
                if component_name == name:
                    feedback_file = BASE_DIR / proc.get("feedback", "")
                    if feedback_file.exists():
                        try:
                            if feedback_file.suffix == ".jsonl":
                                lines = feedback_file.read_text().strip().split("\n")
                                if lines and lines[-1]:
                                    return json.loads(lines[-1])
                            else:
                                return json.loads(feedback_file.read_text())
                        except:
                            pass

        return {"error": "State not found"}

    def get_system_health(self) -> Dict:
        """Get health status of all components."""
        health = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {},
        }

        # Check layers
        layers = self.architecture.get("architecture", {}).get("layers", {})
        for name, layer in layers.items():
            state_file = BASE_DIR / layer.get("state_file", "")
            health["components"][name] = {
                "exists": state_file.exists(),
                "component": layer.get("component"),
            }

        # Check processes
        processes = self.architecture.get("architecture", {}).get("processes", {})
        for category, procs in processes.items():
            for name, proc in procs.items():
                if "feedback" in proc:
                    feedback_file = BASE_DIR / proc["feedback"]
                    health["components"][name] = {
                        "category": category,
                        "exists": feedback_file.exists(),
                    }

        return health

    def get_connection_graph(self) -> Dict:
        """Get a graph representation of component connections."""
        graph = {"nodes": [], "edges": []}

        # Add layer nodes
        layers = self.architecture.get("architecture", {}).get("layers", {})
        for name, layer in layers.items():
            graph["nodes"].append({
                "id": name,
                "type": "layer",
                "label": layer.get("component", name),
            })

        # Add process nodes
        processes = self.architecture.get("architecture", {}).get("processes", {})
        for category, procs in processes.items():
            for name, proc in procs.items():
                graph["nodes"].append({
                    "id": name,
                    "type": "process",
                    "category": category,
                    "label": proc.get("script", proc.get("actuator", name)),
                })

        # Add edges from connections
        connections = self.architecture.get("architecture", {}).get("connections", {})
        for component, conn in connections.items():
            for target in conn.get("calls", []):
                graph["edges"].append({
                    "from": component,
                    "to": target.split(".")[0] if "." in target else target,
                    "type": "calls",
                })

        return graph


def inject_architecture_awareness(component_name: str) -> Dict:
    """
    Inject architecture awareness into a component.
    Returns context about the component's role and connections.
    """
    arch = ArchitectureMap()

    return {
        "component": component_name,
        "role": arch.get_component_role(component_name),
        "connections": arch.get_component_connections(component_name),
        "current_state": arch.get_component_state(component_name),
        "system_context": {
            "master": arch.architecture.get("master"),
            "objectives": arch.architecture.get("always_objectives", []),
        },
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Architecture Awareness")
    parser.add_argument("command", choices=["explain", "health", "component", "graph", "connections"])
    parser.add_argument("--name", help="Component name for component/connections commands")

    args = parser.parse_args()

    arch = ArchitectureMap()

    if args.command == "explain":
        print(arch.explain_system())

    elif args.command == "health":
        health = arch.get_system_health()
        print(json.dumps(health, indent=2))

    elif args.command == "component":
        if not args.name:
            print("Error: --name required")
            return
        context = inject_architecture_awareness(args.name)
        print(json.dumps(context, indent=2))

    elif args.command == "graph":
        graph = arch.get_connection_graph()
        print(json.dumps(graph, indent=2))

    elif args.command == "connections":
        if not args.name:
            print("Error: --name required")
            return
        conn = arch.get_component_connections(args.name)
        print(json.dumps(conn, indent=2))


if __name__ == "__main__":
    main()
