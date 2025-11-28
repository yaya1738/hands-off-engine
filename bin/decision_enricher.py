from pathlib import Path
import json

STATE = Path("/root/hands-off-out/state")
decision_path = STATE / "decision_report.json"
backup_path = STATE / "decision_report.raw.json"
profit_path = STATE / "profit_signal.json"

def load_json(p):
    if not p.exists():
        return None
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

decision = load_json(decision_path)
profit = load_json(profit_path)

# If there's no decision yet, do nothing
if not isinstance(decision, dict):
    raise SystemExit(0)

# Backup original once (or overwrite; it's small)
try:
    with backup_path.open("w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2)
except Exception:
    pass

risk_regime = None

if isinstance(profit, dict):
    delta = profit.get("delta_net_usd", 0.0)
    direction = profit.get("direction", "unknown")

    # Simple regime logic (can be tuned later)
    # You can think: big up → more aggressive, big down → defensive
    try:
        d = float(delta)
    except Exception:
        d = 0.0

    if d >= 300:
        mode = "aggressive"
        reason = "recent net worth increased significantly"
    elif d <= -300:
        mode = "defensive"
        reason = "recent net worth decreased significantly"
    else:
        mode = "normal"
        reason = "recent change in net worth is moderate"

    risk_regime = {
        "mode": mode,
        "reason": reason,
        "delta_net_usd": d,
        "profit_signal": profit,
    }

# Attach regime + profit to decision file (non-destructive)
if risk_regime is not None:
    decision["risk_regime"] = risk_regime
    decision["profit_signal"] = profit

# Atomic write: write to .tmp, then rename
try:
    tmp_path = decision_path.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2)
    tmp_path.replace(decision_path)
except Exception:
    pass
