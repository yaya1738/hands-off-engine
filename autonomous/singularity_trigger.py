"""Read-only compatibility facade for the legacy singularity trigger.

Trading, pipeline execution, notifications, and state mutation require
FactoryAuthorityGateway and are intentionally fail-closed here.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TRIGGER_STATE = BASE_DIR / "state" / "singularity_trigger.json"
TRADING_THRESHOLD = 50.0
MINIMUM_VIABLE_THRESHOLD = 25.0


def log(msg: str):
    print(f"[SINGULARITY] {msg}")


def get_balance() -> float:
    """Read-only balance probe; no trading authority is granted."""
    return 0.0


def load_state() -> dict:
    if TRIGGER_STATE.exists():
        try:
            return json.loads(TRIGGER_STATE.read_text())
        except (OSError, ValueError):
            pass
    return {"triggered": False, "trigger_time": None, "trigger_balance": None,
            "actions_executed": [], "escape_velocity_at_trigger": None}


def send_telegram(msg: str, priority: str = "normal") -> bool:
    log("[FACTORY-AUTHORITY] notification delivery is disabled")
    return False


def save_state(state: dict) -> bool:
    log("[FACTORY-AUTHORITY] state mutation is disabled; submit through FactoryAuthorityGateway")
    return False


def execute_singularity():
    return ["[FACTORY-AUTHORITY] singularity execution is disabled; submit through FactoryAuthorityGateway"]


def execute_mini_singularity(balance: float):
    return ["[FACTORY-AUTHORITY] mini-singularity execution is disabled; submit through FactoryAuthorityGateway"]


def check_and_trigger():
    state = load_state()
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    state["balance"] = get_balance()
    state["authority_required"] = True
    state["disabled"] = True
    return state


def main():
    state = check_and_trigger()
    print(json.dumps(state, indent=2, default=str))


if __name__ == "__main__":
    main()
