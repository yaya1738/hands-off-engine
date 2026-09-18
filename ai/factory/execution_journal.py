import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED"}
COMPACTION_EVENT_THRESHOLD = 512
COMPACTION_BYTES_THRESHOLD = 4 * 1024 * 1024


class FactoryExecutionJournal:
    """Durable intent lifecycle with append-oriented persistence.

    The snapshot remains the public storage format for compatibility. New
    lifecycle events are appended to a JSONL sidecar and periodically folded
    into the snapshot, avoiding an O(history) rewrite on every event.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.environ.get(
            "FACTORY_EXECUTION_JOURNAL_PATH",
            os.path.join("state", "factory_execution_journal.json"),
        )
        self.events_path = f"{self.storage_path}.events"
        self._entries: List[Dict[str, Any]] = []
        self._events_since_compaction = 0
        self._load()

    def _load(self) -> None:
        self._entries = []
        try:
            with open(self.storage_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, list):
                self._entries.extend(
                    entry for entry in payload if isinstance(entry, dict)
                )
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass

        try:
            with open(self.events_path, "r", encoding="utf-8") as handle:
                for line in handle:
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(entry, dict) and not self._contains(entry):
                        self._entries.append(entry)
                        self._events_since_compaction += 1
        except (FileNotFoundError, OSError):
            pass

    def _entry_key(self, entry: Dict[str, Any]) -> tuple:
        return (
            entry.get("execution_id"),
            entry.get("state"),
            entry.get("ts"),
        )

    def _contains(self, entry: Dict[str, Any]) -> bool:
        key = self._entry_key(entry)
        return any(self._entry_key(existing) == key for existing in self._entries)

    def _append_event(self, entry: Dict[str, Any]) -> None:
        directory = os.path.dirname(os.path.abspath(self.events_path))
        os.makedirs(directory, exist_ok=True)
        with open(self.events_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        self._events_since_compaction += 1

    def _compact(self) -> None:
        directory = os.path.dirname(os.path.abspath(self.storage_path))
        os.makedirs(directory, exist_ok=True)
        fd, temporary = tempfile.mkstemp(
            prefix=".execution-journal-", dir=directory, text=True
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self._entries, handle, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.storage_path)
            with open(self.events_path, "w", encoding="utf-8") as handle:
                handle.flush()
                os.fsync(handle.fileno())
            self._events_since_compaction = 0
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _persist(self, entry: Optional[Dict[str, Any]] = None) -> None:
        if entry is not None:
            self._append_event(entry)
        if self._events_since_compaction >= COMPACTION_EVENT_THRESHOLD:
            self._compact()
        elif (
            os.path.exists(self.events_path)
            and os.path.getsize(self.events_path) >= COMPACTION_BYTES_THRESHOLD
        ):
            self._compact()

    def find_by_idempotency_key(
        self, idempotency_key: str
    ) -> Optional[Dict[str, Any]]:
        """Return the latest lifecycle entry carrying a caller-supplied idempotency key."""
        key = str(idempotency_key).strip()
        if not key:
            return None
        for entry in reversed(self._entries):
            intent = entry.get("intent")
            if isinstance(intent, dict) and intent.get("idempotency_key") == key:
                return entry
        return None

    def record(
        self,
        execution_id: str,
        state: str,
        intent: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Append a lifecycle event, rejecting illegal duplicate terminal events."""
        if not execution_id or state not in {"STARTED", *TERMINAL_STATES}:
            raise ValueError("invalid execution lifecycle event")
        previous = self.latest(execution_id)
        if previous is not None:
            previous_state = previous.get("state")
            allowed = (
                previous_state == "STARTED" and state in TERMINAL_STATES
            )
            if previous_state in TERMINAL_STATES or not allowed:
                raise ValueError(
                    f"illegal execution lifecycle transition: {previous_state} -> {state}"
                )
        entry = {
            "execution_id": execution_id,
            "state": state,
            "intent": intent or {},
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self._entries.append(entry)
        self._persist(entry)
        return entry

    def latest(self, execution_id: str) -> Optional[Dict[str, Any]]:
        for entry in reversed(self._entries):
            if entry.get("execution_id") == execution_id:
                return entry
        return None

    def interrupted(self) -> List[Dict[str, Any]]:
        latest = {}
        for entry in self._entries:
            latest[entry.get("execution_id")] = entry
        return [
            entry
            for entry in latest.values()
            if entry.get("state") not in TERMINAL_STATES
        ]

    def history(self) -> List[Dict[str, Any]]:
        return list(self._entries)
