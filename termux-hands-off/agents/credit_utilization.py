#!/usr/bin/env python3
import json, pathlib, time, math, os, datetime

HOME = pathlib.Path.home()
CARDS = HOME/"hands-off"/"agents"/"cards.json"
LOG   = HOME/"hands-off"/"logs"/"finance_credit.log"

# --------- Tunables ---------
ALERT_WARN = 0.45   # 45% = heads up
ALERT_HARD = 0.50   # 50% = stop line

# Cash-cycling assumptions (edit if needed)
PP_BIZ_FEE = 0.03        # 3% merchant fee to cash out to PayPal Business
PP_PAYPAL_REWARD = 0.03  # 3% at PayPal on PayPal Cashback card
PP_GENERAL_REWARD = 0.015# 1.5% general
# ---------------------------

def notify(title, text):
    os.system(f'termux-notification --title "{title}" --content "{text}" >/dev/null 2>&1')

def load_cards():
    d = json.loads(CARDS.read_text()) if CARDS.exists() else {}
    # sanitize
    out = {}
    for k,v in d.items():
        try:
            lim = float(v.get("limit",0))
            bal = float(v.get("balance",0))
            nm = v.get("name", k)
            if lim > 0:
                out[k] = {"limit": lim, "balance": bal, "name": nm}
        except:
            pass
    return out

def cycle_effective_cost():
    """
    Simple net fee estimate when cycling via PP Biz:
    net_fee ≈ PP_BIZ_FEE - reward_rate
    If spend posts as 'PayPal' (3%), net ~ 0%.
    If only 1.5% applies, net ≈ 1.5%.
    """
    net_at_paypal = PP_BIZ_FEE - PP_PAYPAL_REWARD
    net_general   = PP_BIZ_FEE - PP_GENERAL_REWARD
    return {
        "net_fee_at_paypal": round(net_at_paypal*100, 2),   # %
        "net_fee_general":   round(net_general*100, 2)      # %
    }

def main():
    cards = load_cards()
    tot_lim = sum(c["limit"] for c in cards.values())
    tot_bal = sum(c["balance"] for c in cards.values())
    util = (tot_bal / tot_lim) if tot_lim > 0 else 0.0

    est = cycle_effective_cost()
    row = {
        "ts": datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z",
        "total_limit": round(tot_lim,2),
        "total_balance": round(tot_bal,2),
        "utilization": round(util,4),
        "warn": ALERT_WARN,
        "hard": ALERT_HARD,
        "cycle_cost_pct_at_paypal": est["net_fee_at_paypal"],
        "cycle_cost_pct_general": est["net_fee_general"]
    }

    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row)+"\n")

    # Alerts
    if util >= ALERT_HARD:
        notify("CREDIT UTILIZATION — HARD", f"{round(util*100,1)}% (≥ {int(ALERT_HARD*100)}%). Reduce balance now.")
    elif util >= ALERT_WARN:
        notify("CREDIT UTILIZATION — WARN", f"{round(util*100,1)}% (≥ {int(ALERT_WARN*100)}%). Consider paying down.")

    print(json.dumps(row, indent=2))

if __name__ == "__main__":
    main()
