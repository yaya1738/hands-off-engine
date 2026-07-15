from typing import Any, Dict, List


class FactoryEventReplay:
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def store_event(
        self,
        event: Dict[str, Any],
    ):
        self.events.append(event)

        result = {
            "stored": True,
            "event": event,
        }

        self._history.append(result)

        return result

    def query_events(
        self,
        event_type: str = None,
    ):
        if event_type is None:
            result_events = self.events
        else:
            result_events = [
                event
                for event in self.events
                if event.get("type") == event_type
            ]

        result = {
            "queried": True,
            "events": result_events,
        }

        self._history.append(result)

        return result

    def replay_execution(
        self,
        events: List[Dict[str, Any]],
    ):
        result = {
            "replayed": True,
            "count": len(events),
        }

        self._history.append(result)

        return result

    def diagnose_run(
        self,
        events: List[Dict[str, Any]],
    ):
        result = {
            "diagnosed": True,
            "event_count": len(events),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
