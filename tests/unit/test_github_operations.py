"""
Unit tests for scripts.github_operations

Tests high-level GitHub operations with mocked client responses.
"""

import types
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

import scripts.github_operations as github_ops
import scripts.github_client as github_client


@pytest.fixture
def mock_github_get(monkeypatch):
    """Fixture to mock github_get calls with controlled responses."""
    responses = []
    call_log = []

    def fake_get(path: str, params=None, max_retries=5):
        call_log.append({"path": path, "params": params})
        if responses:
            return responses.pop(0)
        # Default response
        return {"default": "response"}, {"limit": "5000", "remaining": "4999", "reset": "123456"}

    # Patch in the github_operations module where it's imported
    monkeypatch.setattr(github_ops, "github_get", fake_get)
    return {"responses": responses, "calls": call_log}


def test_get_repo_info(mock_github_get):
    """Test fetching repository information."""
    mock_github_get["responses"].append((
        {
            "name": "test-repo",
            "full_name": "owner/test-repo",
            "description": "A test repository",
            "stargazers_count": 42,
            "forks_count": 7,
            "watchers_count": 15,
            "open_issues_count": 3,
            "default_branch": "main",
            "language": "Python",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-11-26T00:00:00Z",
            "pushed_at": "2024-11-26T12:00:00Z",
            "html_url": "https://github.com/owner/test-repo",
            "clone_url": "https://github.com/owner/test-repo.git",
            "private": False,
            "archived": False,
        },
        {"limit": "5000", "remaining": "4998", "reset": "123456"}
    ))

    result = github_ops.get_repo_info("owner", "test-repo")

    assert result["name"] == "test-repo"
    assert result["stars"] == 42
    assert result["language"] == "Python"
    assert result["private"] is False
    assert result["rate_limit"]["remaining"] == "4998"
    assert mock_github_get["calls"][0]["path"] == "/repos/owner/test-repo"


def test_list_pull_requests(mock_github_get):
    """Test listing pull requests."""
    mock_github_get["responses"].append((
        [
            {
                "number": 123,
                "title": "Fix critical bug",
                "state": "open",
                "user": {
                    "login": "contributor",
                    "avatar_url": "https://avatars.github.com/u/1234"
                },
                "created_at": "2024-11-20T00:00:00Z",
                "updated_at": "2024-11-25T00:00:00Z",
                "html_url": "https://github.com/owner/repo/pull/123",
                "draft": False,
                "mergeable_state": "clean",
                "labels": [{"name": "bug"}, {"name": "critical"}],
            },
            {
                "number": 124,
                "title": "Add new feature",
                "state": "open",
                "user": {
                    "login": "developer",
                    "avatar_url": "https://avatars.github.com/u/5678"
                },
                "created_at": "2024-11-21T00:00:00Z",
                "updated_at": "2024-11-26T00:00:00Z",
                "html_url": "https://github.com/owner/repo/pull/124",
                "draft": True,
                "mergeable_state": "unstable",
                "labels": [{"name": "enhancement"}],
            },
        ],
        {"limit": "5000", "remaining": "4997", "reset": "123456"}
    ))

    prs, meta = github_ops.list_pull_requests("owner", "repo", state="open")

    assert len(prs) == 2
    assert prs[0]["number"] == 123
    assert prs[0]["title"] == "Fix critical bug"
    assert prs[0]["user"]["login"] == "contributor"
    assert prs[0]["labels"] == ["bug", "critical"]
    assert prs[1]["draft"] is True
    assert meta["remaining"] == "4997"

    # Verify API call
    call = mock_github_get["calls"][0]
    assert call["path"] == "/repos/owner/repo/pulls"
    assert call["params"]["state"] == "open"
    assert call["params"]["per_page"] == 30


