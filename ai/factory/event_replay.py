import json
import os
import tempfile
from typing import Any, Dict, List, Optional


class FactoryEventReplay:
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.environ.get(
            "FACTORY_EVENT_REPLAY_PATH",
            "state/factory_event_replay.jsonl",
        )
        self.events: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            with open(self.storage_path, "r", encoding="utf-8") as handle:
                self.events = [
                    json.loads(line)
                    for line in handle
                    if line.strip()
                ]
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self.events = []

    def _persist(self):
        directory = os.path.dirname(os.path.abspath(self.storage_path))
        os.makedirs(directory, exist_ok=True)
        fd, temporary_path = tempfile.mkstemp(
            prefix=".factory-event-replay-",
            dir=directory,
            text=True,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                for event in self.events:
                    handle.write(json.dumps(event, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.storage_path)
        finally:
            if os.path.exists(temporary_path):
                os.unlink(temporary_path)

    def store_event(self, event: Dict[str, Any]):
        self.events.append(event)
        self._persist()

        result = {
            "stored": True,
            "event": event,
        }
        self._history.append(result)
        return result

    def query_events(self, event_type: str = None):
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

    def replay_execution(self, events: List[Dict[str, Any]]):
        result = {
            "replayed": True,
            "count": len(events),
        }
        self._history.append(result)
        return result

    def diagnose_run(self, events: List[Dict[str, Any]]):
        result = {
            "diagnosed": True,
            "event_count": len(events),
        }
        self._history.append(result)
        return result

    def history(self):
        return self._history
