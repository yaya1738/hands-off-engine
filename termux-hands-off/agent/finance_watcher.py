#!/data/data/com.termux/files/usr/bin/python
"""Legacy finance watcher.

Manual local account snapshots and public price lookups are not reconciled account
truth. This module preserves component observations but never promotes incomplete
or unverified inputs into an authoritative net-worth total.
"""

import os
import json
import time
import math
import requests
import traceback

BASE = os.path.expanduser("~/hands-off")
STATE = f"{BASE}/state"
AGENT = f"{BASE}/agent"
LOGDIR = os.path.expanduser("~/.cron-logs")

TG_ENV = f"{STATE}/tg/bots/handsoff.env"
IFTTTENV = f"{STATE}/auto_sources.env"
PREV = f"{STATE}/finance_prev.json"

PM_CANDIDATES = [
    f"{STATE}/polymarket-compact.json",
    f"{AGENT}/polymarket-compact.json",
    f"{STATE}/polymarket_compact.json",
]
WC_PATH = f"{STATE}/watchlist_coins.json"
CH_PATH = f"{STATE}/crypto_holdings.json"
FA_PATH = f"{STATE}/fiat_accounts.json"


def load_env(path):
    data = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip()
    return data


def load_json(path):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
    except (OSError, ValueError, TypeError):
        return None
    return None


def find_pm_compact():
    return next((path for path in PM_CANDIDATES if os.path.exists(path)), None)


