import json
from typing import Any, Dict


class AgentResultValidator:
    """Normalize untrusted local-agent output into the bounded edit contract."""

    REQUIRED = {"path", "operation", "old", "new"}

    @classmethod
    def validate(cls, raw: Any, allowed_paths) -> Dict[str, str]:
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError("agent response is not valid JSON") from exc

        if not isinstance(raw, dict):
            raise TypeError("agent result must be a JSON object")

        if set(raw) != cls.REQUIRED:
            raise ValueError("agent edit must contain exactly path, operation, old, and new")

        path = raw["path"]
        operation = raw["operation"]
        old = raw["old"]
        new = raw["new"]

        if not isinstance(path, str) or not path:
            raise TypeError("edit path must be a non-empty string")
        if path not in set(allowed_paths):
            raise PermissionError(f"path not authorized: {path}")
        if operation != "replace_text":
            raise ValueError("unsupported edit operation")
        if not isinstance(old, str) or not isinstance(new, str):
            raise TypeError("edit old/new values must be strings")
        if not old:
            raise ValueError("edit old value must be non-empty")

        return {"path": path, "operation": operation, "old": old, "new": new}
