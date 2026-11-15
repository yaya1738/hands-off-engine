#!/usr/bin/env python3
"""Statement reminders; redacted financial values remain explicitly unknown."""
import datetime
import json
import math
import os
import pathlib

HOME = pathlib.Path.home()
CARDS = HOME / "hands-off" / "agents" / "cards.json"
LOG = HOME / "hands-off" / "logs" / "finance_credit.log"
WARN_DAYS = 5


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
        limit, balance, statement_day = item.get("limit"), item.get("balance"), item.get("statement_day")
        if limit is None or balance is None or statement_day is None:
            return None, "one or more card values are redacted or unknown"
        try:
            limit, balance, statement_day = float(limit), float(balance), int(statement_day)
        except (TypeError, ValueError):
            return None, "one or more card values are not valid numbers"
        if (not math.isfinite(limit) or not math.isfinite(balance)
                or limit <= 0 or balance < 0 or not 1 <= statement_day <= 28):
            return None, "one or more card values are invalid"
        cards.append({"name": item.get("name") or key, "statement_day": statement_day,
                      "limit": limit, "balance": balance})
    return cards, None


def next_statement_date(day_of_month):
    today = datetime.date.today()
    year, month = today.year, today.month
    candidate = datetime.date(year, month, min(day_of_month, 28))
    if today <= candidate:
        return candidate
    if month == 12:
        year, month = year + 1, 1
    else:
        month += 1
    return datetime.date(year, month, min(day_of_month, 28))


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
        today = datetime.date.today()
        messages = []
        for card in cards:
            due = next_statement_date(card["statement_day"])
            days = (due - today).days
            if days in (WARN_DAYS, 0):
                tag = "WARN" if days == WARN_DAYS else "DUE"
                messages.append(f'{tag}: {card["name"]} statement {due.isoformat()} (in {days}d)')
        if messages:
            notify("Statements", f'Total util {round(utilization * 100, 1)}% | ' + " / ".join(messages))
        row.update({"total_utilization": round(utilization, 4), "statement_notes": messages})
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")
    print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()
