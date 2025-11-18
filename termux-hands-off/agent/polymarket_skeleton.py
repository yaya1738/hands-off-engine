#!/usr/bin/env python3
"""
polymarket_skeleton.py

Generic, pluggable skeleton for Polymarket event modelling.

- Takes Polymarket-like JSON:
    * either: { "markets": [ ... ] }
    * or: [ ... ]

- Normalizes into an internal Market dataclass
- Auto-categorizes each market (sports / crypto / politics / macro / other)
- Routes each market to a category model (uses alpha_scorer for multi-factor scoring)
- Produces an output JSON with per-market:
    - fair_yes
    - edge vs current yes price
    - score (composite multi-factor score from alpha_scorer)
    - rec: buy_yes / buy_no / hold
    - notes: short explanation
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import alpha scorer for composite scoring
# Try to import from alpha/ directory first, fallback to local if not available
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "alpha"))
    from alpha_scorer import calculate_composite_score
    ALPHA_SCORER_AVAILABLE = True
except ImportError:
    ALPHA_SCORER_AVAILABLE = False
    print("[polymarket_skeleton] Warning: alpha_scorer not available, using basic scoring")


# ---------- Core domain types ----------

class Category(str, Enum):
    SPORTS = "sports"
    CRYPTO = "crypto"
    POLITICS = "politics"
    MACRO = "macro"
    OTHER = "other"


@dataclass
class Market:
    id: str
    question: str
    category: Category
    closes_at: str
    yes_price: float
    no_price: float
    volume: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Opinion:
    """
    fair_yes : model's fair probability for YES (0-1)
    edge     : fair_yes - market.yes_price (positive = YES edge)
    score    : composite multi-factor score (higher = better opportunity)
    rec      : "buy_yes" / "buy_no" / "hold"
    notes    : human-readable explanation
    """
    fair_yes: float
    edge: float
    score: float
    rec: str
    notes: str = ""


# ---------- Base model + naive stub ----------

class BaseModel:
    category: Category

    def score(self, market: Market, context: Dict[str, Any]) -> Opinion:
        raise NotImplementedError


class NaivePriceModel(BaseModel):
    """
    Model with alpha scoring integration:

    - Treats current yes_price as "fair" (placeholder for real model)
    - Uses alpha_scorer's calculate_composite_score for multi-factor scoring
    - Factors: edge, volume, spread, time decay, confidence
    - Falls back to basic scoring if alpha_scorer unavailable
    """

    category = Category.OTHER

    def score(self, market: Market, context: Dict[str, Any]) -> Opinion:
        # Try to get fair value from market.extra first (if provided by upstream)
        fair_yes_raw = market.extra.get('fair_yes')

        if fair_yes_raw is not None:
            # Use provided fair value
            fair_yes = max(0.01, min(0.99, float(fair_yes_raw)))
        else:
            # Fallback: assume market price is fair (naive model, zero edge)
            # In production, replace with actual model predictions per category
            fair_yes = max(0.01, min(0.99, float(market.yes_price)))

        # Target edge threshold in basis points (e.g. 500 = 5%)
        target_edge_bps = float(context.get("target_edge_bps", 500))
        threshold = target_edge_bps / 10_000.0

        edge = fair_yes - market.yes_price

        # Calculate composite score using alpha_scorer
        if ALPHA_SCORER_AVAILABLE:
            # Extract optional fields for scoring
            volume = market.volume

            # Calculate spread from extra fields if available
            spread = None
            best_bid = market.extra.get("best_bid")
            best_ask = market.extra.get("best_ask")
            if best_bid is not None and best_ask is not None:
                spread = abs(float(best_ask) - float(best_bid))

            # Calculate days to close
            days_to_close = None
            if market.closes_at:
                try:
                    close_dt = datetime.fromisoformat(market.closes_at.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    days_to_close = max(0, (close_dt - now).days)
                except Exception:
                    pass

            # Use alpha_scorer's composite scoring
            composite_score = calculate_composite_score(
                edge_raw=edge,
                volume=volume,
                spread=spread,
                days_to_close=days_to_close,
                p_fair=fair_yes
            )
        else:
            # Fallback: simple score based on absolute edge
            composite_score = abs(edge)

        # Recommendation based on edge threshold
        if edge > threshold:
            rec = "buy_yes"
        elif -edge > threshold:
            rec = "buy_no"
        else:
            rec = "hold"

        notes = "alpha-scored" if ALPHA_SCORER_AVAILABLE else "basic scoring (alpha_scorer unavailable)"

        return Opinion(
            fair_yes=fair_yes,
            edge=edge,
            score=composite_score,
            rec=rec,
            notes=notes,
        )


# Registry of models per category (all share NaivePriceModel for now)
REGISTRY: Dict[Category, BaseModel] = {
    Category.SPORTS: NaivePriceModel(),
    Category.CRYPTO: NaivePriceModel(),
    Category.POLITICS: NaivePriceModel(),
    Category.MACRO: NaivePriceModel(),
    Category.OTHER: NaivePriceModel(),
}


# ---------- Category routing / normalization ----------

def infer_category(raw: Dict[str, Any]) -> Category:
    """
    Dumb keyword-based classifier to get us started.
    You’ll replace this with something better later.
    """
    q = str(raw.get("question", raw.get("title", ""))).lower()
    tags = " ".join(map(str, raw.get("tags", []))).lower()
    blob = f"{q} {tags}"

    if any(w in blob for w in [
        "wins", "points", "rebounds", "touchdowns",
        "final score", "nba", "nfl", "mlb", "soccer", "premier league"
    ]):
        return Category.SPORTS

    if any(w in blob for w in [
        "bitcoin", "eth", "ethereum", "crypto",
        "btc", "sol", "doge", "token", "altcoin"
    ]):
        return Category.CRYPTO

    if any(w in blob for w in [
        "election", "president", "prime minister",
        "parliament", "senate", "house of representatives",
        "votes", "runoff"
    ]):
        return Category.POLITICS

    if any(w in blob for w in [
        "inflation", "cpi", "ppi", "gdp",
        "unemployment", "fed", "interest rate", "fomc"
    ]):
        return Category.MACRO

    return Category.OTHER


def to_market(raw: Dict[str, Any]) -> Market:
    """
    Convert a raw Polymarket market dict into a Market dataclass.

    Expected keys (loose):
    - id / _id / slug
    - question / title
    - closes_at / end_date
    - yes_price or best_yes
    - no_price or best_no
    - volume (optional)
    """
    yes = float(raw.get("yes_price", raw.get("best_yes", 0.5)))
    no = float(raw.get("no_price", raw.get("best_no", 0.5)))

    if "category" in raw:
        try:
            cat = Category(str(raw["category"]))
        except ValueError:
            cat = infer_category(raw)
    else:
        cat = infer_category(raw)

    extra = {
        k: v
        for k, v in raw.items()
        if k
        not in {
            "id",
            "_id",
            "slug",
            "question",
            "title",
            "closes_at",
            "end_date",
            "yes_price",
            "no_price",
            "best_yes",
            "best_no",
            "volume",
            "category",
        }
    }

    return Market(
        id=str(raw.get("id") or raw.get("_id") or raw.get("slug") or "unknown"),
        question=str(raw.get("question", raw.get("title", "unknown question"))),
        category=cat,
        closes_at=str(raw.get("closes_at", raw.get("end_date", ""))),
        yes_price=yes,
        no_price=no,
        volume=float(raw.get("volume", 0.0)) if raw.get("volume") is not None else None,
        extra=extra,
    )


# ---------- Main analysis pipeline ----------

def analyze_markets(
    markets_raw: List[Dict[str, Any]],
    context: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Core skeleton function.

    Input  : list of raw market dicts
    Output : list of normalized + scored dicts
    """
    out: List[Dict[str, Any]] = []

    for raw in markets_raw:
        m = to_market(raw)
        model = REGISTRY.get(m.category, REGISTRY[Category.OTHER])
        opinion = model.score(m, context)

        out.append(
            {
                "id": m.id,
                "question": m.question,
                "category": m.category.value,
                "closes_at": m.closes_at,
                "yes_price": m.yes_price,
                "no_price": m.no_price,
                "volume": m.volume,
                "fair_yes": opinion.fair_yes,
                "edge": opinion.edge,
                "score": opinion.score,
                "rec": opinion.rec,
                "notes": opinion.notes,
            }
        )

    return out


# ---------- CLI wrapper ----------

def main(argv: Optional[List[str]] = None) -> None:
    argv = list(argv or sys.argv[1:])

    if not argv:
        print(
            "Usage: polymarket_skeleton.py INPUT_JSON [OUTPUT_JSON]\n"
            "  INPUT_JSON  - Polymarket-style file ({\"markets\": [...] } or [...])\n"
            "  OUTPUT_JSON - Optional. If omitted, prints to stdout.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    inp = Path(argv[0])
    outp = Path(argv[1]) if len(argv) > 1 else None

    raw = json.loads(inp.read_text(encoding="utf-8"))

    if isinstance(raw, dict) and "markets" in raw:
        markets_raw = raw["markets"]
    elif isinstance(raw, list):
        markets_raw = raw
    else:
        raise SystemExit('Expected list or {"markets": [...]} JSON')

    # Global modelling context (tunable)
    context: Dict[str, Any] = {
        # how much edge (in bps) we demand before "buy" instead of "hold"
        "target_edge_bps": 500,  # 5% default
    }

    analyzed = analyze_markets(markets_raw, context)
    result = {"markets": analyzed}

    if outp:
        outp.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"[ok] wrote {outp}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
