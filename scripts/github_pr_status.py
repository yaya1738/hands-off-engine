#!/usr/bin/env python3
"""
GitHub Pull Request Status Checker

Checks PR status and provides actionable information for automated workflows.
Useful for CI/CD, automation agents, and monitoring systems.

Usage:
    # Check specific PR
    python scripts/github_pr_status.py owner repo PR_NUMBER

    # Check all open PRs
    python scripts/github_pr_status.py owner repo --all

    # JSON output for automation
    python scripts/github_pr_status.py owner repo 123 --json

    # Check if ready to merge
    python scripts/github_pr_status.py owner repo 123 --check-mergeable

Examples:
    python scripts/github_pr_status.py yaya1738 hands-off-engine 16
    python scripts/github_pr_status.py anthropics anthropic-sdk-python --all
"""

import json
import sys
from typing import Dict, List, Any

from scripts.github_operations import get_pull_request, list_pull_requests


def check_pr_status(owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
    """
    Check detailed status of a pull request.

    Returns:
        Dictionary with PR status including:
        - ready_to_merge: Boolean
        - blocking_issues: List of issues preventing merge
        - warnings: List of warnings
        - metadata: PR details
    """
    pr = get_pull_request(owner, repo, pr_number)

    result = {
        "owner": owner,
        "repo": repo,
        "pr_number": pr_number,
        "ready_to_merge": False,
        "blocking_issues": [],
        "warnings": [],
        "metadata": {
            "title": pr["title"],
            "state": pr["state"],
            "draft": pr["draft"],
            "mergeable": pr.get("mergeable"),
            "mergeable_state": pr.get("mergeable_state"),
            "merged": pr["merged"],
            "user": pr["user"]["login"],
            "created_at": pr["created_at"],
            "updated_at": pr["updated_at"],
            "commits": pr.get("commits"),
            "additions": pr.get("additions"),
            "deletions": pr.get("deletions"),
            "changed_files": pr.get("changed_files"),
            "labels": pr["labels"],
            "html_url": pr["html_url"],
        },
    }

    # Check blocking issues
    if pr["state"] != "open":
        result["blocking_issues"].append(f"PR is {pr['state']}, not open")
        return result

    if pr["draft"]:
        result["blocking_issues"].append("PR is marked as draft")

    if pr["merged"]:
        result["blocking_issues"].append("PR already merged")
        return result

    mergeable = pr.get("mergeable")
    if mergeable is False:
        result["blocking_issues"].append("PR has merge conflicts")

    mergeable_state = pr.get("mergeable_state", "unknown")
    if mergeable_state == "dirty":
        result["blocking_issues"].append("PR has failing checks or conflicts")
    elif mergeable_state == "blocked":
        result["blocking_issues"].append("PR is blocked (review required or failing checks)")
    elif mergeable_state == "behind":
        result["warnings"].append("PR branch is behind base branch")
    elif mergeable_state == "unstable":
        result["warnings"].append("PR has unstable checks")

    # Check labels for blockers
    labels = [label.lower() for label in pr["labels"]]
    if "wip" in labels or "work in progress" in labels:
        result["blocking_issues"].append("PR labeled as work-in-progress")
    if "do not merge" in labels or "do-not-merge" in labels:
        result["blocking_issues"].append("PR labeled as do-not-merge")
    if "needs review" in labels:
        result["warnings"].append("PR needs review")
    if "changes requested" in labels:
        result["blocking_issues"].append("Changes requested in review")

    # Determine if ready to merge
    result["ready_to_merge"] = (
        len(result["blocking_issues"]) == 0
        and pr["state"] == "open"
        and not pr["draft"]
        and not pr["merged"]
        and mergeable_state in ["clean", "unstable", "has_hooks"]
    )

    return result


def print_pr_status(status: Dict[str, Any], verbose: bool = False) -> None:
    """Print PR status in human-readable format."""
    meta = status["metadata"]

    print(f"\nPR #{status['pr_number']}: {meta['title']}")
    print(f"Repository: {status['owner']}/{status['repo']}")
    print(f"Author: {meta['user']}")
    print(f"State: {meta['state']} | Draft: {meta['draft']} | Merged: {meta['merged']}")
    print(f"Mergeable: {meta['mergeable']} | State: {meta['mergeable_state']}")

    if meta.get("commits"):
        print(
            f"Changes: {meta['commits']} commits, "
            f"+{meta['additions']} -{meta['deletions']}, "
            f"{meta['changed_files']} files"
        )

    if meta["labels"]:
        print(f"Labels: {', '.join(meta['labels'])}")

    print(f"\n{'✅' if status['ready_to_merge'] else '❌'} Ready to merge: {status['ready_to_merge']}")

    if status["blocking_issues"]:
        print(f"\n🚫 Blocking Issues ({len(status['blocking_issues'])}):")
        for issue in status["blocking_issues"]:
            print(f"   - {issue}")

    if status["warnings"]:
        print(f"\n⚠️  Warnings ({len(status['warnings'])}):")
        for warning in status["warnings"]:
            print(f"   - {warning}")

    if verbose:
        print(f"\nURL: {meta['html_url']}")
        print(f"Created: {meta['created_at']}")
        print(f"Updated: {meta['updated_at']}")


def check_all_prs(owner: str, repo: str) -> List[Dict[str, Any]]:
    """Check status of all open PRs in a repository."""
    prs, _ = list_pull_requests(owner, repo, state="open", per_page=100)

    results = []
    for pr in prs:
        status = check_pr_status(owner, repo, pr["number"])
        results.append(status)

    return results


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    owner = sys.argv[1]
    repo = sys.argv[2]

    # Parse arguments
    check_all = "--all" in sys.argv
    json_output = "--json" in sys.argv
    check_mergeable = "--check-mergeable" in sys.argv
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    try:
        if check_all:
            # Check all open PRs
            results = check_all_prs(owner, repo)

            if json_output:
                print(json.dumps(results, indent=2))
            else:
                print(f"\n{'='*60}")
                print(f"All Open PRs for {owner}/{repo}")
                print(f"{'='*60}")

                ready_count = sum(1 for r in results if r["ready_to_merge"])
                print(f"\nTotal: {len(results)} PRs | Ready to merge: {ready_count}")

                for result in results:
                    print_pr_status(result, verbose=verbose)
                    print("-" * 60)

        else:
            # Check specific PR
            if len(sys.argv) < 4 or sys.argv[3].startswith("--"):
                print("Error: PR number required")
                print(f"Usage: {sys.argv[0]} {owner} {repo} PR_NUMBER [--json]")
                sys.exit(1)

            pr_number = int(sys.argv[3])
            status = check_pr_status(owner, repo, pr_number)

            if json_output:
                print(json.dumps(status, indent=2))
            elif check_mergeable:
                # Exit code 0 if ready to merge, 1 otherwise
                if status["ready_to_merge"]:
                    print(f"✅ PR #{pr_number} is ready to merge")
                    sys.exit(0)
                else:
                    print(f"❌ PR #{pr_number} is NOT ready to merge")
                    for issue in status["blocking_issues"]:
                        print(f"   - {issue}")
                    sys.exit(1)
            else:
                print_pr_status(status, verbose=verbose)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
