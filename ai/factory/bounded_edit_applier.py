from pathlib import Path
from typing import Any, Dict


class BoundedEditApplier:
    """Apply only explicitly authorized text replacements inside a workspace."""

    def __init__(self, workspace: str):
        self.workspace = Path(workspace).resolve()

    def _path(self, relative_path: str) -> Path:
        path = Path(relative_path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unauthorized path: {relative_path}")
        target = (self.workspace / path).resolve()
        try:
            target.relative_to(self.workspace)
        except ValueError as exc:
            raise ValueError(f"unauthorized path: {relative_path}") from exc
        return target

    def apply(self, edit: Dict[str, Any], allowed_paths) -> Dict[str, Any]:
        path = edit.get("path")
        if path not in set(allowed_paths):
            raise PermissionError(f"path not authorized: {path}")
        if edit.get("operation") != "replace_text":
            raise ValueError("unsupported edit operation")
        target = self._path(path)
        original = target.read_text()
        old = edit.get("old")
        new = edit.get("new")
        if not isinstance(old, str) or not isinstance(new, str):
            raise TypeError("edit old/new values must be strings")
        if original.count(old) != 1:
            raise ValueError("edit must match exactly one existing occurrence")
        target.write_text(original.replace(old, new, 1))
        return {"status": "applied", "path": path}
