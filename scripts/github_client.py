#!/usr/bin/env python3
"""
Authenticated GitHub API Client with Rate Limit Handling

Features:
- Automatic authentication via GITHUB_TOKEN environment variable
- Rate limit awareness (checks before requests, waits if needed)
- Retry logic with exponential backoff
- Logging of API usage
"""
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("github_client")


@dataclass
class RateLimitInfo:
    """GitHub API rate limit information."""
    limit: int
    remaining: int
    reset_timestamp: int
    used: int = 0
    
    @property
    def reset_datetime(self) -> datetime:
        """Get reset time as datetime."""
        return datetime.fromtimestamp(self.reset_timestamp, tz=timezone.utc)
    
    @property
    def seconds_until_reset(self) -> float:
        """Get seconds until rate limit resets."""
        now = datetime.now(timezone.utc)
        delta = self.reset_datetime - now
        return max(0, delta.total_seconds())
    
    def is_exhausted(self) -> bool:
        """Check if rate limit is exhausted."""
        return self.remaining <= 0


class GitHubClientError(Exception):
    """Base exception for GitHub client errors."""
    pass


class RateLimitExceededError(GitHubClientError):
    """Raised when rate limit is exceeded and wait is not desired."""
    def __init__(self, rate_info: RateLimitInfo):
        self.rate_info = rate_info
        super().__init__(
            f"Rate limit exceeded. Resets in {rate_info.seconds_until_reset:.0f} seconds"
        )


class AuthenticationError(GitHubClientError):
    """Raised when authentication fails."""
    pass


