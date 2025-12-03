#!/usr/bin/env python3
import json, pathlib, time, datetime

HOME = pathlib.Path.home()
CREDIT_LOG = HOME/"hands-off"/"logs"/"finance_credit.log"
PLAN_LOG   = HOME/"hands-off"/"logs"/"guardrail_actions.log"
EXT        = HOME/"hands-off"/"agents"/"external_accounts.json"

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
cash_now = sum(float(ext.get(k,0) or 0) for k in ("paypal","monzo","robinhood_cash","polymarket_cash"))

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

msg = f"Util {util*100:.1f}% | {decision} | Cash ${cash_now:,.0f} | Cycle% PP {cycle_pp}% / Gen {cycle_gen}%"
notify("Credit Guardrail", msg)

PLAN_LOG.parent.mkdir(parents=True, exist_ok=True)
PLAN_LOG.open("a", encoding="utf-8").write(json.dumps({
    "ts": now,
    "util": util,
    "decision": decision,
    "cash_liquid": round(cash_now,2),
    "cycle_cost_pct_at_paypal": cycle_pp,
    "cycle_cost_pct_general": cycle_gen,
    "recommendations": reco
})+"\n")

print(msg)
for r in reco: print("-", r)
