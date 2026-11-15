#!/usr/bin/env python3
"""Credit utilization reporting that never treats redaction as a zero balance."""
import datetime
import json
import math
import os
import pathlib

HOME = pathlib.Path.home()
CARDS = HOME / "hands-off" / "agents" / "cards.json"
LOG = HOME / "hands-off" / "logs" / "finance_credit.log"
ALERT_WARN = 0.45
ALERT_HARD = 0.50


def notify(title, text):
    os.system(f'termux-notification --title "{title}" --content "{text}" >/dev/null 2>&1')


def load_cards():
    if not CARDS.is_file():
        return None, "cards file missing"
    try:
        data = json.loads(CARDS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "cards file unreadable or malformed"
    if not isinstance(data, dict) or not data:
        return None, "card data absent"
    cards = []
    for key, item in data.items():
        if key.startswith("_"):
            continue
        if not isinstance(item, dict):
            return None, f"invalid card record: {key}"
        limit, balance = item.get("limit"), item.get("balance")
        if limit is None or balance is None:
            return None, "one or more card values are redacted or unknown"
        try:
            limit, balance = float(limit), float(balance)
        except (TypeError, ValueError):
            return None, "one or more card values are not numeric"
        if not math.isfinite(limit) or not math.isfinite(balance) or limit <= 0 or balance < 0:
            return None, "one or more card values are invalid"
        cards.append({"limit": limit, "balance": balance})
    if not cards:
        return None, "no measured card records"
    return cards, None


def main():
    cards, reason = load_cards()
    row = {"ts": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
           "data_status": "unknown" if cards is None else "measured"}
    if cards is None:
        row["reason"] = reason
    else:
        total_limit = sum(card["limit"] for card in cards)
        total_balance = sum(card["balance"] for card in cards)
        utilization = total_balance / total_limit
        row.update({"total_limit": round(total_limit, 2),
                    "total_balance": round(total_balance, 2),
                    "utilization": round(utilization, 4),
                    "warn": ALERT_WARN, "hard": ALERT_HARD})
        if utilization >= ALERT_HARD:
            notify("CREDIT UTILIZATION — HARD", f"{round(utilization * 100, 1)}% (≥ {int(ALERT_HARD * 100)}%).")
        elif utilization >= ALERT_WARN:
            notify("CREDIT UTILIZATION — WARN", f"{round(utilization * 100, 1)}% (≥ {int(ALERT_WARN * 100)}%).")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")
    print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()
