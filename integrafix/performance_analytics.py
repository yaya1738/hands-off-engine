#!/usr/bin/env python3
"""
INTEGRAFIX: Performance Analytics
=================================

Deep analysis of trading performance:
1. Win rate by category
2. P&L distribution
3. Edge accuracy
4. Time-based patterns
5. Recommendations for improvement
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
LOGS_DIR = PROJECT_ROOT / "logs"


def load_hft_trades() -> List[Dict]:
    """Load all HFT trades."""
    hft_log = LOGS_DIR / "hft_economics.jsonl"
    trades = []

    if hft_log.exists():
        with open(hft_log) as f:
            for line in f:
                try:
                    d = json.loads(line)
                    if d.get("type") == "trade_close":
                        trades.append(d)
                except:
                    pass

    return trades


def load_executor_trades() -> List[Dict]:
    """Load executor trade details."""
    exec_log = STATE_DIR / "autonomous_executor.jsonl"
    trades = []

    if exec_log.exists():
        with open(exec_log) as f:
            for line in f:
                try:
                    d = json.loads(line)
                    for trade in d.get("trades", []):
                        trade["timestamp"] = d.get("timestamp")
                        trades.append(trade)
                except:
                    pass

    return trades


def categorize_market(title: str) -> str:
    """Categorize market by title."""
    title_lower = title.lower()

    if any(w in title_lower for w in ["trump", "biden", "congress", "election"]):
        return "politics_us"
    if any(w in title_lower for w in ["ukraine", "russia", "china"]):
        return "politics_intl"
    if any(w in title_lower for w in ["bitcoin", "btc", "eth", "crypto"]):
        return "crypto"
    if any(w in title_lower for w in ["fed", "rate", "inflation"]):
        return "finance"
    if any(w in title_lower for w in ["nfl", "nba", "mlb", "sports"]):
        return "sports"
    if any(w in title_lower for w in ["movie", "oscar", "celebrity"]):
        return "entertainment"
    if any(w in title_lower for w in ["ai", "tech", "apple", "google"]):
        return "tech"
    if any(w in title_lower for w in ["nasa", "climate", "research"]):
        return "science"

    return "unknown"


def analyze_by_category() -> Dict[str, Dict]:
    """Analyze performance by market category."""
    trades = load_executor_trades()
    categories = defaultdict(lambda: {"trades": 0, "pnl": 0, "wins": 0})

    for trade in trades:
        cat = categorize_market(trade.get("market", trade.get("question", "")))
        pnl = trade.get("expected_pnl", 0)
        categories[cat]["trades"] += 1
        categories[cat]["pnl"] += pnl
        if pnl > 0:
            categories[cat]["wins"] += 1

    # Calculate win rates
    result = {}
    for cat, data in categories.items():
        data["win_rate"] = data["wins"] / data["trades"] if data["trades"] > 0 else 0
        result[cat] = dict(data)

    return result


def analyze_by_edge_bucket() -> Dict[str, Dict]:
    """Analyze performance by edge size."""
    trades = load_executor_trades()
    buckets = {
        "3-5%": {"min": 0.03, "max": 0.05, "trades": 0, "pnl": 0, "wins": 0},
        "5-8%": {"min": 0.05, "max": 0.08, "trades": 0, "pnl": 0, "wins": 0},
        "8-12%": {"min": 0.08, "max": 0.12, "trades": 0, "pnl": 0, "wins": 0},
        "12%+": {"min": 0.12, "max": 1.0, "trades": 0, "pnl": 0, "wins": 0},
    }

    for trade in trades:
        edge = abs(trade.get("edge", 0))
        pnl = trade.get("expected_pnl", 0)

        for name, bucket in buckets.items():
            if bucket["min"] <= edge < bucket["max"]:
                bucket["trades"] += 1
                bucket["pnl"] += pnl
                if pnl > 0:
                    bucket["wins"] += 1
                break

    # Calculate win rates
    for name, bucket in buckets.items():
        bucket["win_rate"] = bucket["wins"] / bucket["trades"] if bucket["trades"] > 0 else 0

    return buckets


def analyze_by_price_range() -> Dict[str, Dict]:
    """Analyze performance by price range."""
    trades = load_executor_trades()
    ranges = {
        "0-10%": {"min": 0, "max": 0.1, "trades": 0, "pnl": 0, "wins": 0},
        "10-30%": {"min": 0.1, "max": 0.3, "trades": 0, "pnl": 0, "wins": 0},
        "30-50%": {"min": 0.3, "max": 0.5, "trades": 0, "pnl": 0, "wins": 0},
        "50-70%": {"min": 0.5, "max": 0.7, "trades": 0, "pnl": 0, "wins": 0},
        "70-90%": {"min": 0.7, "max": 0.9, "trades": 0, "pnl": 0, "wins": 0},
        "90-100%": {"min": 0.9, "max": 1.0, "trades": 0, "pnl": 0, "wins": 0},
    }

    for trade in trades:
        price = trade.get("price", 0.5)
        pnl = trade.get("expected_pnl", 0)

        for name, r in ranges.items():
            if r["min"] <= price < r["max"]:
                r["trades"] += 1
                r["pnl"] += pnl
                if pnl > 0:
                    r["wins"] += 1
                break

    # Calculate win rates
    for name, r in ranges.items():
        r["win_rate"] = r["wins"] / r["trades"] if r["trades"] > 0 else 0

    return ranges


def get_recommendations() -> List[str]:
    """Generate improvement recommendations."""
    recommendations = []

    # Category analysis
    by_cat = analyze_by_category()
    best_cats = sorted(by_cat.items(), key=lambda x: x[1]["win_rate"], reverse=True)
    worst_cats = sorted(by_cat.items(), key=lambda x: x[1]["win_rate"])

    if best_cats:
        best = best_cats[0]
        if best[1]["win_rate"] > 0.55:
            recommendations.append(f"✓ Focus on {best[0]} (WR: {best[1]['win_rate']*100:.0f}%)")

    if worst_cats:
        worst = worst_cats[0]
        if worst[1]["win_rate"] < 0.50 and worst[1]["trades"] >= 5:
            recommendations.append(f"✗ Avoid {worst[0]} (WR: {worst[1]['win_rate']*100:.0f}%)")

    # Edge analysis
    by_edge = analyze_by_edge_bucket()
    for name, bucket in by_edge.items():
        if bucket["trades"] >= 5 and bucket["win_rate"] > 0.60:
            recommendations.append(f"✓ {name} edge signals have {bucket['win_rate']*100:.0f}% WR")

    # Price range analysis
    by_price = analyze_by_price_range()
    for name, r in by_price.items():
        if r["trades"] >= 5 and r["win_rate"] < 0.45:
            recommendations.append(f"✗ Avoid {name} price range (WR: {r['win_rate']*100:.0f}%)")

    if not recommendations:
        recommendations.append("Need more trade data for recommendations")

    return recommendations


def overall_stats() -> Dict:
    """Get overall trading statistics."""
    hft_trades = load_hft_trades()
    exec_trades = load_executor_trades()

    total_pnl = sum(t.get("cost", 0) for t in hft_trades)
    wins = sum(1 for t in hft_trades if t.get("cost", 0) > 0)
    losses = sum(1 for t in hft_trades if t.get("cost", 0) < 0)

    return {
        "total_trades": len(hft_trades),
        "total_pnl": total_pnl,
        "wins": wins,
        "losses": losses,
        "win_rate": wins / len(hft_trades) if hft_trades else 0,
        "avg_win": sum(t.get("cost", 0) for t in hft_trades if t.get("cost", 0) > 0) / wins if wins else 0,
        "avg_loss": sum(t.get("cost", 0) for t in hft_trades if t.get("cost", 0) < 0) / losses if losses else 0,
    }


def status_report() -> str:
    """Generate performance analytics report."""
    stats = overall_stats()
    by_cat = analyze_by_category()
    by_edge = analyze_by_edge_bucket()
    recs = get_recommendations()

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║             PERFORMANCE ANALYTICS                            ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║  OVERALL:                                                    ║",
        f"║    Trades: {stats['total_trades']:>6} | P&L: ${stats['total_pnl']:>+10.2f}              ║",
        f"║    Wins: {stats['wins']:>4} | Losses: {stats['losses']:>4} | WR: {stats['win_rate']*100:>5.1f}%            ║",
        f"║    Avg Win: ${stats['avg_win']:>+6.2f} | Avg Loss: ${stats['avg_loss']:>+6.2f}          ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║  BY CATEGORY:                                                ║",
    ]

    # Sort categories by win rate
    sorted_cats = sorted(by_cat.items(), key=lambda x: x[1]["win_rate"], reverse=True)
    for cat, data in sorted_cats[:5]:
        if data["trades"] > 0:
            lines.append(f"║    {cat:<15} {data['trades']:>3} trades | WR: {data['win_rate']*100:>5.1f}% | ${data['pnl']:>+7.2f} ║")

    lines.extend([
        "╠══════════════════════════════════════════════════════════════╣",
        "║  BY EDGE SIZE:                                               ║",
    ])

    for name, bucket in by_edge.items():
        if bucket["trades"] > 0:
            lines.append(f"║    {name:<8} {bucket['trades']:>3} trades | WR: {bucket['win_rate']*100:>5.1f}% | ${bucket['pnl']:>+7.2f} ║")

    lines.extend([
        "╠══════════════════════════════════════════════════════════════╣",
        "║  RECOMMENDATIONS:                                            ║",
    ])

    for rec in recs[:5]:
        lines.append(f"║    {rec:<54} ║")

    lines.append("╚══════════════════════════════════════════════════════════════╝")

    return "\n".join(lines)


def main():
    print(status_report())


if __name__ == "__main__":
    main()
