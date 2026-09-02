#!/usr/bin/env python3
"""Compatibility facade for the retired legacy activation controller.

The old implementation could execute arbitrary local modules, mutate remote
nodes with rsync, invoke doctl, run curl, and persist activation state. Those
are privileged operational actions and are now owned by the Factory authority.
This module remains only for read-only status compatibility.
"""

import json
from pathlib import Path
from typing import Dict

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / "state"
ACTIVATION_FILE = STATE_DIR / "full_activation.json"
MASTER = "Yair Siegel"


class FullActivation:
    """Read-only compatibility facade; never executes or mutates operations."""

    def __init__(self):
        self.state = self._load_state()
        self.results = {}

    def _load_state(self) -> Dict:
        if ACTIVATION_FILE.exists():
            try:
                return json.loads(ACTIVATION_FILE.read_text())
            except (OSError, json.JSONDecodeError):
                pass
        return {"master": MASTER, "last_activation": None, "modules_active": 0, "nodes_coordinated": 0}

    def get_status(self) -> Dict:
        return {
            "master": MASTER,
            "last_activation": self.state.get("last_activation"),
            "modules_active": self.state.get("modules_active", 0),
            "nodes_coordinated": self.state.get("nodes_coordinated", 0),
            "ready_for_capital": False,
            "authority": "FactoryAuthorityGateway",
        }

    def _disabled(self, operation: str) -> Dict:
        print(f"[FACTORY-AUTHORITY] Legacy full activation '{operation}' is disabled; use FactoryAuthorityGateway.")
        return {"success": False, "authority": "FactoryAuthorityGateway", "disabled": True}

    def activate_intelligence_gathering(self) -> Dict:
        return self._disabled("intelligence")

    def activate_preparation_mode(self) -> Dict:
        return self._disabled("preparation")

    def activate_node_coordination(self) -> Dict:
        return self._disabled("node coordination")

    def activate_protection_layers(self) -> Dict:
        return self._disabled("protection")

    def activate_income_generation(self) -> Dict:
        return self._disabled("income")

    def full_activation(self) -> Dict:
        return self._disabled("full")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Read-only activation status compatibility tool")
    parser.add_argument("command", choices=["status", "full", "intelligence", "preparation", "nodes", "protection", "income"])
    args = parser.parse_args()
    activation = FullActivation()

    if args.command == "status":
        print(json.dumps(activation.get_status(), indent=2))
        return

    operation = "node coordination" if args.command == "nodes" else args.command
    raise SystemExit(0 if activation._disabled(operation).get("disabled") is False else 1)


if __name__ == "__main__":
    main()
