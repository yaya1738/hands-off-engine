#!/usr/bin/env python3
"""Read-only, bounded GitHub governance monitor for the Hands-Off scheduler.

It inspects open PR metadata, latest-head check runs, coordination issue comment
activity, and local runtime-evidence freshness. It never writes to GitHub,
changes PR state, merges, deploys, or executes tasks. Reports are persisted
locally and published to the canonical bus only when their signature changes.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
REPO = os.getenv("FACTORY_GITHUB_REPO", "yaya1738/hands-off-engine")
COORDINATION_ISSUE = int(os.getenv("FACTORY_COORDINATION_ISSUE", "374"))
API_ROOT = os.getenv("FACTORY_GITHUB_API_URL", "https://api.github.com").rstrip("/")
STATE_FILE = ROOT / "state" / "github_governance_monitor_state.json"
REPORT_FILE = ROOT / "state" / "github_governance_report.json"
BUS_FILE = ROOT / "ai" / "coordination" / "messages.jsonl"
MAX_PRS = 10
STALE_DAYS = 14
SUCCESS_CONCLUSIONS = {"success", "neutral", "skipped"}
FAILURE_CONCLUSIONS = {"failure", "cancelled", "timed_out", "action_required", "startup_failure"}


def _fetch_json(path: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "hands-off-engine-governance-monitor",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{API_ROOT}{path}", headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=2) as response:
        return json.loads(response.read().decode("utf-8"))


def _load_json(path: Path, default: dict) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else dict(default)
    except Exception:
        return dict(default)


def _parse_time(value: str | None) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _check_status(payload: Any) -> str:
    checks = payload.get("check_runs", []) if isinstance(payload, dict) else []
    if not isinstance(checks, list) or not checks:
        return "missing"
    statuses = [item.get("status") for item in checks if isinstance(item, dict)]
    conclusions = [item.get("conclusion") for item in checks if isinstance(item, dict)]
    if any(status in {"queued", "in_progress", "requested", "waiting"} for status in statuses):
        return "pending"
    if any(conclusion in FAILURE_CONCLUSIONS for conclusion in conclusions):
        return "failed"
    completed = [item for item in checks if isinstance(item, dict) and item.get("status") == "completed"]
    if completed and all(item.get("conclusion") in SUCCESS_CONCLUSIONS for item in completed):
        return "passed"
    return "unknown"


def _runtime_evidence(root: Path, now: datetime) -> dict:
    candidates = [
        root / "state" / "supervisor_state.json",
        root / "state" / "termux_supervisor_state.json",
        root / "state" / "node1_state.json",
    ]
    existing = [(path, path.stat().st_mtime) for path in candidates if path.exists()]
    if not existing:
        return {"available": False, "age_seconds": None, "source": None}
    path, mtime = max(existing, key=lambda item: item[1])
    age = max(0, int(now.timestamp() - mtime))
    modified_at = datetime.fromtimestamp(mtime, timezone.utc).isoformat()
    return {
        "available": True,
        "age_seconds": age,
        "source": str(path.relative_to(root)),
        "modified_at": modified_at,
    }


def monitor_once(
    fetch_json: Callable[[str], Any] | None = None,
    *,
    root: Path = ROOT,
    now: datetime | None = None,
    max_prs: int = MAX_PRS,
) -> dict:
    """Run one bounded read-only poll. fetch_json is injectable for tests."""
    fetch = fetch_json or _fetch_json
    root = Path(root)
    now = now or datetime.now(timezone.utc)
    state_path = root / "state" / "github_governance_monitor_state.json"
    report_path = root / "state" / "github_governance_report.json"
    bus_path = root / "ai" / "coordination" / "messages.jsonl"
    state = _load_json(state_path, {"last_signature": "", "comment_ids": []})
    errors: list[str] = []
    findings: list[dict] = []
    status_counts = {"passed": 0, "failed": 0, "pending": 0, "missing": 0, "unknown": 0}
    draft_count = 0
    review_status_counts = {"changes_requested": 0, "approved": 0, "commented": 0, "unknown": 0}

    try:
        pull_requests = fetch(f"/repos/{REPO}/pulls?state=open&per_page=100&sort=updated&direction=desc")
        if not isinstance(pull_requests, list):
            raise ValueError("pull request response was not a list")
    except Exception as exc:
        pull_requests = []
        errors.append(f"pulls_newest:{type(exc).__name__}")

    try:
        oldest_pull_requests = fetch(f"/repos/{REPO}/pulls?state=open&per_page=100&sort=updated&direction=asc")
        if not isinstance(oldest_pull_requests, list):
            raise ValueError("oldest pull request response was not a list")
    except Exception as exc:
        oldest_pull_requests = []
        errors.append("pulls_oldest:unavailable")

    limit = max(1, min(int(max_prs), 20))
    half = max(1, limit // 2)
    candidates = pull_requests[:half] + oldest_pull_requests[:half] + pull_requests[half:limit]
    selected_by_number = {}
    for item in candidates:
        if isinstance(item, dict) and item.get("number") is not None:
            selected_by_number[item["number"]] = item
    selected = list(selected_by_number.values())[:limit]
    for pr in selected:
        if not isinstance(pr, dict):
            continue
        number = pr.get("number")
        head = pr.get("head") if isinstance(pr.get("head"), dict) else {}
        sha = head.get("sha")
        if pr.get("draft"):
            draft_count += 1
        checks_status = "unknown"
        if isinstance(sha, str) and sha:
            try:
                checks_status = _check_status(fetch(f"/repos/{REPO}/commits/{sha}/check-runs"))
            except Exception as exc:
                errors.append(f"checks:{number}:{type(exc).__name__}")
        status_counts[checks_status] = status_counts.get(checks_status, 0) + 1

        review_status = "unknown"
        if number is not None:
            try:
                reviews = fetch(f"/repos/{REPO}/pulls/{number}/reviews")
                if isinstance(reviews, list):
                    latest_by_reviewer = {}
                    for review in reviews:
                        if not isinstance(review, dict):
                            continue
                        reviewer = (review.get("user") or {}).get("login")
                        if reviewer:
                            latest_by_reviewer[reviewer] = review.get("state")
                    states = set(latest_by_reviewer.values())
                    if "CHANGES_REQUESTED" in states:
                        review_status = "changes_requested"
                    elif "APPROVED" in states:
                        review_status = "approved"
                    elif "COMMENTED" in states:
                        review_status = "commented"
                    else:
                        review_status = "unknown"
            except Exception as exc:
                errors.append(f"reviews:{number}:{type(exc).__name__}")
        review_status_counts[review_status] = review_status_counts.get(review_status, 0) + 1

        def add(category: str, detail: str):
            findings.append({
                "id": f"pr:{number}:{category}:{str(sha or 'no-sha')[:12]}",
                "pr_number": number,
                "title": str(pr.get("title") or "")[:160],
                "category": category,
                "detail": detail[:240],
                "draft": bool(pr.get("draft")),
                "head_sha": str(sha or "")[:40],
                "updated_at": pr.get("updated_at"),
                "html_url": pr.get("html_url"),
            })

        if review_status == "changes_requested":
            add("review_changes_requested", "The latest review state includes a changes-requested review.")
        if checks_status == "failed":
            add("ci_failed", "One or more latest-head checks failed.")
        elif checks_status == "missing":
            add("ci_missing", "No check runs were returned; empty checks are not treated as passing.")
        elif checks_status == "pending":
            add("ci_pending", "One or more latest-head checks are still running.")

        updated = _parse_time(pr.get("updated_at"))
        if updated and updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        if updated and now - updated > timedelta(days=STALE_DAYS):
            add("stale_pr", f"Open PR has not been updated for more than {STALE_DAYS} days.")

        mergeable_state = str(pr.get("mergeable_state") or "").lower()
        if pr.get("mergeable") is False or mergeable_state in {"dirty", "behind", "blocked"}:
            add("merge_blocked", f"GitHub reports mergeable={pr.get('mergeable')} state={mergeable_state or 'unknown'}.")

    try:
        comments = fetch(f"/repos/{REPO}/issues/{COORDINATION_ISSUE}/comments?per_page=100&direction=desc")
        if not isinstance(comments, list):
            raise ValueError("coordination comments response was not a list")
    except Exception as exc:
        comments = []
        errors.append(f"comments:{type(exc).__name__}")

    previous_ids = set(map(str, state.get("comment_ids", [])))
    current_ids = [str(item.get("id")) for item in comments if isinstance(item, dict) and item.get("id")]
    new_comment_count = sum(1 for item in current_ids if item not in previous_ids)
    runtime = _runtime_evidence(root, now)

    report = {
        "generated_at": now.astimezone(timezone.utc).isoformat(),
        "repository": REPO,
        "coordination_issue": COORDINATION_ISSUE,
        "api_status": "partial" if errors else "ok",
        "open_pr_count": len(pull_requests),
        "monitored_pr_count": len(selected),
        "draft_pr_count": draft_count,
        "check_status_counts": status_counts,
        "review_status_counts": review_status_counts,
        "finding_count": len(findings),
        "findings": findings[:100],
        "new_coordination_comments": new_comment_count,
        "coordination_comment_count": len(comments),
        "runtime_evidence": runtime,
        "errors": errors[:20],
        "mode": "read_only",
    }
    signature_material = {
        "repository": REPO,
        "coordination_issue": COORDINATION_ISSUE,
        "api_status": report["api_status"],
        "open_pr_count": report["open_pr_count"],
        "monitored_pr_count": report["monitored_pr_count"],
        "draft_pr_count": report["draft_pr_count"],
        "check_status_counts": status_counts,
        "review_status_counts": review_status_counts,
        "findings": findings,
        "runtime_evidence": {
            "available": runtime["available"],
            "source": runtime["source"],
            "modified_at": runtime.get("modified_at"),
        },
        "latest_coordination_comment_id": current_ids[0] if current_ids else None,
        "errors": errors[:20],
    }
    canonical = json.dumps(signature_material, sort_keys=True, separators=(",", ":"))
    signature = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    report["signature"] = signature

    report_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_report = report_path.with_suffix(".tmp")
    tmp_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    tmp_report.replace(report_path)

    if signature != state.get("last_signature"):
        message = {
            "from": "github_governance_monitor",
            "to": "factory",
            "type": "governance_report",
            "msg_id": f"github-governance-{signature[:16]}",
            "timestamp": report["generated_at"],
            "message": f"Read-only governance snapshot: {len(selected)} PRs checked, {len(findings)} findings, API status {report['api_status']}.",
            "context": {
                "report_path": "state/github_governance_report.json",
                "signature": signature,
                "finding_count": len(findings),
                "findings": findings[:50],
                "execution_enabled": False,
            },
        }
        bus_path.parent.mkdir(parents=True, exist_ok=True)
        existing = bus_path.read_text(encoding="utf-8", errors="ignore") if bus_path.exists() else ""
        if message["msg_id"] not in existing:
            with bus_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(message) + "\n")

    state["last_signature"] = signature
    state["comment_ids"] = current_ids[-500:]
    state["last_run"] = report["generated_at"]
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_state = state_path.with_suffix(".tmp")
    tmp_state.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    tmp_state.replace(state_path)
    return report


if __name__ == "__main__":
    result = monitor_once()
    print(json.dumps({
        "api_status": result["api_status"],
        "monitored_pr_count": result["monitored_pr_count"],
        "finding_count": result["finding_count"],
        "new_coordination_comments": result["new_coordination_comments"],
        "runtime_evidence": result["runtime_evidence"],
    }, indent=2))