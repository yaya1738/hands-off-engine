#!/usr/bin/env python3
"""
GitHub Batch Operations Utility

Perform operations on multiple repositories efficiently with rate limit awareness.

Usage:
    python scripts/github_batch.py <operation> <repos_file> [options]

Operations:
    health      - Check health of all repositories
    stats       - Get statistics for all repositories
    prs         - List open PRs for all repositories
    releases    - Check latest releases

Examples:
    python scripts/github_batch.py health repos.json
    python scripts/github_batch.py stats repos.json --json
    python scripts/github_batch.py prs repos.json --output prs_report.json

Repos File Format (JSON):
[
  {"owner": "owner1", "repo": "repo1"},
  {"owner": "owner2", "repo": "repo2"}
]
"""

import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

from scripts.github_operations import (
    get_repo_info,
    get_repo_stats,
    list_pull_requests,
    get_latest_release,
)
from scripts.github_repo_health import analyze_repository_health


def load_repos(repos_file: str) -> List[Dict[str, str]]:
    """Load repository list from JSON file."""
    path = Path(repos_file)
    if not path.exists():
        raise FileNotFoundError(f"Repos file not found: {repos_file}")

    with open(path) as f:
        repos = json.load(f)

    if not isinstance(repos, list):
        raise ValueError("Repos file must contain a JSON array of {owner, repo} objects")

    return repos


def batch_health_check(repos: List[Dict[str, str]], delay: float = 1.0) -> List[Dict[str, Any]]:
    """Check health of multiple repositories."""
    results = []

    for i, repo_config in enumerate(repos):
        owner = repo_config["owner"]
        repo = repo_config["repo"]

        print(f"[{i+1}/{len(repos)}] Analyzing {owner}/{repo}...", file=sys.stderr)

        try:
            health = analyze_repository_health(owner, repo)
            results.append({
                "owner": owner,
                "repo": repo,
                "success": True,
                "health": health,
            })
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            results.append({
                "owner": owner,
                "repo": repo,
                "success": False,
                "error": str(e),
            })

        # Rate limit friendly delay
        if i < len(repos) - 1:
            time.sleep(delay)

    return results


def batch_stats(repos: List[Dict[str, str]], delay: float = 1.0) -> List[Dict[str, Any]]:
    """Get statistics for multiple repositories."""
    results = []

    for i, repo_config in enumerate(repos):
        owner = repo_config["owner"]
        repo = repo_config["repo"]

        print(f"[{i+1}/{len(repos)}] Fetching stats for {owner}/{repo}...", file=sys.stderr)

        try:
            stats = get_repo_stats(owner, repo)
            results.append({
                "owner": owner,
                "repo": repo,
                "success": True,
                "stats": stats,
            })
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            results.append({
                "owner": owner,
                "repo": repo,
                "success": False,
                "error": str(e),
            })

        if i < len(repos) - 1:
            time.sleep(delay)

    return results


def batch_prs(repos: List[Dict[str, str]], delay: float = 1.0) -> List[Dict[str, Any]]:
    """List open PRs for multiple repositories."""
    results = []

    for i, repo_config in enumerate(repos):
        owner = repo_config["owner"]
        repo = repo_config["repo"]

        print(f"[{i+1}/{len(repos)}] Fetching PRs for {owner}/{repo}...", file=sys.stderr)

        try:
            prs, meta = list_pull_requests(owner, repo, state="open", per_page=100)
            results.append({
                "owner": owner,
                "repo": repo,
                "success": True,
                "pr_count": len(prs),
                "prs": prs,
                "rate_limit": meta,
            })
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            results.append({
                "owner": owner,
                "repo": repo,
                "success": False,
                "error": str(e),
            })

        if i < len(repos) - 1:
            time.sleep(delay)

    return results


def batch_releases(repos: List[Dict[str, str]], delay: float = 1.0) -> List[Dict[str, Any]]:
    """Check latest releases for multiple repositories."""
    results = []

    for i, repo_config in enumerate(repos):
        owner = repo_config["owner"]
        repo = repo_config["repo"]

        print(f"[{i+1}/{len(repos)}] Checking release for {owner}/{repo}...", file=sys.stderr)

        try:
            release = get_latest_release(owner, repo)
            results.append({
                "owner": owner,
                "repo": repo,
                "success": True,
                "has_release": release is not None,
                "release": release,
            })
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            results.append({
                "owner": owner,
                "repo": repo,
                "success": False,
                "error": str(e),
            })

        if i < len(repos) - 1:
            time.sleep(delay)

    return results


def print_health_summary(results: List[Dict[str, Any]]) -> None:
    """Print summary of health check results."""
    print("\n" + "="*70)
    print("Batch Health Check Summary")
    print("="*70 + "\n")

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"Total: {len(results)} | Successful: {len(successful)} | Failed: {len(failed)}\n")

    if successful:
        print("Repository Health:")
        print(f"{'Repository':<40} {'Score':<10} {'Status':<15}")
        print("-"*70)

        for result in successful:
            repo_name = f"{result['owner']}/{result['repo']}"
            health = result["health"]
            score = health["health_score"]
            status = health["status"]

            status_icon = {
                "excellent": "🟢",
                "good": "🟡",
                "fair": "🟠",
                "poor": "🔴",
                "critical": "⛔",
            }.get(status, "⚪")

            print(f"{repo_name:<40} {score:<10} {status_icon} {status.upper()}")

    if failed:
        print("\n❌ Failed:")
        for result in failed:
            repo_name = f"{result['owner']}/{result['repo']}"
            print(f"  {repo_name}: {result['error']}")

    print()


def print_prs_summary(results: List[Dict[str, Any]]) -> None:
    """Print summary of PR results."""
    print("\n" + "="*70)
    print("Batch PRs Summary")
    print("="*70 + "\n")

    total_prs = sum(r.get("pr_count", 0) for r in results if r["success"])
    print(f"Total Open PRs: {total_prs}\n")

    print(f"{'Repository':<40} {'Open PRs':<10}")
    print("-"*70)

    for result in results:
        if result["success"]:
            repo_name = f"{result['owner']}/{result['repo']}"
            pr_count = result["pr_count"]
            print(f"{repo_name:<40} {pr_count}")

            # Show PR titles if there are any
            if pr_count > 0 and pr_count <= 5:
                for pr in result["prs"]:
                    print(f"  #{pr['number']}: {pr['title'][:60]}")

    print()


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    operation = sys.argv[1]
    repos_file = sys.argv[2]

    # Parse options
    json_output = "--json" in sys.argv
    output_file = None

    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]

    try:
        # Load repositories
        repos = load_repos(repos_file)
        print(f"Loaded {len(repos)} repositories from {repos_file}\n", file=sys.stderr)

        # Execute operation
        if operation == "health":
            results = batch_health_check(repos)
            if json_output or output_file:
                output = json.dumps(results, indent=2)
            else:
                print_health_summary(results)
                sys.exit(0)

        elif operation == "stats":
            results = batch_stats(repos)
            output = json.dumps(results, indent=2)

        elif operation == "prs":
            results = batch_prs(repos)
            if json_output or output_file:
                output = json.dumps(results, indent=2)
            else:
                print_prs_summary(results)
                sys.exit(0)

        elif operation == "releases":
            results = batch_releases(repos)
            output = json.dumps(results, indent=2)

        else:
            print(f"Unknown operation: {operation}")
            print("Valid operations: health, stats, prs, releases")
            sys.exit(1)

        # Output results
        if output_file:
            with open(output_file, "w") as f:
                f.write(output)
            print(f"\nResults written to: {output_file}", file=sys.stderr)
        else:
            print(output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