def _finite_nonnegative(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def get_coingecko_prices(ids):
    if not ids:
        return {}
    url = "https://api.coingecko.com/api/v3/simple/price"
    try:
        response = requests.get(
            url,
            params={"ids": ",".join(ids), "vs_currencies": "usd"},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def money(value):
    number = _finite_nonnegative(value)
    return f"${number:,.2f}" if number is not None else "UNKNOWN"


def calc_snapshot():
    snapshot = {
        "ts": int(time.time()),
        "components": {},
        "sources": {},
        "notes": [],
        "status": "partial_unknown",
        "net_usd": None,
        "estimated_net_usd": None,
    }
    components = snapshot["components"]
    sources = snapshot["sources"]

    # Polymarket compact snapshots are not proof of current wallet balance.
    pm_file = find_pm_compact()
    pm = load_json(pm_file) if pm_file else None
    if isinstance(pm, dict):
        cash_raw = pm.get("cash_usd", pm.get("cashUSD"))
        mark_raw = pm.get("mark_value_usd", pm.get("markUSD"))
        cash = _finite_nonnegative(cash_raw)
        mark = _finite_nonnegative(mark_raw)
        if cash is not None and mark is not None:
            components["polymarket_cash_usd"] = cash
            components["polymarket_mark_usd"] = mark
            sources["polymarket"] = "unverified_snapshot"
        else:
            sources["polymarket"] = "unknown"
            snapshot["notes"].append("Polymarket cash/mark fields are missing or invalid")
    else:
        sources["polymarket"] = "unknown"
        snapshot["notes"].append("Polymarket compact snapshot is missing or malformed")

    # Fiat balances are manual inputs; preserve them as unverified components.
    fiat = load_json(FA_PATH)
    if isinstance(fiat, dict) and fiat:
        valid = True
        for key, value in fiat.items():
            number = _finite_nonnegative(value)
            if number is None:
                valid = False
                snapshot["notes"].append(f"Fiat input {key!r} is invalid")
                continue
            components[str(key)] = number
        sources["fiat"] = "manual_unverified" if valid else "partial"
    else:
        sources["fiat"] = "unknown"
        snapshot["notes"].append("Fiat account inputs are missing or empty")

    # Crypto quantities need a valid price for every holding; missing prices
    # remain unknown instead of becoming a zero-dollar holding.
    holdings = load_json(CH_PATH)
    if isinstance(holdings, dict) and holdings:
        amounts = {key: _finite_nonnegative(value) for key, value in holdings.items()}
        prices = get_coingecko_prices(sorted(holdings.keys()))
        priced = {}
        for coin_id, amount in amounts.items():
            price_payload = prices.get(coin_id) if isinstance(prices, dict) else None
            price = _finite_nonnegative(price_payload.get("usd")) if isinstance(price_payload, dict) else None
            if amount is None or price is None:
                snapshot["notes"].append(f"Crypto amount/price unavailable for {coin_id}")
                continue
            priced[coin_id] = amount * price
        if len(priced) == len(holdings):
            for coin_id, value in priced.items():
                components[f"crypto_{coin_id}_usd"] = value
            components["crypto_total_usd"] = sum(priced.values())
            sources["crypto"] = "market_priced_manual_amounts"
        else:
            sources["crypto"] = "partial"
    else:
        sources["crypto"] = "unknown"
        snapshot["notes"].append("Crypto holdings are missing or empty")

    complete_inputs = (
        sources.get("polymarket") == "unverified_snapshot"
        and sources.get("fiat") == "manual_unverified"
        and sources.get("crypto") == "market_priced_manual_amounts"
    )
    if complete_inputs:
        snapshot["estimated_net_usd"] = sum(components.values())
        snapshot["status"] = "unverified_estimate"

    snapshot["notes"].append(
        "Authoritative net worth is UNKNOWN: these inputs are not independently reconciled."
    )
    return snapshot


def diff(previous, current):
    if not isinstance(previous, dict):
        previous = {}
    previous_components = previous.get("components", {})
    current_components = current.get("components", {})
    if not isinstance(previous_components, dict):
        previous_components = {}
    if not isinstance(current_components, dict):
        current_components = {}

    net_delta = None
    previous_net = previous.get("net_usd")
    current_net = current.get("net_usd")
    if (
        isinstance(previous_net, (int, float))
        and not isinstance(previous_net, bool)
        and math.isfinite(previous_net)
        and isinstance(current_net, (int, float))
        and not isinstance(current_net, bool)
        and math.isfinite(current_net)
    ):
        net_delta = current_net - previous_net

    component_deltas = {}
    for key in set(previous_components) & set(current_components):
        old = _finite_nonnegative(previous_components[key])
        new = _finite_nonnegative(current_components[key])
        if old is not None and new is not None:
            component_deltas[key] = new - old

    return {"net_delta": net_delta, "components": component_deltas}


def send_telegram(text, env):
    token = env.get("TOKEN")
    chat_id = env.get("CHAT_ID")
    if not token or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except Exception:
        pass


def send_ifttt(text, env):
    hook = env.get("IFTTT_WEBHOOK")
    if not hook:
        return
    try:
        requests.post(
            hook,
            json={"value1": "finance_watcher", "value2": text, "value3": ""},
            timeout=10,
        )
    except Exception:
        pass


def build_summary(current, delta):
    lines = [
        "💹 Finance watcher — "
        + time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(current["ts"]))
    ]
    estimated = current.get("estimated_net_usd")
    if current.get("status") == "unverified_estimate" and estimated is not None:
        lines.append(f"Estimated total (UNVERIFIED): {money(estimated)}")
    else:
        lines.append("Net worth: UNKNOWN (incomplete or unreconciled source evidence)")
    lines.append("Components (unverified inputs):")
    components = current.get("components", {})
    top = sorted(components.items(), key=lambda item: abs(item[1]), reverse=True)[:6]
    for key, value in top:
        lines.append(f"- {key}: {money(value)}")
    for note in current.get("notes", []):
        lines.append(f"note: {note}")
    return "\n".join(lines)


def main():
    os.makedirs(LOGDIR, exist_ok=True)
    previous = load_json(PREV)
    current = calc_snapshot()
    delta = diff(previous, current)
    message = build_summary(current, delta)

    with open(PREV, "w", encoding="utf-8") as handle:
        json.dump(current, handle, indent=2)

    send_telegram(message, load_env(TG_ENV))
    send_ifttt(message, load_env(IFTTTENV))

    with open(f"{LOGDIR}/finance.log", "a", encoding="utf-8") as handle:
        handle.write(message + "\n\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        os.makedirs(LOGDIR, exist_ok=True)
        with open(f"{LOGDIR}/finance.log", "a", encoding="utf-8") as handle:
            handle.write("[error] " + repr(exc) + "\n" + traceback.format_exc() + "\n")
        raise
