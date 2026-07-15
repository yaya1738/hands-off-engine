from typing import Any, Dict, List


class FactoryMasterIntegration:
    def __init__(self):
        self.components: Dict[str, Any] = {}
        self.initialized = False
        self.cycles = 0
        self._history: List[Dict[str, Any]] = []

    def register_component(
        self,
        name: str,
        component: Any,
    ):
        self.components[name] = component

        result = {
            "registered": True,
            "component": name,
        }

        self._history.append(result)

        return result

    def initialize_system(self):
        self.initialized = True

        result = {
            "initialized": True,
            "components": len(
                self.components
            ),
        }

        self._history.append(result)

        return result

    def run_cycle(self):
        self.cycles += 1

        result = {
            "ran": True,
            "cycle": self.cycles,
        }

        self._history.append(result)

        return result

    def get_system_status(self):
        result = {
            "initialized": self.initialized,
            "components": len(
                self.components
            ),
            "cycles": self.cycles,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
