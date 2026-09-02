"""Fail-closed compatibility facade for the legacy bounty monitor.

GitHub API access, PR commenting, credential use, and persistent monitoring
are operational authorities and must be performed through FactoryAuthorityGateway.
"""

from datetime import datetime, timezone

TRACKED_PRS = []


def gh_api(pr_number: int, repo: str, fields: str = ""):
    return None


def check_pr_status(pr_info: dict) -> dict:
    return {
        "pr_number": pr_info.get("pr_number"),
        "status": "authority_required",
        "message": "Legacy bounty PR inspection is disabled; use FactoryAuthorityGateway.",
    }


def monitor_all_prs() -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_bounty_value": 0,
        "prs": [],
        "authority": "FactoryAuthorityGateway",
        "status": "disabled",
    }


def get_latest_comments(pr_number: int, repo: str, limit: int = 5):
    return []


def respond_to_pr_comment(pr_number: int, repo: str, body: str) -> bool:
    return False


def continuous_monitor(interval: int = 300):
    print("[FACTORY-AUTHORITY] continuous bounty monitoring is disabled")


if __name__ == "__main__":
    print(monitor_all_prs())
