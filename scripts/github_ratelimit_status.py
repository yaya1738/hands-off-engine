"""
Small CLI utility to print the current GitHub core rate limit status.

Usage (from repo root):

    python -m scripts.github_ratelimit_status

Requires:
    - Environment variable GITHUB_TOKEN or GH_TOKEN (recommended), otherwise
      runs unauthenticated and may hit low rate limits quickly.
"""

from __future__ import annotations

import datetime
import time

from scripts.github_client import github_get


def _format_unix_timestamp(ts_str: str | None) -> str:
    """Format a Unix timestamp string into a human-readable format."""
    if not ts_str:
        return "unknown"
    try:
        ts_int = int(ts_str)
    except (TypeError, ValueError):
        return ts_str
    dt = datetime.datetime.utcfromtimestamp(ts_int)
    return f"{ts_int} ({dt.isoformat()}Z)"


def main() -> None:
    """Fetch and display GitHub rate limit information."""
    data, _meta = github_get("/rate_limit")

    core = data.get("resources", {}).get("core", {})
    search = data.get("resources", {}).get("search", {})

    now = int(time.time())

    def line(name: str, bucket: dict) -> str:
        limit = bucket.get("limit", "unknown")
        remaining = bucket.get("remaining", "unknown")
        reset = bucket.get("reset")
        reset_str = _format_unix_timestamp(str(reset) if reset is not None else None)
        return f"{name:8} | limit={limit:>5} remaining={remaining:>5} reset={reset_str}"

    print("GitHub rate limit status (UTC)")
    print("Now:", _format_unix_timestamp(str(now)))
    print()
    print(line("core", core))
    print(line("search", search))


if __name__ == "__main__":
    main()
