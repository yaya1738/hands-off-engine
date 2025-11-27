#!/usr/bin/env python3
"""
GitHub Repository Health Monitor

Analyzes repository health metrics and provides actionable insights.
Useful for identifying issues, tracking activity, and ensuring code quality.

Usage:
    python scripts/github_repo_health.py owner repo [--json] [--detailed]

Examples:
    python scripts/github_repo_health.py yaya1738 hands-off-engine
    python scripts/github_repo_health.py anthropics anthropic-sdk-python --detailed
    python scripts/github_repo_health.py owner repo --json > health_report.json
"""

import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

from scripts.github_operations import (
    get_repo_info,
    list_pull_requests,
    list_issues,
    get_latest_release,
)


def calculate_health_score(metrics: Dict[str, Any]) -> int:
    """
    Calculate overall repository health score (0-100).

    Factors:
    - Recent activity (25 points)
    - Issue management (20 points)
    - PR management (20 points)
    - Release management (15 points)
    - Documentation (10 points)
    - Community engagement (10 points)
    """
    score = 0

    # Recent activity (25 points)
    days_since_push = metrics.get("days_since_last_push", 999)
    if days_since_push < 1:
        score += 25
    elif days_since_push < 7:
        score += 20
    elif days_since_push < 30:
        score += 15
    elif days_since_push < 90:
        score += 10
    elif days_since_push < 180:
        score += 5

    # Issue management (20 points)
    open_issues = metrics.get("open_issues", 0)
    stars = max(metrics.get("stars", 1), 1)  # Avoid division by zero
    issue_ratio = open_issues / stars

    if issue_ratio < 0.1:
        score += 20
    elif issue_ratio < 0.2:
        score += 15
    elif issue_ratio < 0.5:
        score += 10
    elif issue_ratio < 1.0:
        score += 5

    # PR management (20 points)
    open_prs = metrics.get("open_prs_count", 0)
    old_prs = metrics.get("stale_prs_count", 0)

    if open_prs == 0 and old_prs == 0:
        score += 20
    elif open_prs < 5 and old_prs == 0:
        score += 15
    elif open_prs < 10 and old_prs < 3:
        score += 10
    elif old_prs < 5:
        score += 5

    # Release management (15 points)
    days_since_release = metrics.get("days_since_last_release", 999)
    if days_since_release < 30:
        score += 15
    elif days_since_release < 90:
        score += 10
    elif days_since_release < 180:
        score += 5

    # Documentation (10 points)
    has_description = bool(metrics.get("has_description"))
    has_recent_release = days_since_release < 180

    if has_description:
        score += 5
    if has_recent_release:
        score += 5

    # Community engagement (10 points)
    if stars > 100:
        score += 5
    elif stars > 10:
        score += 3
    elif stars > 0:
        score += 1

    forks = metrics.get("forks", 0)
    if forks > 20:
        score += 5
    elif forks > 5:
        score += 3
    elif forks > 0:
        score += 1

    return min(score, 100)


