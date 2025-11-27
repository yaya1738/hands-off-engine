#!/usr/bin/env python3
"""
Unit tests for GitHub client module.

Run with:
    python3 -m pytest tests/unit/test_github_client.py -v
    
Or directly:
    python3 tests/unit/test_github_client.py
"""

import os
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError
from io import BytesIO

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.github_client import (
    GitHubClient,
    GitHubAuthError,
    GitHubClientError,
    GitHubRateLimitError,
    RateLimitInfo,
    check_github_auth
)


class TestRateLimitInfo(unittest.TestCase):
    """Tests for RateLimitInfo dataclass."""
    
    def test_reset_in_seconds_future(self):
        """Test reset_in_seconds when reset is in the future."""
        import time
        future = int(time.time()) + 3600  # 1 hour from now
        info = RateLimitInfo(limit=5000, remaining=4000, reset_timestamp=future, used=1000)
        self.assertGreater(info.reset_in_seconds, 3500)
        self.assertLessEqual(info.reset_in_seconds, 3600)
    
    def test_reset_in_seconds_past(self):
        """Test reset_in_seconds when reset is in the past."""
        import time
        past = int(time.time()) - 100
        info = RateLimitInfo(limit=5000, remaining=4000, reset_timestamp=past, used=1000)
        self.assertEqual(info.reset_in_seconds, 0)
    
    def test_is_exhausted_true(self):
        """Test is_exhausted when remaining is 0."""
        info = RateLimitInfo(limit=5000, remaining=0, reset_timestamp=0, used=5000)
        self.assertTrue(info.is_exhausted)
    
    def test_is_exhausted_false(self):
        """Test is_exhausted when remaining > 0."""
        info = RateLimitInfo(limit=5000, remaining=100, reset_timestamp=0, used=4900)
        self.assertFalse(info.is_exhausted)


