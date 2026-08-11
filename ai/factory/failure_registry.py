from typing import Any, Dict, List
from pathlib import Path
import hashlib
import json


class FactoryFailureRegistry:

    def __init__(self):
        self._failures: List[Dict[str, Any]] = []
        self.state_path = Path(
            "state/factory_failure_registry.json"
        )
        self._load()


    def _load(self):
        if not self.state_path.exists():
            return

        try:
            self._failures = json.loads(
                self.state_path.read_text()
            )
        except Exception:
            self._failures = []

    def _persist(self):
        self.state_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.state_path.write_text(
            json.dumps(
                self._failures,
                indent=2,
            )
        )

    def fingerprint(self, failure: Dict[str, Any]) -> str:
        raw = str(
            sorted(failure.items())
        )
        return hashlib.sha256(
            raw.encode()
        ).hexdigest()

    def record_failure(self, failure: Dict[str, Any]):
        fingerprint = self.fingerprint(failure)

        existing = self.find(
            fingerprint
        )

        if existing:
            existing["count"] += 1
            existing["last_status"] = failure.get(
                "status"
            )

            if existing.get("status") == "RESOLVED":
                existing["status"] = "ACTIVE"
                existing.pop("resolution", None)

            self._failures.remove(existing)
            self._failures.append(existing)

            self._persist()
            return existing

        entry = {
            "fingerprint": fingerprint,
            "failure": failure,
            "count": 1,
            "status": "ACTIVE",
        }

        self._failures.append(entry)
        self._persist()

        return entry

    def resolve(
        self,
        fingerprint: str,
        outcome: Dict[str, Any],
    ):
        item = self.find(fingerprint)

        if item:
            item["status"] = "RESOLVED"
            item["resolution"] = outcome
            self._persist()

        return item

    def find(self, fingerprint: str):
        for item in self._failures:
            if item["fingerprint"] == fingerprint:
                return item

        return None

    def history(self):
        return self._failures