def analyze_repository_health(owner: str, repo: str) -> Dict[str, Any]:
    """Perform comprehensive health analysis of a repository."""
    # Fetch data
    info = get_repo_info(owner, repo)
    open_prs, _ = list_pull_requests(owner, repo, state="open", per_page=100)
    all_issues, _ = list_issues(owner, repo, state="open", per_page=100)
    latest_release = get_latest_release(owner, repo)

    # Filter actual issues (not PRs)
    actual_issues = [i for i in all_issues if not i["is_pull_request"]]

    # Calculate metrics
    now = datetime.now(datetime.now().astimezone().tzinfo)

    # Parse timestamps
    def parse_time(ts_str):
        if not ts_str:
            return None
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))

    pushed_at = parse_time(info.get("pushed_at"))
    days_since_push = (now - pushed_at).days if pushed_at else 999

    created_at = parse_time(info.get("created_at"))
    repo_age_days = (now - created_at).days if created_at else 0

    # Analyze PRs
    stale_pr_threshold = timedelta(days=30)
    stale_prs = []
    for pr in open_prs:
        updated = parse_time(pr.get("updated_at"))
        if updated and (now - updated) > stale_pr_threshold:
            stale_prs.append(pr)

    # Analyze issues
    stale_issue_threshold = timedelta(days=60)
    stale_issues = []
    for issue in actual_issues:
        updated = parse_time(issue.get("updated_at"))
        if updated and (now - updated) > stale_issue_threshold:
            stale_issues.append(issue)

    # Release info
    days_since_release = 999
    if latest_release and latest_release.get("published_at"):
        published = parse_time(latest_release["published_at"])
        if published:
            days_since_release = (now - published).days

    # Compile metrics
    metrics = {
        "repository": f"{owner}/{repo}",
        "stars": info.get("stars", 0),
        "forks": info.get("forks", 0),
        "watchers": info.get("watchers", 0),
        "open_issues": info.get("open_issues", 0),
        "language": info.get("language"),
        "has_description": bool(info.get("description")),
        "archived": info.get("archived", False),
        "private": info.get("private", False),
        "days_since_last_push": days_since_push,
        "repo_age_days": repo_age_days,
        "open_prs_count": len(open_prs),
        "stale_prs_count": len(stale_prs),
        "open_issues_count": len(actual_issues),
        "stale_issues_count": len(stale_issues),
        "days_since_last_release": days_since_release,
        "has_recent_release": days_since_release < 180,
        "latest_release_tag": latest_release.get("tag_name") if latest_release else None,
    }

    # Calculate health score
    health_score = calculate_health_score(metrics)

    # Determine health status
    if health_score >= 80:
        status = "excellent"
    elif health_score >= 60:
        status = "good"
    elif health_score >= 40:
        status = "fair"
    elif health_score >= 20:
        status = "poor"
    else:
        status = "critical"

    # Generate recommendations
    recommendations = []
    warnings = []

    if info.get("archived"):
        warnings.append("Repository is archived")

    if days_since_push > 90:
        warnings.append(f"No activity for {days_since_push} days")
        recommendations.append("Consider updating README or making a commit to show activity")
    elif days_since_push > 30:
        recommendations.append("Repository has low recent activity")

    if len(stale_prs) > 0:
        warnings.append(f"{len(stale_prs)} stale PRs (>30 days old)")
        recommendations.append("Review and merge or close stale pull requests")

    if len(stale_issues) > 0:
        warnings.append(f"{len(stale_issues)} stale issues (>60 days old)")
        recommendations.append("Triage and update old issues")

    if len(open_prs) > 10:
        warnings.append(f"High number of open PRs ({len(open_prs)})")
        recommendations.append("Consider reviewing backlog of pull requests")

    if not info.get("description"):
        recommendations.append("Add a repository description")

    if days_since_release > 180:
        recommendations.append("Consider creating a new release")

    if metrics["open_issues"] > metrics["stars"] * 0.5:
        warnings.append("High issue-to-star ratio")
        recommendations.append("Address open issues to improve repository health")

    # Compile result
    result = {
        "health_score": health_score,
        "status": status,
        "metrics": metrics,
        "warnings": warnings,
        "recommendations": recommendations,
        "analysis_timestamp": now.isoformat(),
        "url": info.get("html_url"),
    }

    return result


def print_health_report(health: Dict[str, Any], detailed: bool = False) -> None:
    """Print health report in human-readable format."""
    # Header
    print(f"\n{'='*70}")
    print(f"Repository Health Report: {health['metrics']['repository']}")
    print(f"{'='*70}\n")

    # Health Score
    score = health["health_score"]
    status = health["status"]

    status_emoji = {
        "excellent": "🟢",
        "good": "🟡",
        "fair": "🟠",
        "poor": "🔴",
        "critical": "⛔",
    }

    print(f"{status_emoji.get(status, '⚪')} Health Score: {score}/100 ({status.upper()})")
    print()

    # Key Metrics
    m = health["metrics"]
    print("Key Metrics:")
    print(f"  Stars: {m['stars']} | Forks: {m['forks']} | Watchers: {m['watchers']}")
    print(f"  Language: {m['language'] or 'Not specified'}")
    print(f"  Repository age: {m['repo_age_days']} days")
    print(f"  Last push: {m['days_since_last_push']} days ago")

    if m['latest_release_tag']:
        print(f"  Latest release: {m['latest_release_tag']} ({m['days_since_last_release']} days ago)")
    else:
        print("  Latest release: None")

    print()

    # Activity Summary
    print("Activity Summary:")
    print(f"  Open PRs: {m['open_prs_count']} (Stale: {m['stale_prs_count']})")
    print(f"  Open Issues: {m['open_issues_count']} (Stale: {m['stale_issues_count']})")
    print()

    # Warnings
    if health["warnings"]:
        print(f"⚠️  Warnings ({len(health['warnings'])}):")
        for warning in health["warnings"]:
            print(f"  - {warning}")
        print()

    # Recommendations
    if health["recommendations"]:
        print(f"💡 Recommendations ({len(health['recommendations'])}):")
        for rec in health["recommendations"]:
            print(f"  - {rec}")
        print()

    # Detailed metrics
    if detailed:
        print("Detailed Metrics:")
        for key, value in sorted(m.items()):
            print(f"  {key}: {value}")
        print()

    print(f"Report generated: {health['analysis_timestamp']}")
    print(f"Repository URL: {health['url']}")
    print(f"{'='*70}\n")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    owner = sys.argv[1]
    repo = sys.argv[2]

    json_output = "--json" in sys.argv
    detailed = "--detailed" in sys.argv

    try:
        health = analyze_repository_health(owner, repo)

        if json_output:
            print(json.dumps(health, indent=2))
        else:
            print_health_report(health, detailed=detailed)

        # Exit code based on health status
        if health["status"] in ["excellent", "good"]:
            sys.exit(0)
        elif health["status"] == "fair":
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"Error analyzing repository health: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