def test_get_pull_request(mock_github_get):
    """Test fetching detailed pull request information."""
    mock_github_get["responses"].append((
        {
            "number": 456,
            "title": "Refactor authentication",
            "body": "This PR refactors the auth system to use OAuth2.",
            "state": "open",
            "user": {
                "login": "security-expert",
                "avatar_url": "https://avatars.github.com/u/9999"
            },
            "created_at": "2024-11-15T00:00:00Z",
            "updated_at": "2024-11-26T00:00:00Z",
            "html_url": "https://github.com/owner/repo/pull/456",
            "draft": False,
            "mergeable": True,
            "mergeable_state": "clean",
            "merged": False,
            "merged_at": None,
            "head": {
                "ref": "feature/oauth2",
                "sha": "abc123def456",
            },
            "base": {
                "ref": "main",
                "sha": "789ghi012jkl",
            },
            "commits": 7,
            "additions": 234,
            "deletions": 89,
            "changed_files": 12,
            "labels": [{"name": "security"}, {"name": "breaking-change"}],
        },
        {"limit": "5000", "remaining": "4996", "reset": "123456"}
    ))

    result = github_ops.get_pull_request("owner", "repo", 456)

    assert result["number"] == 456
    assert result["title"] == "Refactor authentication"
    assert "OAuth2" in result["body"]
    assert result["mergeable"] is True
    assert result["merged"] is False
    assert result["head"]["ref"] == "feature/oauth2"
    assert result["base"]["ref"] == "main"
    assert result["commits"] == 7
    assert result["additions"] == 234
    assert result["deletions"] == 89
    assert result["changed_files"] == 12
    assert result["labels"] == ["security", "breaking-change"]

    assert mock_github_get["calls"][0]["path"] == "/repos/owner/repo/pulls/456"


def test_list_issues(mock_github_get):
    """Test listing issues (may include PRs)."""
    mock_github_get["responses"].append((
        [
            {
                "number": 42,
                "title": "Documentation improvements",
                "state": "open",
                "user": {
                    "login": "doc-writer",
                    "avatar_url": "https://avatars.github.com/u/1111"
                },
                "created_at": "2024-11-10T00:00:00Z",
                "updated_at": "2024-11-20T00:00:00Z",
                "html_url": "https://github.com/owner/repo/issues/42",
                "labels": [{"name": "documentation"}],
            },
            {
                "number": 43,
                "title": "Some PR disguised as issue",
                "state": "open",
                "user": {
                    "login": "pr-creator",
                    "avatar_url": "https://avatars.github.com/u/2222"
                },
                "created_at": "2024-11-11T00:00:00Z",
                "updated_at": "2024-11-21T00:00:00Z",
                "html_url": "https://github.com/owner/repo/issues/43",
                "labels": [],
                "pull_request": {"url": "https://api.github.com/repos/owner/repo/pulls/43"},
            },
        ],
        {"limit": "5000", "remaining": "4995", "reset": "123456"}
    ))

    issues, meta = github_ops.list_issues("owner", "repo", state="open")

    assert len(issues) == 2
    assert issues[0]["number"] == 42
    assert issues[0]["is_pull_request"] is False
    assert issues[1]["number"] == 43
    assert issues[1]["is_pull_request"] is True

    call = mock_github_get["calls"][0]
    assert call["path"] == "/repos/owner/repo/issues"
    assert call["params"]["state"] == "open"


def test_list_issues_with_labels(mock_github_get):
    """Test filtering issues by labels."""
    mock_github_get["responses"].append((
        [],
        {"limit": "5000", "remaining": "4994", "reset": "123456"}
    ))

    issues, meta = github_ops.list_issues("owner", "repo", labels=["bug", "critical"])

    call = mock_github_get["calls"][0]
    assert call["params"]["labels"] == "bug,critical"


def test_get_latest_release(mock_github_get):
    """Test fetching latest release information."""
    mock_github_get["responses"].append((
        {
            "tag_name": "v1.2.3",
            "name": "Release 1.2.3",
            "body": "## Changes\n- Fixed bug #42\n- Added feature X",
            "created_at": "2024-11-01T00:00:00Z",
            "published_at": "2024-11-01T10:00:00Z",
            "html_url": "https://github.com/owner/repo/releases/tag/v1.2.3",
            "tarball_url": "https://api.github.com/repos/owner/repo/tarball/v1.2.3",
            "zipball_url": "https://api.github.com/repos/owner/repo/zipball/v1.2.3",
            "prerelease": False,
            "draft": False,
            "author": {
                "login": "maintainer",
                "avatar_url": "https://avatars.github.com/u/3333"
            },
        },
        {"limit": "5000", "remaining": "4993", "reset": "123456"}
    ))

    result = github_ops.get_latest_release("owner", "repo")

    assert result["tag_name"] == "v1.2.3"
    assert result["name"] == "Release 1.2.3"
    assert "Fixed bug #42" in result["body"]
    assert result["prerelease"] is False
    assert result["author"]["login"] == "maintainer"

    assert mock_github_get["calls"][0]["path"] == "/repos/owner/repo/releases/latest"


