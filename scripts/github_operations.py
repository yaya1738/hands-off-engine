"""
High-level GitHub operations built on the rate-limit-aware client.

Provides convenient functions for common GitHub tasks:
- Repository information and statistics
- Pull request management
- Issue tracking
- Release information
- Code search

All functions use the rate-limit-aware github_client and return structured data.
"""

from typing import Any, Dict, List, Optional, Tuple
from scripts.github_client import github_get, GitHubRateLimitError


def get_repo_info(owner: str, repo: str) -> Dict[str, Any]:
    """
    Get comprehensive information about a repository.

    Args:
        owner: Repository owner (user or organization)
        repo: Repository name

    Returns:
        Dictionary with repository information including:
        - name, full_name, description
        - stargazers_count, forks_count, watchers_count
        - open_issues_count
        - default_branch, language
        - created_at, updated_at, pushed_at
        - html_url, clone_url

    Raises:
        GitHubRateLimitError: If rate limit exceeded
        requests.HTTPError: For other API errors
    """
    data, meta = github_get(f"/repos/{owner}/{repo}")
    return {
        "name": data.get("name"),
        "full_name": data.get("full_name"),
        "description": data.get("description"),
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "watchers": data.get("watchers_count"),
        "open_issues": data.get("open_issues_count"),
        "default_branch": data.get("default_branch"),
        "language": data.get("language"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "pushed_at": data.get("pushed_at"),
        "html_url": data.get("html_url"),
        "clone_url": data.get("clone_url"),
        "private": data.get("private"),
        "archived": data.get("archived"),
        "rate_limit": meta,
    }


def list_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    per_page: int = 30,
    page: int = 1,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    List pull requests for a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        state: PR state - "open", "closed", or "all" (default: "open")
        per_page: Results per page (default: 30, max: 100)
        page: Page number (default: 1)

    Returns:
        Tuple of (list of PR summaries, rate limit metadata)

    Each PR summary contains:
        - number, title, state
        - user (login, avatar_url)
        - created_at, updated_at
        - html_url
        - draft, mergeable_state

    Raises:
        GitHubRateLimitError: If rate limit exceeded
        requests.HTTPError: For other API errors
    """
    params = {
        "state": state,
        "per_page": min(per_page, 100),
        "page": page,
    }

    data, meta = github_get(f"/repos/{owner}/{repo}/pulls", params=params)

    prs = []
    for pr in data:
        prs.append({
            "number": pr.get("number"),
            "title": pr.get("title"),
            "state": pr.get("state"),
            "user": {
                "login": pr.get("user", {}).get("login"),
                "avatar_url": pr.get("user", {}).get("avatar_url"),
            },
            "created_at": pr.get("created_at"),
            "updated_at": pr.get("updated_at"),
            "html_url": pr.get("html_url"),
            "draft": pr.get("draft"),
            "mergeable_state": pr.get("mergeable_state"),
            "labels": [label.get("name") for label in pr.get("labels", [])],
        })

    return prs, meta


def get_pull_request(
    owner: str,
    repo: str,
    pr_number: int,
) -> Dict[str, Any]:
    """
    Get detailed information about a specific pull request.

    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number

    Returns:
        Dictionary with detailed PR information including:
        - All fields from list_pull_requests
        - body (PR description)
        - head, base (branch information)
        - commits, additions, deletions, changed_files
        - mergeable, merged, merged_at

    Raises:
        GitHubRateLimitError: If rate limit exceeded
        requests.HTTPError: For other API errors (including 404 if PR not found)
    """
    data, meta = github_get(f"/repos/{owner}/{repo}/pulls/{pr_number}")

    return {
        "number": data.get("number"),
        "title": data.get("title"),
        "body": data.get("body"),
        "state": data.get("state"),
        "user": {
            "login": data.get("user", {}).get("login"),
            "avatar_url": data.get("user", {}).get("avatar_url"),
        },
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "html_url": data.get("html_url"),
        "draft": data.get("draft"),
        "mergeable": data.get("mergeable"),
        "mergeable_state": data.get("mergeable_state"),
        "merged": data.get("merged"),
        "merged_at": data.get("merged_at"),
        "head": {
            "ref": data.get("head", {}).get("ref"),
            "sha": data.get("head", {}).get("sha"),
        },
        "base": {
            "ref": data.get("base", {}).get("ref"),
            "sha": data.get("base", {}).get("sha"),
        },
        "commits": data.get("commits"),
        "additions": data.get("additions"),
        "deletions": data.get("deletions"),
        "changed_files": data.get("changed_files"),
        "labels": [label.get("name") for label in data.get("labels", [])],
        "rate_limit": meta,
    }


def list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    labels: Optional[List[str]] = None,
    per_page: int = 30,
    page: int = 1,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    List issues for a repository.

    Note: GitHub's API considers PRs as issues, so this may include PRs.
    Filter by checking if 'pull_request' key exists in results.

    Args:
        owner: Repository owner
        repo: Repository name
        state: Issue state - "open", "closed", or "all" (default: "open")
        labels: Filter by label names (optional)
        per_page: Results per page (default: 30, max: 100)
        page: Page number (default: 1)

    Returns:
        Tuple of (list of issue summaries, rate limit metadata)

    Each issue summary contains:
        - number, title, state
        - user (login, avatar_url)
        - created_at, updated_at
        - html_url
        - labels
        - is_pull_request (True if this is a PR, not an issue)

    Raises:
        GitHubRateLimitError: If rate limit exceeded
        requests.HTTPError: For other API errors
    """
    params = {
        "state": state,
        "per_page": min(per_page, 100),
        "page": page,
    }

    if labels:
        params["labels"] = ",".join(labels)

    data, meta = github_get(f"/repos/{owner}/{repo}/issues", params=params)

    issues = []
    for issue in data:
        issues.append({
            "number": issue.get("number"),
            "title": issue.get("title"),
            "state": issue.get("state"),
            "user": {
                "login": issue.get("user", {}).get("login"),
                "avatar_url": issue.get("user", {}).get("avatar_url"),
            },
            "created_at": issue.get("created_at"),
            "updated_at": issue.get("updated_at"),
            "html_url": issue.get("html_url"),
            "labels": [label.get("name") for label in issue.get("labels", [])],
            "is_pull_request": "pull_request" in issue,
        })

    return issues, meta


def get_latest_release(owner: str, repo: str) -> Optional[Dict[str, Any]]:
    """
    Get the latest release for a repository.

    Args:
        owner: Repository owner
        repo: Repository name

    Returns:
        Dictionary with release information, or None if no releases exist:
        - tag_name, name, body
        - created_at, published_at
        - html_url, tarball_url, zipball_url
        - prerelease, draft
        - author (login, avatar_url)

    Raises:
        GitHubRateLimitError: If rate limit exceeded
        requests.HTTPError: For other API errors (404 if no releases)
    """
    try:
        data, meta = github_get(f"/repos/{owner}/{repo}/releases/latest")

        return {
            "tag_name": data.get("tag_name"),
            "name": data.get("name"),
            "body": data.get("body"),
            "created_at": data.get("created_at"),
            "published_at": data.get("published_at"),
            "html_url": data.get("html_url"),
            "tarball_url": data.get("tarball_url"),
            "zipball_url": data.get("zipball_url"),
            "prerelease": data.get("prerelease"),
            "draft": data.get("draft"),
            "author": {
                "login": data.get("author", {}).get("login"),
                "avatar_url": data.get("author", {}).get("avatar_url"),
            },
            "rate_limit": meta,
        }
    except Exception as e:
        # If 404 or no releases, return None
        if "404" in str(e):
            return None
        raise


def get_repo_stats(owner: str, repo: str) -> Dict[str, Any]:
    """
    Get statistics and health metrics for a repository.

    Combines multiple API calls to provide a comprehensive stats overview.

    Args:
        owner: Repository owner
        repo: Repository name

    Returns:
        Dictionary with combined statistics:
        - Basic repo info (from get_repo_info)
        - open_prs_count, closed_prs_count
        - open_issues_count (excluding PRs)
        - latest_release (if exists)

    Raises:
        GitHubRateLimitError: If rate limit exceeded
        requests.HTTPError: For other API errors
    """
    # Get basic repo info
    repo_info = get_repo_info(owner, repo)

    # Get PR counts
    open_prs, _ = list_pull_requests(owner, repo, state="open", per_page=1)

    # Get latest release (may be None)
    latest_release = get_latest_release(owner, repo)

    return {
        "repository": {
            "name": repo_info["name"],
            "full_name": repo_info["full_name"],
            "description": repo_info["description"],
            "stars": repo_info["stars"],
            "forks": repo_info["forks"],
            "language": repo_info["language"],
            "html_url": repo_info["html_url"],
        },
        "activity": {
            "last_pushed": repo_info["pushed_at"],
            "last_updated": repo_info["updated_at"],
            "created": repo_info["created_at"],
        },
        "health": {
            "open_issues": repo_info["open_issues"],
            "archived": repo_info["archived"],
        },
        "latest_release": latest_release,
    }


def search_code(
    query: str,
    per_page: int = 30,
    page: int = 1,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Search for code across GitHub repositories.

    Note: Code search has a lower rate limit (30 requests/minute for authenticated users).

    Args:
        query: Search query (supports GitHub code search syntax)
        per_page: Results per page (default: 30, max: 100)
        page: Page number (default: 1)

    Returns:
        Tuple of (list of code results, rate limit metadata)

    Each result contains:
        - name, path, sha
        - repository (full_name, html_url)
        - html_url

    Example queries:
        - "repo:owner/repo filename:test.py"
        - "language:python TODO"
        - "org:myorg extension:js"

    Raises:
        GitHubRateLimitError: If rate limit exceeded
        requests.HTTPError: For other API errors
    """
    params = {
        "q": query,
        "per_page": min(per_page, 100),
        "page": page,
    }

    data, meta = github_get("/search/code", params=params)

    results = []
    for item in data.get("items", []):
        results.append({
            "name": item.get("name"),
            "path": item.get("path"),
            "sha": item.get("sha"),
            "repository": {
                "full_name": item.get("repository", {}).get("full_name"),
                "html_url": item.get("repository", {}).get("html_url"),
            },
            "html_url": item.get("html_url"),
        })

    return results, meta
