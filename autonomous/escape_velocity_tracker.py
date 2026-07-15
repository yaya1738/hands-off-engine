#!/usr/bin/env python3
"""
ESCAPE VELOCITY TRACKER
=======================

Tracks exponential progress toward self-sustaining system.

Escape Velocity Definition:
- System generates more value than it consumes
- Daily profit > daily costs
- Compounds without human intervention

Exponential Factors:
1. Capital: More capital → more trading → more capital
2. Automation: More monitors → more opportunities → more automation
3. Income: More channels → more revenue → more channels
4. Intelligence: Better signals → better trades → better signals
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


import json
from datetime import datetime, timezone

STATE_FILE = BASE_DIR / "state" / "escape_velocity.json"


def load_tracker() -> dict:
    if STATE_FILE.exists():
        return json.load(open(STATE_FILE))
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "measurements": [],
        "current_velocity": 0.0,
        "acceleration": 0.0,
        "projected_escape_date": None,
        "exponential_factors": {
            "capital_multiplier": 1.0,
            "automation_multiplier": 1.0,
            "income_multiplier": 1.0,
            "intelligence_multiplier": 1.0
        }
    }


def save_tracker(data: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def record_measurement(balance: float, positions: float, income: float = 0, costs: float = 0):
    """Record a point-in-time measurement"""
    data = load_tracker()

    now = datetime.now(timezone.utc)
    measurement = {
        "timestamp": now.isoformat(),
        "balance": balance,
        "positions": positions,
        "total_value": balance + positions,
        "income": income,
        "costs": costs,
        "net": income - costs
    }

    data["measurements"].append(measurement)

    # Keep last 100 measurements
    data["measurements"] = data["measurements"][-100:]

    # Calculate velocity (rate of value change)
    if len(data["measurements"]) >= 2:
        recent = data["measurements"][-5:]
        if len(recent) >= 2:
            first_value = recent[0]["total_value"]
            last_value = recent[-1]["total_value"]
            data["current_velocity"] = last_value - first_value

            # Calculate acceleration (rate of velocity change)
            if len(data["measurements"]) >= 10:
                older = data["measurements"][-10:-5]
                older_velocity = older[-1]["total_value"] - older[0]["total_value"]
                data["acceleration"] = data["current_velocity"] - older_velocity

    # Update exponential factors based on measurements
    update_exponential_factors(data)

    # Project escape date
    if data["current_velocity"] > 0:
        # Escape velocity = $100/day profit
        target_velocity = 100.0
        days_to_escape = (target_velocity - data["current_velocity"]) / max(0.1, data["acceleration"])
        if 0 < days_to_escape < 365:
            escape_date = now.timestamp() + (days_to_escape * 86400)
            data["projected_escape_date"] = datetime.fromtimestamp(escape_date, tz=timezone.utc).isoformat()

    save_tracker(data)
    return data


def update_exponential_factors(data: dict):
    """Update multipliers based on system state"""
    measurements = data["measurements"]
    if not measurements:
        return

    latest = measurements[-1]

    # Capital multiplier: increases with balance
    if latest["balance"] >= 200:
        data["exponential_factors"]["capital_multiplier"] = 2.0
    elif latest["balance"] >= 100:
        data["exponential_factors"]["capital_multiplier"] = 1.5
    elif latest["balance"] >= 50:
        data["exponential_factors"]["capital_multiplier"] = 1.2
    else:
        data["exponential_factors"]["capital_multiplier"] = 1.0

    # Automation multiplier: increases with each cycle
    cycle_count = len(measurements)
    data["exponential_factors"]["automation_multiplier"] = 1.0 + (cycle_count * 0.02)

    # Compound multiplier
    compound = 1.0
    for factor in data["exponential_factors"].values():
        compound *= factor
    data["compound_multiplier"] = compound


def get_escape_status() -> dict:
    """Get current escape velocity status"""
    data = load_tracker()

    status = {
        "velocity": data.get("current_velocity", 0),
        "acceleration": data.get("acceleration", 0),
        "compound_multiplier": data.get("compound_multiplier", 1.0),
        "projected_escape": data.get("projected_escape_date"),
        "measurements_count": len(data.get("measurements", [])),
        "is_accelerating": data.get("acceleration", 0) > 0,
        "is_positive_velocity": data.get("current_velocity", 0) > 0
    }

    # Calculate progress percentage
    target_velocity = 100.0  # $100/day
    status["progress_percent"] = min(100, (status["velocity"] / target_velocity) * 100) if target_velocity > 0 else 0

    return status


if __name__ == "__main__":
    # Test measurement
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    # Get current balance
    try:
        from executor.trading_safeguards import TradingSafeguards
        safeguards = TradingSafeguards()
        ok, msg = safeguards.check_wallet_balance(0)
        balance = 0.0
        if "balance: $" in msg:
            balance = float(msg.split("balance: $")[1].split()[0])
        elif "Insufficient" in msg:
            balance = float(msg.split("$")[1].split()[0])
    except:
        balance = 8.99

    # Record measurement
    data = record_measurement(balance=balance, positions=99.0)

    print(f"Balance: ${balance:.2f}")
    print(f"Velocity: ${data['current_velocity']:.2f}/period")
    print(f"Acceleration: ${data['acceleration']:.2f}")
    print(f"Compound Multiplier: {data.get('compound_multiplier', 1.0):.2f}x")

    status = get_escape_status()
    print(f"\nEscape Progress: {status['progress_percent']:.1f}%")
    if status["projected_escape"]:
        print(f"Projected Escape: {status['projected_escape']}")
