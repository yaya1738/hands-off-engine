#!/usr/bin/env python3
"""
ho-market-scanner.py

Lightweight Polymarket scanner that:
- Reads polymarket-compact.json
- Picks out interesting markets (for now: NBA + crypto, by keywords)
- Writes scanner_report.json
- Attaches scanner section into decision_report.json if present

This is a safe MVP: no trading, just classification + ranking.
"""

import json
import datetime as dt
from pathlib import Path
from typing import Any, Dict, List, Optional

STATE = Path("/root/hands-off-out/state")
COMPACT_PATH = STATE / "polymarket-compact.json"
SCANNER_PATH = STATE / "scanner_report.json"
DECISION_PATH = STATE / "decision_report.json"


def utc_now_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    try:
        data = json.loads(text)
    except Exception:
        return None
    if isinstance(data, dict):
        return data
    return None


def classify_category(question: str) -> str:
    q = question.lower()

    # Sports (NBA focus for now)
    nba_terms = [
        "nba", "mvp", "finals", "playoffs",
        "celtics", "lakers", "knicks", "warriors", "bucks", "nuggets",
        "heat", "suns", "clippers", "76ers", "sixers", "mavericks"
    ]
    if any(t in q for t in nba_terms):
        return "nba"

    # Crypto
    crypto_terms = [
        "bitcoin", "btc",
        "ethereum", "eth",
        "solana", "sol",
        "dogecoin", "doge",
        "crypto", "token", "altcoin"
    ]
    if any(t in q for t in crypto_terms):
        return "crypto"

    # Politics (we may use later)
    politics_terms = [
        "election", "president", "presidency", "primary",
        "parliament", "senate", "house of representatives",
        "governor", "mayor"
    ]
    if any(t in q for t in politics_terms):
        return "politics"

    return "other"


def extract_markets(compact: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Try both "events" and "markets", depending on how pm_trim wrote it
    if "events" in compact and isinstance(compact["events"], list):
        return compact["events"]
    if "markets" in compact and isinstance(compact["markets"], list):
        return compact["markets"]
    return []


def safe_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


def main() -> None:
    now = utc_now_iso()

    compact = load_json(COMPACT_PATH)
    if not compact:
        scanner = {
            "as_of": now,
            "reason": "no_polymarket_compact",
            "total_markets": 0,
            "candidates_count": 0,
            "candidates": [],
        }
        # Atomic write to scanner_report.json
        tmp = SCANNER_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(scanner, indent=2), encoding="utf-8")
        tmp.replace(SCANNER_PATH)

        # Best-effort attach (atomic)
        decision = load_json(DECISION_PATH)
        if decision is not None:
            pm = decision.setdefault("polymarket", {})
            pm["scanner"] = scanner
            tmp = DECISION_PATH.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(decision, indent=2), encoding="utf-8")
            tmp.replace(DECISION_PATH)

        print("[warn] no polymarket-compact.json found; wrote empty scanner_report.json")
        return

    markets = extract_markets(compact)
    total_markets = len(markets)

    candidates: List[Dict[str, Any]] = []

    for m in markets:
        if not isinstance(m, dict):
            continue

        question = (
            m.get("question")
            or m.get("title")
            or m.get("name")
            or ""
        )
        question = str(question).strip()
        if not question:
            continue

        category = classify_category(question)
        # For now focus scanner on things you actually care about for edge
        if category not in {"nba", "crypto"}:
            continue

        market_id = (
            m.get("id")
            or m.get("market_id")
            or m.get("slug")
            or None
        )

        yes_price = (
            m.get("yes_price")
            or m.get("yesPrice")
            or m.get("probability")
            or None
        )
        yes_price_f = safe_float(yes_price)

        # crude heuristic:
        # - prices near 0.5 are "more interesting" by default (max uncertainty)
        #   score = 1 at p=0.5, score = 0 at p=0 or 1
        if isinstance(yes_price_f, float):
            score = 1.0 - abs(yes_price_f - 0.5) * 2.0
            if score < 0.0:
                score = 0.0
        else:
            score = 0.5

        # Capture some raw info for later smarter models
        out = {
            "id": market_id,
            "category": category,
            "question": question,
            "yes_price": yes_price_f,
            "raw_yes_price": yes_price,
            "score": round(score, 3),
        }

        # Pass through a few common fields if present
        for key in ("end_date", "closes_at", "closeTime", "liquidity", "volume", "slug"):
            if key in m:
                out[key] = m.get(key)

        candidates.append(out)

    # Sort by score descending (most "interesting" first)
    candidates.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    top_candidates = candidates[:50]

    scanner = {
        "as_of": now,
        "total_markets": total_markets,
        "candidates_count": len(top_candidates),
        "candidates": top_candidates,
    }

    # Atomic write to scanner_report.json
    tmp = SCANNER_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(scanner, indent=2), encoding="utf-8")
    tmp.replace(SCANNER_PATH)
    print(f"[ok] scanner_report.json written with {len(top_candidates)} candidate(s) from {total_markets} market(s)")

    # Try to attach into decision_report.json (atomic)
    decision = load_json(DECISION_PATH)
    if decision is not None:
        pm = decision.setdefault("polymarket", {})
        pm["scanner"] = scanner
        tmp = DECISION_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(decision, indent=2), encoding="utf-8")
        tmp.replace(DECISION_PATH)
        print("[ok] attached scanner into decision_report.polymarket.scanner")
    else:
        print("[info] no decision_report.json yet; skipping attach")


if __name__ == "__main__":
    main()
