"""Fail-closed merge authorization policy.

Automated agents may prepare and validate merge proposals, but this module
intentionally grants no automated merge authority. Human review and the
repository's protected merge controls remain independent requirements.
"""
from __future__ import annotations


def evaluate_merge_request(pr_number: int, requester: str) -> dict:
    """Return a review proposal; never authorize or execute a merge."""
    if isinstance(pr_number, bool) or not isinstance(pr_number, int) or pr_number < 1:
        raise ValueError("pr_number must be a positive integer")
    if not isinstance(requester, str) or not requester.strip():
        raise ValueError("requester must be a non-empty string")
    return {
        "pr_number": pr_number,
        "requester": requester,
        "decision": "human_review_required",
        "automated_merge": False,
        "reason": "Agent requests and CI results are not independent merge authorization.",
    }
