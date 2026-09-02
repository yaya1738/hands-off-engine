"""Read-only compatibility facade for legacy bounty PR monitoring.

The former implementation executed the GitHub CLI, used a credential embedded
in source, posted comments, and persisted monitor state. Those side effects
must be owned by the central Factory authority path.
"""
import json
from datetime import datetime, timezone

TRACKED_PRS = [
    {"pr_number": 239, "repo": "cortexlinux/cortex", "bounty_value": 125, "title": "KV Cache Manager", "issue": 223},
    {"pr_number": 240, "repo": "cortexlinux/cortex", "bounty_value": 100, "title": "LLM Device Abstraction", "issue": 222},
    {"pr_number": 241, "repo": "cortexlinux/cortex", "bounty_value": 25, "title": "Smart Package Search", "issue": 117},
]


def gh_api(pr_number, repo, fields="state,title,comments,reviews,updatedAt,mergeable,mergedAt"):
    """Fail closed; external GitHub access requires Factory authority."""
    return None


def check_pr_status(pr_info):
    return {
        "pr_number": pr_info["pr_number"],
        "bounty_value": pr_info["bounty_value"],
        "status": "authority_required",
        "authority": "FactoryAuthorityGateway",
        "action_required": [],
    }


def monitor_all_prs():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_bounty_value": sum(pr["bounty_value"] for pr in TRACKED_PRS),
        "prs": [check_pr_status(pr) for pr in TRACKED_PRS],
        "disabled": True,
        "authority": "FactoryAuthorityGateway",
    }


def get_latest_comments(pr_number, repo, limit=5):
    return []


def respond_to_pr_comment(pr_number, repo, body):
    return False


def continuous_monitor(interval=300):
    raise RuntimeError(
        "[FACTORY-AUTHORITY] legacy bounty monitoring is disabled; "
        "submit through FactoryAuthorityGateway"
    )


if __name__ == "__main__":
    print(json.dumps(monitor_all_prs(), indent=2))
