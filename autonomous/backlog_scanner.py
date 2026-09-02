#!/usr/bin/env python3
"""Legacy backlog scanner compatibility facade.

The former implementation embedded a GitHub credential and used the ``gh``
CLI for remote PR inspection/commenting. Remote communication and mutations
belong to the governed integration/Factory authority layer. This module now
fails closed and contains no credential material.
"""

from typing import Any, Dict, Optional

REPO = "cortexlinux/cortex"
PRS = [239, 240, 241]
_AUTHORITY = "FactoryAuthorityGateway"


def check_pr(pr_num: int):
    """Do not perform remote PR inspection through the legacy process path."""
    print(f"[FACTORY-AUTHORITY] PR #{pr_num} inspection requires {_AUTHORITY}.")
    return None


def respond_to_action(pr_num: int, action_type: str, data: Dict[str, Any]) -> bool:
    """Do not post remote PR comments through the legacy process path."""
    print(
        f"[FACTORY-AUTHORITY] PR #{pr_num} action '{action_type}' requires "
        f"{_AUTHORITY}."
    )
    return False


def main():
    """Report the governed handoff without contacting GitHub."""
    print("[FACTORY-AUTHORITY] legacy backlog network execution is disabled.")
    print(f"Repository: {REPO}")
    print(f"PRs configured: {len(PRS)}")
    print(f"Next step: submit backlog inspection through {_AUTHORITY}.")
    return {"disabled": True, "authority": _AUTHORITY, "actions_needed": []}


if __name__ == "__main__":
    main()
