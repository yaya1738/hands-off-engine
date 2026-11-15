#!/usr/bin/env python3
"""Run the read-only governance poll, then admit findings for human review.

The wrapper is a scheduler child, not a daemon. It creates queue records only;
it never dispatches tasks or invokes execution.
"""
from __future__ import annotations

import json
from scripts.github_governance_monitor import monitor_once
from ai.factory.authority_gateway import FactoryAuthorityGateway

PRIORITY = {
    "ci_failed": 1,
    "review_changes_requested": 1,
    "merge_blocked": 2,
    "ci_missing": 2,
    "ci_pending": 3,
    "stale_pr": 3,
}
MAX_ADMISSIONS = 50


def admit_findings(report: dict, gateway=None) -> dict:
    if not isinstance(report, dict):
        raise ValueError("governance report must be an object")
    findings = report.get("findings", [])
    if not isinstance(findings, list):
        raise ValueError("governance findings must be a list")
    gateway = gateway or FactoryAuthorityGateway()
    counts = {"queued": 0, "replayed": 0, "skipped": 0, "errors": 0}
    for finding in findings[:MAX_ADMISSIONS]:
        if not isinstance(finding, dict):
            counts["skipped"] += 1
            continue
        category = finding.get("category")
        finding_id = finding.get("id")
        if category not in PRIORITY or not isinstance(finding_id, str) or not finding_id:
            counts["skipped"] += 1
            continue
        number = finding.get("pr_number")
        title = str(finding.get("title") or "")[:160]
        detail = str(finding.get("detail") or "")[:240]
        objective = f"Review GitHub governance finding ({category}) for PR #{number}: {title}. {detail}"[:1000]
        metadata = {
            "finding_id": finding_id[:200],
            "category": category,
            "pr_number": number if isinstance(number, int) and not isinstance(number, bool) else None,
            "head_sha": str(finding.get("head_sha") or "")[:40],
            "html_url": str(finding.get("html_url") or "")[:300],
        }
        try:
            result = gateway.submit_goal(
                objective,
                priority=PRIORITY[category],
                source="github_governance_monitor",
                idempotency_key=f"github-governance:{finding_id}",
                metadata=metadata,
            )
            if result.get("status") == "queued_for_review":
                counts["queued"] += 1
            elif result.get("status") == "idempotent_replay":
                counts["replayed"] += 1
            else:
                counts["errors"] += 1
        except Exception:
            counts["errors"] += 1
    counts["processed"] = min(len(findings), MAX_ADMISSIONS)
    return counts


def main():
    report = monitor_once()
    result = admit_findings(report)
    print(json.dumps({
        "api_status": report.get("api_status"),
        "finding_count": report.get("finding_count", 0),
        "objective_admission": result,
        "execution_enabled": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
