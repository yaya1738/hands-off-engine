#!/usr/bin/env python3
"""Read-only legacy snapshot compatibility facade.

The former implementation executed Python, contacted external APIs with an
embedded bot token, changed the working directory, and wrote repository state.
Those operational actions are now owned by FactoryAuthorityGateway.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_polymarket_balance():
    """Return an unavailable marker; external balance checks require authority."""
    return 0.0


def get_api_status():
    """Return a non-authoritative status marker without network access."""
    return {"openai": False, "telegram": False, "authority_required": True}


def get_git_status():
    """Return an empty compatibility result; git inspection is authority-owned."""
    return []


def generate_snapshot():
    """Generate an in-memory, non-persistent compatibility snapshot."""
    snapshot = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "polymarket_balance": get_polymarket_balance(),
        "api_status": get_api_status(),
        "recent_commits": get_git_status(),
        "authority": "FactoryAuthorityGateway",
        "disabled": True,
    }
    print(json.dumps(snapshot, indent=2))
    return snapshot


if __name__ == "__main__":
    generate_snapshot()
