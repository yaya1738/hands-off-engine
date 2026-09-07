#!/usr/bin/env python3
"""Turn authenticated GitHub issues into durable autonomous work.

This is a production fallback control surface for environments where the
original host is unavailable. Only repository-authenticated users who can
create issues can submit work, and requests must explicitly use the
``[autonomous]`` title prefix. The governed supervisor remains the only
execution authority.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


# When executed as ``python tools/github_issue_autonomous_ingress.py``, Python
# puts ``tools/`` on sys.path rather than the repository root. Resolve the
# root explicitly so the durable queue import works identically in Actions,
# local execution, and module-based tests.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.autonomous_task_queue import AutonomousTaskQueue


API = "https://api.github.com"
PREFIX = "[autonomous]"


def _request(path: str, token: str) -> object:
    request = urllib.request.Request(
        f"{API}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "hands-off-autonomous-ingress",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def _mutate(path: str, token: str, payload: dict) -> object:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{API}{path}",
        data=body,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "hands-off-autonomous-ingress",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def _already_recorded(repo_root: Path, issue_number: int) -> bool:
    queue = AutonomousTaskQueue(repo_root)
    marker = f"github_issue:{issue_number}"
    for task in queue.get_all_tasks():
        if task.get("metadata", {}).get("external_id") == marker:
            return True
    for filename in ("autonomous_tasks_completed.jsonl", "autonomous_task_attempts.jsonl"):
        path = repo_root / "state" / filename
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            task = record.get("task", {})
            if isinstance(task, dict) and task.get("metadata", {}).get("external_id") == marker:
                return True
    return False


def ingest(repo: str, token: str, repo_root: Path) -> int:
    encoded = urllib.parse.quote(repo, safe="/")
    issues = _request(
        f"/repos/{encoded}/issues?state=open&per_page=50&sort=created&direction=asc",
        token,
    )
    queue = AutonomousTaskQueue(repo_root)
    count = 0
    for issue in issues if isinstance(issues, list) else []:
        if "pull_request" in issue:
            continue
        title = str(issue.get("title", "")).strip()
        if not title.casefold().startswith(PREFIX.casefold()):
            continue
        number = int(issue["number"])
        if _already_recorded(repo_root, number):
            continue
        objective = title[len(PREFIX):].strip()
        body = str(issue.get("body") or "").strip()
        if body:
            objective = f"{objective}\n\nRequest details:\n{body}"
        task_id = queue.add_task(
            title=title,
            description=objective,
            priority="high",
            source="github_issue",
            metadata={
                "external_id": f"github_issue:{number}",
                "issue_number": number,
                "issue_url": issue.get("html_url"),
                "requester": issue.get("user", {}).get("login"),
                "authority": "FactoryAuthorityGateway",
            },
        )
        _mutate(
            f"/repos/{encoded}/issues/{number}/comments",
            token,
            {"body": f"Autonomous request accepted into the durable queue as `{task_id}`. Execution is governed by the autonomous supervisor."},
        )
        count += 1
    return count


def main() -> int:
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")
    if not repo or not token:
        raise SystemExit("GITHUB_REPOSITORY and GITHUB_TOKEN are required")
    count = ingest(repo, token, REPO_ROOT)
    print(json.dumps({"ingested": count}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
