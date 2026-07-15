from typing import Any, Dict, List


class FactoryRuntimeLoop:
    def __init__(self):
        self.running = False
        self.cycles: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def start_cycle(
        self,
        context: Dict[str, Any],
    ):
        self.running = True

        result = {
            "started": True,
            "context": context,
        }

        self.cycles.append(
            result
        )

        self._history.append(
            result
        )

        return result

    def run_cycle(
        self,
        cycle: Dict[str, Any],
    ):
        result = {
            "completed": True,
            "cycle": cycle,
        }

        self._history.append(
            result
        )

        return result

    def pause_cycle(self):
        self.running = False

        result = {
            "paused": True,
        }

        self._history.append(
            result
        )

        return result

    def resume_cycle(self):
        self.running = True

        result = {
            "resumed": True,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
