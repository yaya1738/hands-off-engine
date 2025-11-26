"""
Rate-limit-aware GitHub API client.

Provides a simple wrapper around GitHub API requests with automatic rate limit
handling, exponential backoff for transient errors, and authentication support.
"""

import os
import time
import random
from typing import Any, Dict, Optional, Tuple

import requests

GITHUB_API = "https://api.github.com"


class GitHubRateLimitError(Exception):
    """Raised when the GitHub API rate limit has been exceeded and retries are exhausted."""


def _auth_headers() -> Dict[str, str]:
    """
    Build GitHub API headers, including authentication if a token is available.

    Looks for GITHUB_TOKEN or GH_TOKEN in the environment. If no token is found,
    the request will be unauthenticated and subject to the low unauthenticated rate limit.
    """
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    headers: Dict[str, str] = {"Accept": "application/vnd.github+json"}
    if token:
        # GitHub recommends "Bearer" for fine-grained tokens, but also accepts "token".
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_get(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    max_retries: int = 5,
) -> Tuple[Any, Dict[str, Optional[str]]]:
    """
    Perform a GET request against the GitHub API with basic rate limit awareness
    and simple exponential backoff for transient errors.

    Args:
        path: Either a full URL (starting with http) or a relative API path like "/rate_limit".
        params: Optional query parameters to send with the request.
        max_retries: Maximum number of attempts, including the first.

    Returns:
        A tuple of (json_data, meta) where meta is a dict containing
        "limit", "remaining", and "reset" from the GitHub rate limit headers.

    Raises:
        GitHubRateLimitError: If the rate limit has been exceeded and retries are exhausted.
        requests.HTTPError: For non-rate-limit HTTP errors after retries are exhausted.
    """
    if params is None:
        params = {}

    url = path if path.startswith("http") else f"{GITHUB_API}{path}"
    wait_seconds = 1.0

    for attempt in range(max_retries):
        resp = requests.get(url, headers=_auth_headers(), params=params)

        limit = resp.headers.get("X-RateLimit-Limit")
        remaining = resp.headers.get("X-RateLimit-Remaining")
        reset = resp.headers.get("X-RateLimit-Reset")

        # Hard rate limit case.
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            if remaining == "0" and reset:
                reset_ts = int(reset)
                now = int(time.time())
                sleep_for = max(reset_ts - now, 0) + random.uniform(0, 1)

                # If this is the last attempt, raise instead of sleeping again.
                if attempt == max_retries - 1:
                    raise GitHubRateLimitError(
                        f"GitHub rate limit exceeded. "
                        f"limit={limit}, remaining={remaining}, reset={reset_ts}"
                    )

                # Sleep until the reset time (best-effort) and then retry.
                time.sleep(sleep_for)
                continue

        # Transient 5xx errors: simple exponential backoff.
        if resp.status_code >= 500:
            if attempt == max_retries - 1:
                resp.raise_for_status()
            time.sleep(wait_seconds + random.uniform(0, 0.5))
            wait_seconds *= 2
            continue

        # Success or non-retryable error.
        if resp.ok:
            try:
                data = resp.json()
            except ValueError:
                # If JSON decoding fails, raise a standard HTTP error for now.
                resp.raise_for_status()

            meta = {
                "limit": limit,
                "remaining": remaining,
                "reset": reset,
            }
            return data, meta

        # Non-OK and non-5xx / non-rate-limit: do not retry by default.
        resp.raise_for_status()

    # If we get here, retries were exhausted without a clear rate limit signal.
    raise GitHubRateLimitError("Exhausted retries calling GitHub API without success.")
