#!/usr/bin/env python3
"""Interactive editor for explicitly supplied card data; never invent defaults."""
import json
import math
import pathlib

HOME = pathlib.Path.home()
CARDS = HOME / "hands-off" / "agents" / "cards.json"


def load_cards():
    if not CARDS.is_file():
        raise SystemExit(f"[blocked] {CARDS} is missing; refusing to create guessed financial data")
    try:
        data = json.loads(CARDS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"[blocked] Cannot read card data: {exc}")
    if not isinstance(data, dict) or not data:
        raise SystemExit("[blocked] Card data must be a non-empty JSON object")
    return data


def ask(prompt, current, cast=float):
    shown = "unknown" if current is None else str(current)
    raw = input(f"{prompt} [{shown}]: ").strip()
    if not raw:
        return current
    try:
        value = cast(raw)
        if isinstance(value, float) and (not math.isfinite(value) or value < 0):
            raise ValueError("value must be finite and non-negative")
        return value
    except (TypeError, ValueError):
        print("[warning] Invalid value; retaining the current value")
        return current


cards = load_cards()
print("\n[Cards quick editor] Blank keeps the current value; unknown remains unknown.\n")
for key, card in cards.items():
    if not isinstance(card, dict):
        print(f"--- {key}: invalid record; skipped ---")
        continue
    print(f"--- {card.get('name') or key} ---")
    card["limit"] = ask("Limit", card.get("limit"))
    card["balance"] = ask("Balance", card.get("balance"))
    card["apr_pct"] = ask("APR %", card.get("apr_pct"))
    card["statement_day"] = ask("Statement day (1-28)", card.get("statement_day"), int)

CARDS.parent.mkdir(parents=True, exist_ok=True)
temporary = CARDS.with_suffix(CARDS.suffix + ".tmp")
temporary.write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")
temporary.replace(CARDS)
print(f"[ok] wrote {CARDS}")
