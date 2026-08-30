"""Bounded JSON extraction and schema validation for Ollama canary edits.

Extracted from .github/workflows/factory-ollama-canary.yml (commit 5226635)
so the same validated logic can run outside GitHub Actions (self-hosted).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def strip_ansi(raw: str) -> str:
    return _ANSI_RE.sub("", raw)


def extract_authorized_edit(
    raw: str,
    allowed_path: str,
    allowed_contents: set[str],
) -> Optional[dict]:
    """Scan raw model output for the first JSON object matching the
    authorized {path, content} schema. Returns None if none found.

    Models can repeat, truncate, or fence JSON output, so every
    plausible object start is scanned and only an exact bounded
    schema match is accepted.
    """
    raw = strip_ansi(raw)
    decoder = json.JSONDecoder()

    for match in re.finditer(r"\{", raw):
        try:
            candidate, _ = decoder.raw_decode(raw[match.start():])
        except json.JSONDecodeError:
            continue
        if not isinstance(candidate, dict):
            continue
        if set(candidate) != {"path", "content"}:
            continue
        if candidate.get("path") != allowed_path:
            continue
        if candidate.get("content") not in allowed_contents:
            continue
        return candidate
    return None


def apply_edit(
    data: dict,
    write_content: str,
    *,
    allowed_path: str,
    allowed_contents: set[str],
) -> Path:
    """Apply only an edit that independently satisfies the authority contract.

    Keep the policy check at the write boundary so callers cannot accidentally
    turn this helper into an arbitrary filesystem writer by skipping extraction.
    """
    if set(data) != {"path", "content"}:
        raise ValueError("Unauthorized edit schema")
    if data.get("path") != allowed_path:
        raise ValueError(f"Unauthorized edit path: {data.get('path')!r}")
    if data.get("content") not in allowed_contents:
        raise ValueError("Unauthorized edit content")
    if write_content not in allowed_contents or write_content != data["content"]:
        raise ValueError("Write content does not match authorized content")

    target = Path(data["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(write_content)
    return target


def verify_result(path: str, expected_content: str) -> bool:
    p = Path(path)
    if not p.is_file():
        return False
    return p.read_text() == expected_content
