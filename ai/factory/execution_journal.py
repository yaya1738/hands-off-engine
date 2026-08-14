import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class FactoryExecutionJournal:
    """Durable intent lifecycle used to reconcile interrupted work after restart."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.environ.get(
            "FACTORY_EXECUTION_JOURNAL_PATH",
            os.path.join("state", "factory_execution_journal.json"),
        )
        self._entries: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self._entries = payload if isinstance(payload, list) else []
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self._entries = []

    def _persist(self) -> None:
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
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def record(self, execution_id: str, state: str, intent: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        entry = {
            "execution_id": execution_id,
            "state": state,
            "intent": intent or {},
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self._entries.append(entry)
        self._persist()
        return entry

    def latest(self, execution_id: str) -> Optional[Dict[str, Any]]:
        for entry in reversed(self._entries):
            if entry.get("execution_id") == execution_id:
                return entry
        return None

    def interrupted(self) -> List[Dict[str, Any]]:
        terminal = {"COMPLETED", "FAILED", "CANCELLED"}
        latest = {}
        for entry in self._entries:
            latest[entry.get("execution_id")] = entry
        return [entry for entry in latest.values() if entry.get("state") not in terminal]

    def history(self) -> List[Dict[str, Any]]:
        return list(self._entries)
