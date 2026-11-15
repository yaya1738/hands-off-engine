#!/usr/bin/env python3
"""Read-only CLI for inspecting the Factory objective review queue."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai.factory.authority_gateway import FactoryAuthorityGateway


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect Factory objectives (read-only)")
    sub = parser.add_subparsers(dest="command", required=True)
    list_parser = sub.add_parser("list", help="List newest queued objectives")
    list_parser.add_argument("--limit", type=int, default=20)
    list_parser.add_argument("--status", default=None)
    get_parser = sub.add_parser("get", help="Show one objective by goal ID")
    get_parser.add_argument("goal_id")
    args = parser.parse_args(argv)

    gateway = FactoryAuthorityGateway()
    if args.command == "list":
        result = gateway.list_goals(limit=args.limit, status=args.status)
        print(json.dumps({
            "count": len(result),
            "objectives": [
                {
                    "goal_id": row.get("goal_id"),
                    "objective": row.get("objective"),
                    "priority": row.get("priority"),
                    "source": row.get("source"),
                    "status": row.get("status"),
                    "created_at": row.get("created_at"),
                    "approval_required": row.get("approval_required"),
                    "execution_enabled": row.get("execution_enabled"),
                }
                for row in result
            ],
            "read_only": True,
            "execution_enabled": False,
        }, indent=2, sort_keys=True))
        return 0
    result = gateway.get_goal(args.goal_id)
    if result is None:
        print(json.dumps({"status": "not_found", "execution_enabled": False}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
