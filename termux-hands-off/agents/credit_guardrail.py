#!/usr/bin/env python3
import json, pathlib, time, datetime
from private_state import private_path

CREDIT_LOG = private_path("logs/finance_credit.log")
PLAN_LOG   = private_path("logs/guardrail_actions.log", create_parent=True)
EXT        = private_path("agents/external_accounts.json")

def last_json(path):
    if not path.exists(): return None
    last=None
    for line in path.read_text(encoding="utf-8").splitlines():
        try: last=json.loads(line)
        except: pass
    return last

def notify(title, text):
    try:
        import os
        os.system(f'termux-notification --title "{title}" --content "{text}" >/dev/null 2>&1')
    except: pass

now = datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"
snap = last_json(CREDIT_LOG) or {}

util = snap.get("total_utilization")
warn = snap.get("warn", 0.45)
hard = snap.get("hard", 0.50)
cycle_pp = snap.get("cycle_cost_pct_at_paypal", 0.0)  # modelled from your scheme
cycle_gen= snap.get("cycle_cost_pct_general", 1.5)

# load quick cash view for suggestions
ext = {}
if EXT.exists():
    try: ext=json.loads(EXT.read_text())
    except: ext={}
cash_keys = ("paypal", "monzo", "robinhood_cash", "polymarket_cash")
cash_now = None
if EXT.exists() and all(k in ext and ext[k] is not None for k in cash_keys):
    try:
        import math
        values = [float(ext[k]) for k in cash_keys]
        if all(math.isfinite(value) for value in values):
            cash_now = sum(values)
    except (TypeError, ValueError, OverflowError):
        cash_now = None

decision = "ok"
reco = []

if util is None:
    decision="unknown"
    reco.append("No utilization snapshot yet. Run quick_update.py to log cards, then re-run guardrail.")
elif util >= hard:
    decision="HARD"
    reco += [
        "Pause all card spend except necessary & foreign-fee-free.",
        "Route spend to Monzo/Schwab debit (no FX) where possible.",
        "Cycle PayPal Biz to pay statement minimums immediately.",
        "Target: bring utilization below 50% within 48h.",
    ]
elif util >= warn:
    decision="WARN"
    reco += [
        "Prefer Monzo/Schwab for new purchases (no FX).",
        "Increase PayPal Biz cycles to prepay high-APR cards.",
        "Avoid pushing any individual card > 50%.",
    ]
else:
    decision="OK"
    reco.append("All good. Keep cycles modest; avoid >50% per-card at statement cut.")

cash_text = f"${cash_now:,.0f}" if cash_now is not None else "UNKNOWN"
util_text = f"{util*100:.1f}%" if util is not None else "UNKNOWN"
msg = f"Util {util_text} | {decision} | Cash {cash_text} | Cycle% PP {cycle_pp}% / Gen {cycle_gen}%"
notify("Credit Guardrail", msg)

PLAN_LOG.parent.mkdir(parents=True, exist_ok=True)
PLAN_LOG.open("a", encoding="utf-8").write(json.dumps({
    "ts": now,
    "util": util,
    "decision": decision,
    "cash_liquid": round(cash_now,2) if cash_now is not None else None,
    "cycle_cost_pct_at_paypal": cycle_pp,
    "cycle_cost_pct_general": cycle_gen,
    "recommendations": reco
})+"\n")

print(msg)
for r in reco: print("-", r)
