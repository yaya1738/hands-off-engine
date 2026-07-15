#!/usr/bin/env python3
"""
Batch 25: Policy Brain v2 Adapter

Translates learning-weighted Policy Brain v2 output
into the existing Policy Executor contract.

DRYRUN only.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any


ACTION_MAP = {
    "maintain_strategy": "summary",
    "health_check": "health-check",
    "autoloop": "autoloop",
    "analyze_history": "analyze-history",
    "polymarket_analysis": "polymarket-analysis",
}


def adapt_policy_v2(
    state_dir: Path = Path("state"),
) -> Dict[str, Any]:
    state_dir = Path(state_dir)

    source_path = state_dir / "brain_policy_v2.json"
    output_path = state_dir / "brain_policy_next.json"

    if not source_path.exists():
        raise FileNotFoundError(
            f"Missing required input: {source_path}"
        )

    with open(source_path, "r") as f:
        policy_v2 = json.load(f)

    actions = []

    for recommendation in policy_v2.get(
        "weighted_recommendations", []
    ):
        action = recommendation.get("action")

        mapped = ACTION_MAP.get(action)

        if mapped:
            actions.append(
                {
                    "type": mapped,
                    "mode": "DRYRUN",
                    "weight": recommendation.get("weight", 0),
                }
            )

    if not actions:
        actions.append(
            {
                "type": "summary",
                "mode": "DRYRUN",
                "reason": "No executable recommendation mapped",
            }
        )

    adapted = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "policy_brain_v2_adapter",
        "mode": "DRYRUN",
        "actions": actions,
        "confidence": policy_v2.get("confidence"),
        "risk_assessment": policy_v2.get(
            "risk_assessment",
            "unknown",
        ),
    }

    with open(output_path, "w") as f:
        json.dump(adapted, f, indent=2)

    return {
        "status": "ok",
        "output_files": [str(output_path)],
        "actions_generated": len(actions),
    }


if __name__ == "__main__":
    import sys

    directory = Path(
        sys.argv[1] if len(sys.argv) > 1 else "state"
    )

    result = adapt_policy_v2(directory)
    print(result)
