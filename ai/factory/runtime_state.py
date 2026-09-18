from typing import Any, Dict, List, Optional
import copy
import json
import os
import tempfile


class FactoryRuntimeState:
    """Durable runtime state with the original in-memory API preserved."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.environ.get(
            "FACTORY_RUNTIME_STATE_PATH",
            os.path.join("state", "factory_runtime_state.json"),
        )
        self.state: Dict[str, Any] = {}
        self._snapshots: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.state = copy.deepcopy(payload.get("state", {}))
            # History can be large and is already deserialized from trusted JSON.
            # Avoid recursively copying the entire historical record on every load.
            history = payload.get("history", [])
            self._history = list(history) if isinstance(history, list) else []
            snapshots = payload.get("snapshots", [])
            self._snapshots = list(snapshots) if isinstance(snapshots, list) else []
        except FileNotFoundError:
            return
        except (OSError, ValueError, TypeError):
            return

    def _persist(self) -> None:
        directory = os.path.dirname(os.path.abspath(self.storage_path))
        os.makedirs(directory, exist_ok=True)
        payload = {
            "state": self.state,
            "snapshots": self._snapshots,
            "history": self._history,
        }
        fd, temporary_path = tempfile.mkstemp(
            prefix=".factory_runtime_state-",
            suffix=".tmp",
            dir=directory,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.storage_path)
        finally:
            if os.path.exists(temporary_path):
                os.unlink(temporary_path)

    def save_state(self, state: Dict[str, Any]):
        self.state = copy.deepcopy(state)
        result = {"saved": True, "state": self.state}
        self._history.append(result)
        self._persist()
        return result

    def load_state(self):
        self._load_from_disk()
        return {"loaded": True, "state": copy.deepcopy(self.state)}

    def snapshot(self):
        snapshot = copy.deepcopy(self.state)
        self._snapshots.append(snapshot)
        result = {"snapshotted": True, "snapshot": snapshot}
        self._history.append(result)
        self._persist()
        return result

    def restore(self, snapshot: Dict[str, Any]):
        self.state = copy.deepcopy(snapshot)
        result = {"restored": True, "state": self.state}
        self._history.append(result)
        self._persist()
        return result

    def history(self):
        return self._history