class TestGitHubClientInit(unittest.TestCase):
    """Tests for GitHubClient initialization."""
    
    def test_init_with_token_arg(self):
        """Test initialization with token passed as argument."""
        client = GitHubClient(token="ghp_test123")
        self.assertEqual(client.token, "ghp_test123")
    
    @patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_env_token"})
    def test_init_with_env_token(self):
        """Test initialization with token from environment."""
        client = GitHubClient()
        self.assertEqual(client.token, "ghp_env_token")
    
    @patch.dict(os.environ, {}, clear=True)
    def test_init_no_token_raises(self):
        """Test that missing token raises GitHubAuthError."""
        with self.assertRaises(GitHubAuthError):
            GitHubClient()
    
    def test_init_custom_settings(self):
        """Test initialization with custom settings."""
        client = GitHubClient(
            token="ghp_test",
            base_url="https://custom.github.com/api",
            max_retries=5,
            backoff_factor=3
        )
        self.assertEqual(client.base_url, "https://custom.github.com/api")
        self.assertEqual(client.max_retries, 5)
        self.assertEqual(client.backoff_factor, 3)
    
    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base_url."""
        client = GitHubClient(token="ghp_test", base_url="https://api.github.com/")
        self.assertEqual(client.base_url, "https://api.github.com")


class TestGitHubClientRequests(unittest.TestCase):
    """Tests for GitHubClient request methods."""
    
    def setUp(self):
        """Set up test client."""
        self.client = GitHubClient(token="ghp_test_token")
    
    def _mock_response(self, data, headers=None):
        """Create a mock response object."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(data).encode("utf-8")
        mock_response.headers = headers or {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Reset": "1700000000",
            "X-RateLimit-Used": "1"
        }
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response
    
    @patch("scripts.github_client.urlopen")
    def test_get_rate_limit(self, mock_urlopen):
        """Test get_rate_limit method."""
        mock_urlopen.return_value = self._mock_response({
            "resources": {
                "core": {
                    "limit": 5000,
                    "remaining": 4500,
                    "used": 500,
                    "reset": 1700000000
                }
            }
        })
        
        info = self.client.get_rate_limit()
        
        self.assertEqual(info.limit, 5000)
        self.assertEqual(info.remaining, 4500)
        self.assertEqual(info.used, 500)
    
    @patch("scripts.github_client.urlopen")
    def test_get_user(self, mock_urlopen):
        """Test get_user method."""
        mock_urlopen.return_value = self._mock_response({
            "login": "testuser",
            "name": "Test User",
            "email": "test@example.com"
        })
        
        user = self.client.get_user()
        
        self.assertEqual(user["login"], "testuser")
        self.assertEqual(user["name"], "Test User")
    
    @patch("scripts.github_client.urlopen")
    def test_is_authenticated_true(self, mock_urlopen):
        """Test is_authenticated returns True when auth works."""
        mock_urlopen.return_value = self._mock_response({"login": "testuser"})
        
        self.assertTrue(self.client.is_authenticated())
    
    @patch("scripts.github_client.urlopen")
    def test_is_authenticated_false_on_error(self, mock_urlopen):
        """Test is_authenticated returns False on auth error."""
        mock_urlopen.side_effect = HTTPError(
            url="https://api.github.com/user",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=None
        )
        
        self.assertFalse(self.client.is_authenticated())
    
    @patch("scripts.github_client.urlopen")
    def test_auth_error_raises(self, mock_urlopen):
        """Test that 401 response raises GitHubAuthError."""
        mock_urlopen.side_effect = HTTPError(
            url="https://api.github.com/user",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=None
        )
        
        with self.assertRaises(GitHubAuthError):
            self.client._make_request("/user")
    
    @patch("scripts.github_client.urlopen")
    def test_rate_limit_error_raises(self, mock_urlopen):
        """Test that rate limit exceeded raises GitHubRateLimitError."""
        headers = MagicMock()
        headers.get = lambda key, default="": {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "1700000000"
        }.get(key, default)
        
        error = HTTPError(
            url="https://api.github.com/rate_limit",
            code=403,
            msg="Forbidden",
            hdrs=headers,
            fp=None
        )
        error.headers = headers
        mock_urlopen.side_effect = error
        
        with self.assertRaises(GitHubRateLimitError):
            self.client._make_request("/rate_limit")
    
    @patch("scripts.github_client.urlopen")
    def test_not_found_raises(self, mock_urlopen):
        """Test that 404 response raises GitHubClientError."""
        mock_urlopen.side_effect = HTTPError(
            url="https://api.github.com/notfound",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None
        )
        
        with self.assertRaises(GitHubClientError):
            self.client._make_request("/notfound")
    
    @patch("scripts.github_client.urlopen")
    @patch("scripts.github_client.time.sleep")
    def test_retry_on_server_error(self, mock_sleep, mock_urlopen):
        """Test that server errors trigger retries."""
        # First two calls fail, third succeeds
        mock_urlopen.side_effect = [
            HTTPError("url", 500, "Server Error", {}, None),
            HTTPError("url", 502, "Bad Gateway", {}, None),
            self._mock_response({"data": "success"})
        ]
        
        result = self.client._make_request("/test")
        
        self.assertEqual(result["data"], "success")
        self.assertEqual(mock_sleep.call_count, 2)  # Two retries before success
    
    @patch("scripts.github_client.urlopen")
    @patch("scripts.github_client.time.sleep")
    def test_retry_exhausted_raises(self, mock_sleep, mock_urlopen):
        """Test that exhausted retries raise GitHubClientError."""
        mock_urlopen.side_effect = HTTPError("url", 500, "Server Error", {}, None)
        
        with self.assertRaises(GitHubClientError):
            self.client._make_request("/test")
        
        # Sleep is called after each failed attempt (max_retries total attempts)
        self.assertEqual(mock_sleep.call_count, self.client.max_retries)


class TestCheckGitHubAuth(unittest.TestCase):
    """Tests for check_github_auth utility function."""
    
    @patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_valid"})
    @patch("scripts.github_client.urlopen")
    def test_returns_true_when_authenticated(self, mock_urlopen):
        """Test check_github_auth returns True when auth works."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"login": "user"}'
        mock_response.headers = {"X-RateLimit-Limit": "5000"}
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        self.assertTrue(check_github_auth())
    
    @patch.dict(os.environ, {}, clear=True)
    def test_returns_false_when_no_token(self):
        """Test check_github_auth returns False when no token."""
        self.assertFalse(check_github_auth())


class TestCachedRateLimit(unittest.TestCase):
    """Tests for cached rate limit functionality."""
    
    def test_cached_rate_limit_initially_none(self):
        """Test that cached_rate_limit is None initially."""
        client = GitHubClient(token="ghp_test")
        self.assertIsNone(client.cached_rate_limit)
    
    @patch("scripts.github_client.urlopen")
    def test_cached_rate_limit_updated_after_request(self, mock_urlopen):
        """Test that cached_rate_limit is updated after a request."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"resources": {"core": {"limit": 5000, "remaining": 4000, "used": 1000, "reset": 0}}}'
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4000",
            "X-RateLimit-Reset": "1700000000",
            "X-RateLimit-Used": "1000"
        }
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        client = GitHubClient(token="ghp_test")
        client.get_rate_limit()
        
        cached = client.cached_rate_limit
        self.assertIsNotNone(cached)
        self.assertEqual(cached.limit, 5000)
        self.assertEqual(cached.remaining, 4000)


if __name__ == "__main__":
    unittest.main()
