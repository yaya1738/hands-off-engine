"""Bounded JSON extraction and schema validation for Ollama canary edits."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def strip_ansi(raw: str) -> str:
    return _ANSI_RE.sub("", raw)


def extract_authorized_edit(raw: str, allowed_path: str, allowed_contents: set[str]) -> Optional[dict]:
    raw = strip_ansi(raw)
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", raw):
        try:
            candidate, _ = decoder.raw_decode(raw[match.start():])
        except json.JSONDecodeError:
            continue
        if not isinstance(candidate, dict) or set(candidate) != {"path", "content"}:
            continue
        if candidate.get("path") == allowed_path and candidate.get("content") in allowed_contents:
            return candidate
    return None


def apply_edit(data: dict, write_content: str, *, allowed_path: str, allowed_contents: set[str]) -> Path:
    if set(data) != {"path", "content"}:
        raise ValueError("Unauthorized edit schema")
    if data.get("path") != allowed_path:
        raise ValueError("Unauthorized edit path")
    if data.get("content") not in allowed_contents or write_content != data["content"] or write_content not in allowed_contents:
        raise ValueError("Unauthorized edit content")
    target = Path(data["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(write_content)
    return target


def verify_result(path: str, expected_content: str) -> bool:
    p = Path(path)
    return p.is_file() and p.read_text() == expected_content
