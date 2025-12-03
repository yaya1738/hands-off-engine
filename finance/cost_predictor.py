#!/usr/bin/env python3
"""
COST PREDICTOR - Forecast future costs
=======================================

Master: Yair Siegel
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / "state"


def predict_monthly_costs() -> dict:
    """Predict monthly costs based on current infrastructure."""

    # Get real infrastructure
    reality = STATE_DIR / "reality_bridge.json"
    if not reality.exists():
        return {"error": "No reality bridge data"}

    data = json.load(open(reality))
    droplets = data.get("droplets", [])

    # Calculate infrastructure costs
    infra_cost = sum(d.get("cost_monthly", 0) for d in droplets)

    # Estimate API costs
    api_costs = {
        "openai": 0,  # Quota exceeded, using free alternatives
        "groq": 0,    # Free tier
        "google": 0,  # Free tier
        "anthropic": 50  # Estimated Claude API usage
    }

    total_api = sum(api_costs.values())

    return {
        "predicted_monthly": {
            "infrastructure": infra_cost,
            "api_services": total_api,
            "total": infra_cost + total_api
        },
        "breakdown": {
            "droplets": {d["name"]: d.get("cost_monthly", 0) for d in droplets},
            "apis": api_costs
        },
        "prediction_confidence": 0.85,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    print(json.dumps(predict_monthly_costs(), indent=2))
