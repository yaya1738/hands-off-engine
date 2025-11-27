#!/usr/bin/env python3
"""
GitHub Repository Monitoring Dashboard

Displays real-time status of multiple repositories in a clean dashboard format.
Useful for monitoring project health, PR activity, and release status.

Usage:
    python scripts/github_dashboard.py [config_file]

    # Default config: .github_dashboard.json in repo root
    python scripts/github_dashboard.py

    # Custom config
    python scripts/github_dashboard.py my_repos.json

Config Format (JSON):
{
  "repositories": [
    {"owner": "owner1", "repo": "repo1"},
    {"owner": "owner2", "repo": "repo2"}
  ],
  "refresh_interval": 300,
  "show_prs": true,
  "show_issues": true,
  "show_releases": true
}
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from scripts.github_operations import (
    get_repo_info,
    list_pull_requests,
    list_issues,
    get_latest_release,
    GitHubRateLimitError,
)


DEFAULT_CONFIG = {
    "repositories": [],
    "refresh_interval": 300,  # 5 minutes
    "show_prs": True,
    "show_issues": True,
    "show_releases": True,
}


def load_config(config_path: str = ".github_dashboard.json") -> Dict[str, Any]:
    """Load dashboard configuration from JSON file."""
    config_file = Path(config_path)

    if not config_file.exists():
        print(f"Config file not found: {config_path}")
        print("Creating default config...")

        default_repos = [
            {"owner": "yaya1738", "repo": "hands-off-engine"},
        ]

        config = DEFAULT_CONFIG.copy()
        config["repositories"] = default_repos

        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        print(f"Created: {config_path}")
        print("Edit this file to add more repositories to monitor.")
        return config

    with open(config_file) as f:
        return json.load(f)


def format_time_ago(iso_timestamp: str) -> str:
    """Format ISO timestamp as human-readable time ago."""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        delta = now - dt

        if delta < timedelta(minutes=1):
            return "just now"
        elif delta < timedelta(hours=1):
            mins = int(delta.total_seconds() / 60)
            return f"{mins}m ago"
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() / 3600)
            return f"{hours}h ago"
        elif delta < timedelta(days=7):
            days = delta.days
            return f"{days}d ago"
        elif delta < timedelta(days=30):
            weeks = delta.days // 7
            return f"{weeks}w ago"
        else:
            months = delta.days // 30
            return f"{months}mo ago"
    except Exception:
        return "unknown"


def fetch_repo_data(owner: str, repo: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch all data for a repository."""
    data = {
        "owner": owner,
        "repo": repo,
        "error": None,
    }

    try:
        # Get basic repo info
        info = get_repo_info(owner, repo)
        data["info"] = info

        # Get PRs if enabled
        if config.get("show_prs", True):
            prs, _ = list_pull_requests(owner, repo, state="open", per_page=5)
            data["open_prs"] = prs

        # Get issues if enabled
        if config.get("show_issues", True):
            issues, _ = list_issues(owner, repo, state="open", per_page=5)
            # Filter out PRs (GitHub API includes PRs in issues)
            data["open_issues"] = [i for i in issues if not i["is_pull_request"]]

        # Get latest release if enabled
        if config.get("show_releases", True):
            release = get_latest_release(owner, repo)
            data["latest_release"] = release

    except GitHubRateLimitError as e:
        data["error"] = f"Rate limit exceeded: {e}"
    except Exception as e:
        data["error"] = str(e)

    return data


def print_dashboard(repos_data: List[Dict[str, Any]], config: Dict[str, Any]) -> None:
    """Print the monitoring dashboard."""
    # Clear screen (works on Unix-like systems)
    print("\033[2J\033[H", end="")

    # Header
    print("=" * 80)
    print(f"  GitHub Repository Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    for data in repos_data:
        owner = data["owner"]
        repo = data["repo"]
        full_name = f"{owner}/{repo}"

        if data.get("error"):
            print(f"❌ {full_name}")
            print(f"   Error: {data['error']}")
            print()
            continue

        info = data.get("info", {})

        # Repository header
        print(f"📦 {full_name}")
        if info.get("description"):
            print(f"   {info['description']}")

        # Stats line
        stats = []
        if info.get("stars") is not None:
            stars = info["stars"]
            stats.append(f"⭐ {stars}")
        if info.get("forks") is not None:
            forks = info["forks"]
            stats.append(f"🔀 {forks}")
        if info.get("language"):
            stats.append(f"📝 {info['language']}")

        if stats:
            print(f"   {' | '.join(stats)}")

        # Activity
        if info.get("pushed_at"):
            pushed = format_time_ago(info["pushed_at"])
            print(f"   Last push: {pushed}")

        # Open PRs
        if config.get("show_prs", True) and "open_prs" in data:
            prs = data["open_prs"]
            if prs:
                print(f"   🔀 {len(prs)} open PR(s):")
                for pr in prs[:3]:  # Show first 3
                    print(f"      #{pr['number']}: {pr['title'][:60]}")
                if len(prs) > 3:
                    print(f"      ... and {len(prs) - 3} more")

        # Open Issues
        if config.get("show_issues", True) and "open_issues" in data:
            issues = data["open_issues"]
            if issues:
                print(f"   🐛 {len(issues)} open issue(s):")
                for issue in issues[:3]:  # Show first 3
                    print(f"      #{issue['number']}: {issue['title'][:60]}")
                if len(issues) > 3:
                    print(f"      ... and {len(issues) - 3} more")

        # Latest Release
        if config.get("show_releases", True) and data.get("latest_release"):
            release = data["latest_release"]
            tag = release.get("tag_name", "unknown")
            published = format_time_ago(release.get("published_at", ""))
            print(f"   📦 Latest release: {tag} ({published})")

        print()

    # Footer
    print("-" * 80)
    refresh = config.get("refresh_interval", 300)
    print(f"Refreshing every {refresh}s | Press Ctrl+C to exit")
    print("-" * 80)


def main():
    """Main dashboard loop."""
    # Load config
    config_file = sys.argv[1] if len(sys.argv) > 1 else ".github_dashboard.json"
    config = load_config(config_file)

    if not config.get("repositories"):
        print("No repositories configured!")
        print(f"Edit {config_file} to add repositories to monitor.")
        sys.exit(1)

    refresh_interval = config.get("refresh_interval", 300)

    print(f"Starting dashboard (refresh: {refresh_interval}s)...")
    print("Loading data...")
    time.sleep(2)

    try:
        while True:
            # Fetch data for all repos
            repos_data = []
            for repo_config in config["repositories"]:
                owner = repo_config["owner"]
                repo = repo_config["repo"]
                data = fetch_repo_data(owner, repo, config)
                repos_data.append(data)

            # Print dashboard
            print_dashboard(repos_data, config)

            # Wait before refresh
            time.sleep(refresh_interval)

    except KeyboardInterrupt:
        print("\n\nDashboard stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