class GitHubClient:
    """
    Authenticated GitHub API client with rate limiting.
    
    Usage:
        client = GitHubClient()  # Uses GITHUB_TOKEN from env
        data = client.get("/repos/owner/repo")
        
        # Or with explicit token
        client = GitHubClient(token="ghp_...")
    """
    
    BASE_URL = "https://api.github.com"
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2  # seconds
    
    # Rate limit safety margin (don't use last N requests)
    RATE_LIMIT_BUFFER = 10
    
    def __init__(
        self,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        wait_on_rate_limit: bool = True,
        log_requests: bool = True,
    ):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub token. If None, uses GITHUB_TOKEN from environment.
            base_url: API base URL. Defaults to https://api.github.com
            wait_on_rate_limit: If True, wait when rate limit is low instead of failing.
            log_requests: If True, log API requests.
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.base_url = base_url or os.environ.get("GITHUB_API_URL", self.BASE_URL)
        self.wait_on_rate_limit = wait_on_rate_limit
        self.log_requests = log_requests
        
        # Track rate limit info from response headers
        self._rate_info: Optional[RateLimitInfo] = None
        self._request_count = 0
        
        if not self.token:
            logger.warning(
                "GITHUB_TOKEN not set. Using unauthenticated access (60 req/hour). "
                "Run scripts/setup_github_token.sh to configure."
            )
    
    @property
    def is_authenticated(self) -> bool:
        """Check if client has a token configured."""
        return bool(self.token)
    
    @property
    def rate_limit(self) -> Optional[RateLimitInfo]:
        """Get current rate limit info (from last request)."""
        return self._rate_info
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers."""
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Hands-Off-Engine-GitHub-Client",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        return headers
    
    def _parse_rate_limit_headers(self, headers: Dict[str, str]) -> Optional[RateLimitInfo]:
        """Parse rate limit info from response headers."""
        try:
            limit = int(headers.get("X-RateLimit-Limit", 0))
            remaining = int(headers.get("X-RateLimit-Remaining", 0))
            reset = int(headers.get("X-RateLimit-Reset", 0))
            used = int(headers.get("X-RateLimit-Used", 0))
            
            if limit > 0:
                return RateLimitInfo(
                    limit=limit,
                    remaining=remaining,
                    reset_timestamp=reset,
                    used=used,
                )
        except (ValueError, TypeError):
            pass
        return None
    
    def _check_rate_limit(self) -> None:
        """Check rate limit and wait if necessary."""
        if self._rate_info is None:
            return
        
        if self._rate_info.remaining <= self.RATE_LIMIT_BUFFER:
            if self.wait_on_rate_limit:
                wait_time = self._rate_info.seconds_until_reset + 1
                logger.warning(
                    f"Rate limit nearly exhausted ({self._rate_info.remaining} remaining). "
                    f"Waiting {wait_time:.0f} seconds until reset."
                )
                time.sleep(wait_time)
            else:
                raise RateLimitExceededError(self._rate_info)
    
    def _make_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Tuple[int, Dict[str, str], bytes]:
        """
        Make HTTP request to GitHub API.
        
        Returns:
            Tuple of (status_code, headers, body)
        """
        url = urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))
        
        if params:
            from urllib.parse import urlencode
            url = f"{url}?{urlencode(params)}"
        
        headers = self._build_headers()
        body = None
        
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        
        req = Request(url, data=body, headers=headers, method=method)
        
        try:
            with urlopen(req, timeout=30) as response:
                response_headers = dict(response.getheaders())
                response_body = response.read()
                return response.status, response_headers, response_body
        except HTTPError as e:
            response_headers = dict(e.headers) if e.headers else {}
            response_body = e.read() if hasattr(e, "read") else b""
            return e.code, response_headers, response_body
    
    def request(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make authenticated request to GitHub API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            path: API path (e.g., "/repos/owner/repo")
            data: Request body data (for POST/PUT/PATCH)
            params: Query parameters
            
        Returns:
            Parsed JSON response
            
        Raises:
            GitHubClientError: On API errors
        """
        # Check rate limit before making request
        self._check_rate_limit()
        
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                if self.log_requests:
                    logger.debug(f"{method} {path} (attempt {attempt + 1})")
                
                status, headers, body = self._make_request(method, path, data, params)
                
                # Update rate limit info from headers
                rate_info = self._parse_rate_limit_headers(headers)
                if rate_info:
                    self._rate_info = rate_info
                
                self._request_count += 1
                
                # Log request
                if self.log_requests:
                    remaining = self._rate_info.remaining if self._rate_info else "?"
                    logger.info(
                        f"{method} {path} -> {status} "
                        f"(rate limit: {remaining} remaining)"
                    )
                
                # Handle response
                if 200 <= status < 300:
                    if body:
                        return json.loads(body.decode("utf-8"))
                    return {}
                
                # Handle rate limit exceeded
                if status == 403 and self._rate_info and self._rate_info.is_exhausted():
                    if self.wait_on_rate_limit:
                        wait_time = self._rate_info.seconds_until_reset + 1
                        logger.warning(
                            f"Rate limit exceeded. Waiting {wait_time:.0f} seconds."
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        raise RateLimitExceededError(self._rate_info)
                
                # Handle authentication errors
                if status == 401:
                    raise AuthenticationError(
                        "GitHub authentication failed. Check your GITHUB_TOKEN."
                    )
                
                # Handle server errors with retry
                if status >= 500:
                    wait_time = self.RETRY_BACKOFF_BASE ** attempt
                    logger.warning(
                        f"Server error {status}. Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue
                
                # Client error - don't retry
                error_msg = body.decode("utf-8") if body else "Unknown error"
                raise GitHubClientError(f"GitHub API error {status}: {error_msg}")
                
            except (URLError, TimeoutError) as e:
                last_error = e
                wait_time = self.RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    f"Network error: {e}. Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
        
        raise GitHubClientError(f"Request failed after {self.MAX_RETRIES} retries: {last_error}")
    
    def get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request."""
        return self.request("GET", path, params=params)
    
    def post(self, path: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request."""
        return self.request("POST", path, data=data)
    
    def put(self, path: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make PUT request."""
        return self.request("PUT", path, data=data)
    
    def patch(self, path: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make PATCH request."""
        return self.request("PATCH", path, data=data)
    
    def delete(self, path: str) -> Dict[str, Any]:
        """Make DELETE request."""
        return self.request("DELETE", path)
    
    def get_rate_limit(self) -> RateLimitInfo:
        """Fetch current rate limit from API."""
        data = self.get("/rate_limit")
        core = data.get("resources", {}).get("core", {})
        
        self._rate_info = RateLimitInfo(
            limit=core.get("limit", 0),
            remaining=core.get("remaining", 0),
            reset_timestamp=core.get("reset", 0),
            used=core.get("used", 0),
        )
        
        return self._rate_info
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client usage statistics."""
        return {
            "authenticated": self.is_authenticated,
            "request_count": self._request_count,
            "rate_limit": {
                "limit": self._rate_info.limit if self._rate_info else None,
                "remaining": self._rate_info.remaining if self._rate_info else None,
                "reset_in_seconds": (
                    self._rate_info.seconds_until_reset if self._rate_info else None
                ),
            } if self._rate_info else None,
        }


# Convenience function for simple usage
def get_github_client(**kwargs) -> GitHubClient:
    """
    Get a configured GitHub client instance.
    
    Usage:
        client = get_github_client()
        repos = client.get("/user/repos")
    """
    return GitHubClient(**kwargs)


if __name__ == "__main__":
    # Demo usage
    print("GitHub Client Demo")
    print("=" * 40)
    
    client = get_github_client()
    print(f"Authenticated: {client.is_authenticated}")
    
    try:
        rate_info = client.get_rate_limit()
        print(f"Rate limit: {rate_info.remaining}/{rate_info.limit}")
        print(f"Resets in: {rate_info.seconds_until_reset:.0f} seconds")
    except GitHubClientError as e:
        print(f"Error: {e}")
        sys.exit(1)
