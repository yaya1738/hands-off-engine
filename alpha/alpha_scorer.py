#!/usr/bin/env python3
"""
Alpha Scorer - Multi-factor candidate scoring engine
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from math import log, exp
from typing import Any, Dict, List, Optional
import statistics


@dataclass
class ScoringConfig:
    """Configuration for scoring algorithm"""
    min_score_threshold: float = 0.02
    max_candidates_global: int = 50
    max_candidates_per_category: int = 15
    edge_threshold: float = 0.05
    category_caps: Dict[str, int] = None

    def __post_init__(self):
        if self.category_caps is None:
            self.category_caps = {
                "crypto": 20,
                "sports": 10,
                "politics": 15,
                "macro": 10,
                "other": 5
            }


def calculate_composite_score(
    edge_raw: float,
    volume: Optional[float],
    spread: Optional[float],
    days_to_close: Optional[int],
    p_fair: float
) -> float:
    """
    Calculate composite score from multiple factors.

    Score = |edge| * (1 + vol_factor) * spread_factor * time_factor * (1 + conf)

    Args:
        edge_raw: p_fair - p_mkt (raw edge)
        volume: Market volume in USD (optional)
        spread: best_ask - best_bid (optional)
        days_to_close: Days until market closes (optional)
        p_fair: Fair probability (0-1)

    Returns:
        Composite score (higher = better opportunity)
    """
    # Base edge magnitude
    edge_abs = abs(edge_raw)

    # Volume factor: log-scaled liquidity bonus
    if volume and volume > 0:
        vol_factor = log(1 + volume) / 10.0
    else:
        vol_factor = 0.0

    # Spread factor: execution cost penalty
    if spread is not None and spread >= 0:
        spread_factor = max(0.1, 1.0 - spread * 5.0)
    else:
        spread_factor = 1.0

    # Time decay: urgency factor
    if days_to_close is not None and days_to_close > 0:
        time_factor = exp(-days_to_close / 30.0)
    else:
        time_factor = 1.0

    # Confidence factor: extreme priors = stronger signal
    confidence = 1.0 - 2.0 * abs(p_fair - 0.5)

    # Composite score
    score = edge_abs * (1 + vol_factor) * spread_factor * time_factor * (1 + confidence)

    return round(score, 6)


def score_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score a single candidate and return enriched dict.

    Expected input fields:
        - key: str
        - p_fair: float
        - p_mkt: float
        - volume: float (optional)
        - best_bid: float (optional)
        - best_ask: float (optional)
        - closes_at: str ISO timestamp (optional)
        - category: str (optional)
        - note: str (optional)

    Returns:
        Enriched candidate with added fields:
        - edge_raw
        - score
        - rec (buy_yes | buy_no | hold)
    """
    p_fair = float(candidate.get('p_fair', 0.5))
    p_mkt = float(candidate.get('p_mkt', 0.5))
    edge_raw = p_fair - p_mkt

    # Extract optional fields
    volume = candidate.get('volume')
    if volume is not None:
        volume = float(volume)

    best_bid = candidate.get('best_bid')
    best_ask = candidate.get('best_ask')
    spread = None
    if best_bid is not None and best_ask is not None:
        spread = abs(float(best_ask) - float(best_bid))

    closes_at = candidate.get('closes_at')
    days_to_close = None
    if closes_at:
        try:
            close_dt = datetime.fromisoformat(closes_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            days_to_close = max(0, (close_dt - now).days)
        except Exception:
            pass

    # Calculate composite score
    score = calculate_composite_score(edge_raw, volume, spread, days_to_close, p_fair)

    # Recommendation
    if edge_raw > 0.05:
        rec = "buy_yes"
    elif edge_raw < -0.05:
        rec = "buy_no"
    else:
        rec = "hold"

    # Return enriched candidate
    result = dict(candidate)
    result.update({
        'edge_raw': round(edge_raw, 4),
        'score': score,
        'rec': rec,
        'p_fair': round(p_fair, 4),
        'p_mkt': round(p_mkt, 4),
    })

    return result


def calculate_summary_stats(
    candidates: List[Dict[str, Any]],
    threshold: float
) -> Dict[str, Any]:
    """
    Calculate aggregate statistics for candidates.

    Returns:
        Summary stats dict with best_score, avg_score, category_breakdown, etc.
    """
    if not candidates:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "threshold": threshold,
            "total_candidates": 0,
            "filtered_candidates": 0,
        }

    scores = [c['score'] for c in candidates]
    filtered = [c for c in candidates if c['score'] >= threshold]

    # Category breakdown
    by_category = {}
    for c in filtered:
        cat = c.get('category', 'other')
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(c)

    category_breakdown = {}
    for cat, cands in by_category.items():
        cat_scores = [c['score'] for c in cands]
        cat_edges = [abs(c['edge_raw']) for c in cands]
        category_breakdown[cat] = {
            "count": len(cands),
            "avg_score": round(statistics.mean(cat_scores), 4) if cat_scores else 0.0,
            "top_score": round(max(cat_scores), 4) if cat_scores else 0.0,
            "top_edge": round(max(cat_edges), 4) if cat_edges else 0.0,
        }

    # Percentiles
    percentiles = {}
    if scores:
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        percentiles = {
            "p25": round(sorted_scores[int(n * 0.25)], 4),
            "p50": round(sorted_scores[int(n * 0.50)], 4),
            "p75": round(sorted_scores[int(n * 0.75)], 4),
            "p90": round(sorted_scores[int(n * 0.90)], 4),
            "p95": round(sorted_scores[int(n * 0.95)], 4),
        }

    # Top 10 average
    top_10 = sorted(candidates, key=lambda c: c['score'], reverse=True)[:10]
    top_10_avg = statistics.mean([c['score'] for c in top_10]) if top_10 else 0.0

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "threshold": threshold,
        "best_score": round(max(scores), 4),
        "avg_score": round(statistics.mean(scores), 4),
        "median_score": round(statistics.median(scores), 4),
        "total_candidates": len(candidates),
        "filtered_candidates": len(filtered),
        "top_10_avg": round(top_10_avg, 4),
        "category_breakdown": category_breakdown,
        "percentiles": percentiles,
    }


def rank_and_cap_candidates(
    candidates: List[Dict[str, Any]],
    config: ScoringConfig
) -> List[Dict[str, Any]]:
    """
    Rank candidates and apply caps.

    Logic:
        1. Filter: score >= min_score_threshold
        2. Group by category
        3. Take top N per category
        4. Merge and sort by score DESC
        5. Take top MAX_CANDIDATES_GLOBAL

    Returns:
        Final ranked and capped candidate list
    """
    # Filter by minimum score
    filtered = [c for c in candidates if c['score'] >= config.min_score_threshold]

    # Group by category
    by_category = {}
    for c in filtered:
        cat = c.get('category', 'other')
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(c)

    # Apply per-category caps
    capped = []
    for cat, cands in by_category.items():
        # Sort by score DESC
        sorted_cands = sorted(cands, key=lambda c: c['score'], reverse=True)
        # Take top N for this category
        cap = config.category_caps.get(cat, config.max_candidates_per_category)
        capped.extend(sorted_cands[:cap])

    # Final sort by score DESC
    final = sorted(capped, key=lambda c: c['score'], reverse=True)

    # Global cap
    return final[:config.max_candidates_global]
