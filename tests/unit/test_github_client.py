"""
Unit tests for scripts.github_client

Tests the rate-limit-aware GitHub API client with mocked HTTP requests.
"""

import types
from typing import Any, Dict

import pytest

import scripts.github_client as github_client


class DummyResponse:
    """Mock response object for testing HTTP requests."""

    def __init__(
        self,
        status_code: int = 200,
        json_data: Any | None = None,
        headers: Dict[str, str] | None = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.headers = headers or {}
        self.text = text

    def json(self) -> Any:
        return self._json_data

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def raise_for_status(self) -> None:
        if not self.ok:
            raise RuntimeError(f"HTTP error {self.status_code}: {self.text}")


def test_auth_headers_uses_github_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that _auth_headers() correctly uses GITHUB_TOKEN from environment."""
    monkeypatch.setenv("GITHUB_TOKEN", "test-token-123")
    # Clear GH_TOKEN just in case
    monkeypatch.delenv("GH_TOKEN", raising=False)

    headers = github_client._auth_headers()
    assert headers["Authorization"] == "Bearer test-token-123"
    assert headers["Accept"].startswith("application/vnd.github+json")


def test_auth_headers_fallback_to_gh_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that _auth_headers() falls back to GH_TOKEN if GITHUB_TOKEN is not set."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("GH_TOKEN", "fallback-token-456")

    headers = github_client._auth_headers()
    assert headers["Authorization"] == "Bearer fallback-token-456"
    assert headers["Accept"].startswith("application/vnd.github+json")


def test_auth_headers_no_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that _auth_headers() works without a token (unauthenticated)."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)

    headers = github_client._auth_headers()
    assert "Authorization" not in headers
    assert headers["Accept"].startswith("application/vnd.github+json")


def test_github_get_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that github_get() correctly handles a successful API response."""
    calls: Dict[str, Any] = {}

    def fake_get(url: str, headers=None, params=None) -> DummyResponse:  # type: ignore[override]
        calls["url"] = url
        calls["headers"] = headers
        calls["params"] = params
        return DummyResponse(
            status_code=200,
            json_data={"ok": True},
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Reset": "1234567890",
            },
        )

    monkeypatch.setattr(github_client, "requests", types.SimpleNamespace(get=fake_get))

    data, meta = github_client.github_get("/rate_limit", params={"foo": "bar"})

    assert data == {"ok": True}
    assert meta["limit"] == "5000"
    assert meta["remaining"] == "4999"
    assert meta["reset"] == "1234567890"

    # Verify URL and params were passed through.
    assert calls["url"].endswith("/rate_limit")
    assert calls["params"] == {"foo": "bar"}


def test_github_get_full_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that github_get() handles full URLs correctly."""
    calls: Dict[str, Any] = {}

    def fake_get(url: str, headers=None, params=None) -> DummyResponse:  # type: ignore[override]
        calls["url"] = url
        return DummyResponse(
            status_code=200,
            json_data={"result": "test"},
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Reset": "1234567890",
            },
        )

    monkeypatch.setattr(github_client, "requests", types.SimpleNamespace(get=fake_get))

    full_url = "https://api.github.com/repos/owner/repo"
    data, meta = github_client.github_get(full_url)

    assert data == {"result": "test"}
    assert calls["url"] == full_url


def test_github_get_rate_limit_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that github_get() raises GitHubRateLimitError when rate limit is exceeded."""

    def fake_get(url: str, headers=None, params=None) -> DummyResponse:  # type: ignore[override]
        return DummyResponse(
            status_code=403,
            text="rate limit exceeded",
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "9999999999",  # Far future
            },
        )

    # Mock both requests and time.sleep to avoid actual delays
    monkeypatch.setattr(github_client, "requests", types.SimpleNamespace(get=fake_get))
    monkeypatch.setattr(github_client.time, "sleep", lambda x: None)

    with pytest.raises(github_client.GitHubRateLimitError) as exc_info:
        github_client.github_get("/test", max_retries=2)

    assert "rate limit exceeded" in str(exc_info.value).lower()
