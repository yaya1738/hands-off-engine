#!/usr/bin/env python3
"""
alpha/ho_alpha_polymarket.py

Alpha-facing Polymarket pipeline with integrated scoring.

Pipeline:
1. Load market data from polymarket-compact.json or candidates.jsonl
2. Score candidates using alpha_scorer (multi-factor composite scoring)
3. Rank and cap candidates by category
4. Output scored candidates and summary stats to alpha/ directory

This is DRYRUN / alpha-facing ONLY - no live trading.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Import alpha scorer
from alpha_scorer import (
    score_candidate,
    calculate_summary_stats,
    rank_and_cap_candidates,
    ScoringConfig,
)


# Paths
ALPHA_DIR = Path(__file__).parent
CONFIG_PATH = ALPHA_DIR / "alpha_config.json"
STATE_DIR = Path.home() / "hands-off-out" / "state"
INPUT_FILE = STATE_DIR / "polymarket-compact.json"  # Primary source
OUTPUT_SCORED = ALPHA_DIR / "alpha_candidates_scored.json"
OUTPUT_STATS = ALPHA_DIR / "alpha_stats.json"
OUTPUT_TXT = ALPHA_DIR / "alpha_summary.txt"


def load_config() -> ScoringConfig:
    """Load scoring config from alpha_config.json"""
    if not CONFIG_PATH.exists():
        print(f"[ho_alpha] config not found at {CONFIG_PATH}, using defaults")
        return ScoringConfig()

    try:
        cfg_data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return ScoringConfig(
            min_score_threshold=cfg_data.get("min_score_threshold", 0.02),
            max_candidates_global=cfg_data.get("max_candidates_global", 50),
            max_candidates_per_category=cfg_data.get("max_candidates_per_category", 15),
            edge_threshold=cfg_data.get("edge_threshold", 0.05),
            category_caps=cfg_data.get("category_caps"),
        )
    except Exception as e:
        print(f"[ho_alpha] failed to load config: {e}, using defaults")
        return ScoringConfig()


def load_markets() -> List[Dict[str, Any]]:
    """
    Load market data from polymarket-compact.json.

    Expected format:
    {
        "markets": [
            {
                "id": "...",
                "question": "...",
                "yes_price": 0.5,
                "no_price": 0.5,
                "volume": 1000000,
                "category": "crypto",
                "closes_at": "2025-12-31T23:59:59Z",
                "best_bid": 0.49,
                "best_ask": 0.51,
                ...
            }
        ]
    }
    """
    if not INPUT_FILE.exists():
        print(f"[ho_alpha] input file not found: {INPUT_FILE}")
        return []

    try:
        raw = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ho_alpha] failed to read {INPUT_FILE}: {e}")
        return []

    if isinstance(raw, dict) and "markets" in raw:
        markets_raw = raw["markets"]
    elif isinstance(raw, list):
        markets_raw = raw
    else:
        print("[ho_alpha] unexpected JSON shape (need list or {'markets': [...]})")
        return []

    if not isinstance(markets_raw, list):
        print("[ho_alpha] markets_raw is not a list, aborting")
        return []

    return markets_raw


def normalize_market_to_candidate(market: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert raw market dict to alpha_scorer candidate format.

    Alpha scorer expects:
    - key: str (unique identifier)
    - p_fair: float (model's fair probability)
    - p_mkt: float (market price)
    - volume: float (optional)
    - best_bid: float (optional)
    - best_ask: float (optional)
    - closes_at: str ISO timestamp (optional)
    - category: str (optional)
    - note: str (optional)
    """
    # Extract fair value (if provided by model, else use market price as placeholder)
    p_fair = market.get("fair_yes", market.get("p_fair", market.get("yes_price", 0.5)))
    p_mkt = market.get("yes_price", market.get("p_mkt", 0.5))

    return {
        "key": market.get("id", market.get("slug", "unknown")),
        "question": market.get("question", market.get("title", "")),
        "p_fair": float(p_fair),
        "p_mkt": float(p_mkt),
        "volume": market.get("volume"),
        "best_bid": market.get("best_bid"),
        "best_ask": market.get("best_ask"),
        "closes_at": market.get("closes_at", market.get("end_date")),
        "category": market.get("category", "other"),
        "note": market.get("notes", market.get("note", "")),
    }