def test_get_latest_release_none_exists(monkeypatch):
    """Test handling when no releases exist."""
    def fake_get_raising(path: str, params=None, max_retries=5):
        raise Exception("404: Not Found")

    monkeypatch.setattr(github_ops, "github_get", fake_get_raising)

    result = github_ops.get_latest_release("owner", "repo")
    assert result is None


def test_search_code(mock_github_get):
    """Test code search functionality."""
    mock_github_get["responses"].append((
        {
            "total_count": 2,
            "incomplete_results": False,
            "items": [
                {
                    "name": "auth.py",
                    "path": "src/auth.py",
                    "sha": "abc123",
                    "repository": {
                        "full_name": "owner/repo",
                        "html_url": "https://github.com/owner/repo",
                    },
                    "html_url": "https://github.com/owner/repo/blob/main/src/auth.py",
                },
                {
                    "name": "config.py",
                    "path": "src/config.py",
                    "sha": "def456",
                    "repository": {
                        "full_name": "owner/repo",
                        "html_url": "https://github.com/owner/repo",
                    },
                    "html_url": "https://github.com/owner/repo/blob/main/src/config.py",
                },
            ],
        },
        {"limit": "30", "remaining": "29", "reset": "123456"}
    ))

    results, meta = github_ops.search_code("repo:owner/repo TODO")

    assert len(results) == 2
    assert results[0]["name"] == "auth.py"
    assert results[0]["path"] == "src/auth.py"
    assert results[0]["repository"]["full_name"] == "owner/repo"

    call = mock_github_get["calls"][0]
    assert call["path"] == "/search/code"
    assert call["params"]["q"] == "repo:owner/repo TODO"


def test_get_repo_stats_integration(mock_github_get):
    """Test combined statistics gathering."""
    # Mock get_repo_info response
    mock_github_get["responses"].append((
        {
            "name": "stats-repo",
            "full_name": "owner/stats-repo",
            "description": "Testing stats",
            "stargazers_count": 100,
            "forks_count": 20,
            "watchers_count": 50,
            "open_issues_count": 5,
            "default_branch": "main",
            "language": "JavaScript",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2024-11-26T00:00:00Z",
            "pushed_at": "2024-11-26T14:00:00Z",
            "html_url": "https://github.com/owner/stats-repo",
            "clone_url": "https://github.com/owner/stats-repo.git",
            "private": False,
            "archived": False,
        },
        {"limit": "5000", "remaining": "4990", "reset": "123456"}
    ))

    # Mock list_pull_requests response
    mock_github_get["responses"].append((
        [],
        {"limit": "5000", "remaining": "4989", "reset": "123456"}
    ))

    # Mock get_latest_release response
    mock_github_get["responses"].append((
        {
            "tag_name": "v2.0.0",
            "name": "Major Release",
            "body": "Big changes",
            "created_at": "2024-11-01T00:00:00Z",
            "published_at": "2024-11-01T10:00:00Z",
            "html_url": "https://github.com/owner/stats-repo/releases/tag/v2.0.0",
            "tarball_url": "https://api.github.com/repos/owner/stats-repo/tarball/v2.0.0",
            "zipball_url": "https://api.github.com/repos/owner/stats-repo/zipball/v2.0.0",
            "prerelease": False,
            "draft": False,
            "author": {
                "login": "owner",
                "avatar_url": "https://avatars.github.com/u/1"
            },
        },
        {"limit": "5000", "remaining": "4988", "reset": "123456"}
    ))

    result = github_ops.get_repo_stats("owner", "stats-repo")

    assert result["repository"]["name"] == "stats-repo"
    assert result["repository"]["stars"] == 100
    assert result["repository"]["language"] == "JavaScript"
    assert result["activity"]["last_pushed"] == "2024-11-26T14:00:00Z"
    assert result["health"]["open_issues"] == 5
    assert result["health"]["archived"] is False
    assert result["latest_release"]["tag_name"] == "v2.0.0"

    # Verify all three API calls were made
    assert len(mock_github_get["calls"]) == 3
