"""
Unit tests for GitHub client and rate limit status modules.

Tests the GitHub API client functionality with mocking.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from github_client import (
    GitHubClient,
    GitHubClientError,
    RateLimitExceededError,
    AuthenticationError,
    RateLimitInfo,
    get_github_client,
)
from github_ratelimit_status import (
    get_rate_limit,
    format_reset_time,
)


class TestRateLimitInfo:
    """Test RateLimitInfo dataclass."""

    def test_rate_limit_info_properties(self):
        """Test RateLimitInfo properties."""
        info = RateLimitInfo(
            limit=5000,
            remaining=4500,
            reset_timestamp=1700000000,
            used=500,
        )
        
        assert info.limit == 5000
        assert info.remaining == 4500
        assert info.used == 500
        assert info.is_exhausted() is False

    def test_rate_limit_exhausted(self):
        """Test exhausted rate limit detection."""
        info = RateLimitInfo(
            limit=5000,
            remaining=0,
            reset_timestamp=1700000000,
        )
        
        assert info.is_exhausted() is True


class TestGitHubClient:
    """Test GitHubClient class."""

    def test_client_init_with_token(self):
        """Test client initialization with token."""
        client = GitHubClient(token="test_token")
        
        assert client.token == "test_token"
        assert client.is_authenticated is True

    def test_client_init_from_env(self, monkeypatch):
        """Test client initialization from environment."""
        monkeypatch.setenv("GITHUB_TOKEN", "env_token")
        
        client = GitHubClient()
        
        assert client.token == "env_token"
        assert client.is_authenticated is True

    def test_client_init_no_token(self, monkeypatch):
        """Test client initialization without token."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        
        client = GitHubClient()
        
        assert client.token is None
        assert client.is_authenticated is False

    def test_build_headers_authenticated(self):
        """Test header building with authentication."""
        client = GitHubClient(token="test_token")
        headers = client._build_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["Accept"] == "application/vnd.github+json"

    def test_build_headers_unauthenticated(self, monkeypatch):
        """Test header building without authentication."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        
        client = GitHubClient()
        headers = client._build_headers()
        
        assert "Authorization" not in headers
        assert headers["Accept"] == "application/vnd.github+json"

    def test_parse_rate_limit_headers(self):
        """Test parsing rate limit from response headers."""
        client = GitHubClient(token="test")
        
        headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Reset": "1700000000",
            "X-RateLimit-Used": "1",
        }
        
        info = client._parse_rate_limit_headers(headers)
        
        assert info is not None
        assert info.limit == 5000
        assert info.remaining == 4999
        assert info.used == 1

    def test_parse_rate_limit_headers_missing(self):
        """Test parsing when rate limit headers are missing."""
        client = GitHubClient(token="test")
        
        headers = {}
        info = client._parse_rate_limit_headers(headers)
        
        assert info is None

    def test_get_stats(self):
        """Test getting client statistics."""
        client = GitHubClient(token="test")
        stats = client.get_stats()
        
        assert stats["authenticated"] is True
        assert stats["request_count"] == 0


class TestGitHubClientRequests:
    """Test GitHubClient request methods with mocking."""

    @patch("github_client.urlopen")
    def test_get_request_success(self, mock_urlopen):
        """Test successful GET request."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"key": "value"}'
        mock_response.getheaders.return_value = [
            ("X-RateLimit-Limit", "5000"),
            ("X-RateLimit-Remaining", "4999"),
            ("X-RateLimit-Reset", "1700000000"),
            ("X-RateLimit-Used", "1"),
        ]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        client = GitHubClient(token="test", log_requests=False)
        result = client.get("/test")
        
        assert result == {"key": "value"}
        assert client._request_count == 1
        assert client.rate_limit is not None
        assert client.rate_limit.remaining == 4999


class TestGetGitHubClient:
    """Test get_github_client convenience function."""

    def test_get_github_client(self, monkeypatch):
        """Test getting a client instance."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        
        client = get_github_client()
        
        assert isinstance(client, GitHubClient)
        assert client.is_authenticated is True


class TestFormatResetTime:
    """Test format_reset_time function."""

    @patch("github_ratelimit_status.datetime")
    def test_format_reset_time_future(self, mock_datetime):
        """Test formatting a future reset time."""
        from datetime import datetime, timezone, timedelta
        
        now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = now
        mock_datetime.fromtimestamp.return_value = now + timedelta(minutes=5, seconds=30)
        
        result = format_reset_time(1234567890)
        
        assert "5m" in result or "30s" in result


class TestRateLimitStatus:
    """Test get_rate_limit function."""

    @patch("github_ratelimit_status.urlopen")
    def test_get_rate_limit_success(self, mock_urlopen, monkeypatch):
        """Test successful rate limit fetch."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "resources": {
                "core": {
                    "limit": 5000,
                    "remaining": 4500,
                    "reset": 1700000000,
                    "used": 500,
                }
            }
        }).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        
        result = get_rate_limit()
        
        assert result["success"] is True
        assert result["authenticated"] is True
        assert result["resources"]["core"]["limit"] == 5000

    def test_get_rate_limit_no_token(self, monkeypatch):
        """Test rate limit without token (unauthenticated)."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        
        # This will actually try to hit the API but that's fine for testing
        # the logic path - the result will be authenticated=False
        result = get_rate_limit(token=None)
        
        # Just verify the structure
        assert "authenticated" in result
        assert result["authenticated"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