def write_outputs(
    scored_candidates: List[Dict[str, Any]],
    ranked_candidates: List[Dict[str, Any]],
    stats: Dict[str, Any],
) -> None:
    """Write scored candidates, ranked candidates, and stats to output files"""

    ALPHA_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Write all scored candidates
    OUTPUT_SCORED.write_text(
        json.dumps(
            {
                "scored_candidates": scored_candidates,
                "ranked_candidates": ranked_candidates,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[ho_alpha] wrote {OUTPUT_SCORED} with {len(ranked_candidates)} ranked candidates")

    # 2) Write summary stats
    OUTPUT_STATS.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"[ho_alpha] wrote {OUTPUT_STATS}")

    # 3) Write human-readable summary
    lines: List[str] = []
    ts = datetime.now(timezone.utc).isoformat()
    lines.append(f"[Alpha Polymarket Summary] @ {ts} UTC")
    lines.append(f"{'='*80}")
    lines.append(f"Total candidates: {stats['total_candidates']}")
    lines.append(f"Filtered (score >= {stats['threshold']}): {stats['filtered_candidates']}")
    lines.append(f"Best score: {stats.get('best_score', 0.0):.4f}")
    lines.append(f"Average score: {stats.get('avg_score', 0.0):.4f}")
    lines.append(f"Median score: {stats.get('median_score', 0.0):.4f}")
    lines.append(f"Top 10 average: {stats.get('top_10_avg', 0.0):.4f}")
    lines.append("")

    # Category breakdown
    lines.append("Category Breakdown:")
    lines.append(f"{'-'*80}")
    category_breakdown = stats.get("category_breakdown", {})
    for cat, cat_stats in sorted(category_breakdown.items()):
        lines.append(
            f"  {cat:10} | count={cat_stats['count']:3d} | "
            f"avg_score={cat_stats['avg_score']:.4f} | "
            f"top_score={cat_stats['top_score']:.4f} | "
            f"top_edge={cat_stats['top_edge']:.4f}"
        )
    lines.append("")

    # Percentiles
    percentiles = stats.get("percentiles", {})
    if percentiles:
        lines.append("Score Percentiles:")
        lines.append(f"{'-'*80}")
        lines.append(
            f"  p25={percentiles.get('p25', 0):.4f} | "
            f"p50={percentiles.get('p50', 0):.4f} | "
            f"p75={percentiles.get('p75', 0):.4f} | "
            f"p90={percentiles.get('p90', 0):.4f} | "
            f"p95={percentiles.get('p95', 0):.4f}"
        )
        lines.append("")

    # Top ranked candidates
    lines.append(f"Top {min(30, len(ranked_candidates))} Ranked Candidates:")
    lines.append(f"{'-'*80}")
    for i, cand in enumerate(ranked_candidates[:30], 1):
        score = cand.get("score", 0.0)
        edge = cand.get("edge_raw", 0.0)
        rec = cand.get("rec", "hold")
        cat = cand.get("category", "other")
        question = cand.get("question", "")

        # Trim long questions
        if len(question) > 100:
            question = question[:97] + "..."

        lines.append(
            f"{i:2d}. [{rec:8}] score={score:.4f} edge={edge:+.3f} cat={cat:8} | {question}"
        )

    OUTPUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[ho_alpha] wrote {OUTPUT_TXT}")


def main() -> None:
    """Main alpha pipeline execution"""
    print("[ho_alpha] Starting Alpha Polymarket scoring pipeline...")

    # 1. Load config
    config = load_config()
    print(f"[ho_alpha] Config: threshold={config.min_score_threshold}, "
          f"max_global={config.max_candidates_global}, "
          f"max_per_category={config.max_candidates_per_category}")

    # 2. Load markets
    markets_raw = load_markets()
    if not markets_raw:
        print("[ho_alpha] No markets to score (missing or invalid input)")
        return

    print(f"[ho_alpha] Loaded {len(markets_raw)} markets")

    # 3. Normalize to candidate format
    candidates = [normalize_market_to_candidate(m) for m in markets_raw]

    # 4. Score all candidates
    print(f"[ho_alpha] Scoring {len(candidates)} candidates...")
    scored_candidates = [score_candidate(c) for c in candidates]

    # 5. Rank and cap
    print(f"[ho_alpha] Ranking and applying caps...")
    ranked_candidates = rank_and_cap_candidates(scored_candidates, config)

    # 6. Calculate summary stats
    print(f"[ho_alpha] Calculating summary statistics...")
    stats = calculate_summary_stats(scored_candidates, config.min_score_threshold)

    # 7. Write outputs
    write_outputs(scored_candidates, ranked_candidates, stats)

    print(f"[ho_alpha] Pipeline complete. Ranked {len(ranked_candidates)} candidates.")


if __name__ == "__main__":
    main()
