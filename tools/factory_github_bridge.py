#!/usr/bin/env python3
"""Bridge a GitHub issue mailbox to the live Factory control channel.

The bridge uses the locally authenticated ``gh`` CLI; no GitHub credential is
stored in the repository. It is deliberately a transport adapter: commands are
only appended to the durable control channel, and the governed supervisor
remains the sole executor.

Command comment format:
    [factory-command] {"idempotency_key":"...","objective":"..."}

State comments are compact snapshots:
    [factory-state] {"status":"observed", ...}
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.factory_control_channel import append_command, compact_snapshot

COMMAND_PREFIX = "[factory-command]"
STATE_PREFIX = "[factory-state]"
DEFAULT_ISSUE = "272"
POLL_SECONDS = 30


def _gh_available() -> bool:
    return shutil.which("gh") is not None


def _gh_json(args: list[str]) -> Any:
    completed = subprocess.run(
        ["gh", "api", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return json.loads(completed.stdout or "null")


def _comments(repo: str, issue: str) -> list[dict[str, Any]]:
    value = _gh_json([f"repos/{repo}/issues/{issue}/comments", "--paginate"])
    return value if isinstance(value, list) else []


def _comment(repo: str, issue: str, body: str) -> None:
    subprocess.run(
        ["gh", "api", f"repos/{repo}/issues/{issue}/comments", "-f", f"body={body}"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _command_records(repo: str, issue: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in _comments(repo, issue):
        body = str(item.get("body") or "").strip()
        if not body.startswith(COMMAND_PREFIX):
            continue
        payload = body[len(COMMAND_PREFIX):].strip()
        try:
            command = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if not isinstance(command, dict) or not str(command.get("objective", "")).strip():
            continue
        command["source"] = "github_control_issue"
        command["metadata"] = {
            **(command.get("metadata") or {}),
            "github_issue": int(issue),
            "github_comment_id": item.get("id"),
        }
        records.append(command)
    return records


def _state_fingerprint(snapshot: dict[str, Any]) -> str:
    stable = {k: v for k, v in snapshot.items() if k not in {"observed_at", "fresh_until"}}
    return hashlib.sha256(json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run_once(repo: str, issue: str, publish_state: bool = True) -> dict[str, Any]:
    commands = _command_records(repo, issue)
    promoted = 0
    for command in commands:
        before = len(list((REPO_ROOT / "state" / "factory_control_commands.jsonl").open(encoding="utf-8"))) if (REPO_ROOT / "state" / "factory_control_commands.jsonl").exists() else 0
        append_command(
            REPO_ROOT,
            str(command["objective"]),
            source="github_control_issue",
            idempotency_key=str(command.get("idempotency_key") or ""),
            metadata=command.get("metadata"),
        )
        after = len(list((REPO_ROOT / "state" / "factory_control_commands.jsonl").open(encoding="utf-8"))) if (REPO_ROOT / "state" / "factory_control_commands.jsonl").exists() else before
        promoted += int(after > before)

    snapshot = compact_snapshot(REPO_ROOT)
    marker_path = REPO_ROOT / "state" / "factory_control_last_published_hash"
    previous = marker_path.read_text(encoding="utf-8").strip() if marker_path.exists() else ""
    fingerprint = _state_fingerprint(snapshot)
    if publish_state and fingerprint != previous:
        _comment(repo, issue, f"{STATE_PREFIX} {json.dumps(snapshot, sort_keys=True, separators=(',', ':'))}")
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(fingerprint + "\n", encoding="utf-8")
    return {"commands_seen": len(commands), "commands_promoted": promoted, "state_published": fingerprint != previous}


def main() -> int:
    if not _gh_available():
        print(json.dumps({"status": "unavailable", "reason": "gh CLI not installed"}, sort_keys=True))
        return 1
    repo = os.environ.get("GITHUB_REPOSITORY")
    issue = os.environ.get("FACTORY_CONTROL_ISSUE", DEFAULT_ISSUE)
    if not repo:
        print(json.dumps({"status": "unavailable", "reason": "GITHUB_REPOSITORY not set"}, sort_keys=True))
        return 1
    once = "--once" in sys.argv[1:]
    while True:
        try:
            result = run_once(repo, issue)
            print(json.dumps({"status": "ok", **result}, sort_keys=True), flush=True)
        except Exception as exc:
            print(json.dumps({"status": "degraded", "error": str(exc)}, sort_keys=True), flush=True)
        if once:
            return 0
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
