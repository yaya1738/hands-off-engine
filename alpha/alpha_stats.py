#!/usr/bin/env python3
"""
Alpha Stats - Summary statistics and reporting
"""
import json
from pathlib import Path
from typing import Any, Dict, List
from alpha_scorer import calculate_summary_stats


def write_summary_stats(
    candidates: List[Dict[str, Any]],
    threshold: float,
    output_path: Path
) -> None:
    """
    Calculate and write summary stats to JSON file.
    """
    stats = calculate_summary_stats(candidates, threshold)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(stats, indent=2), encoding='utf-8')
    print(f"[alpha_stats] Wrote summary stats to {output_path}")


def print_summary_stats(stats: Dict[str, Any]) -> None:
    """
    Pretty-print summary stats to console.
    """
    print("\n" + "="*70)
    print("ALPHA CANDIDATE SUMMARY STATISTICS")
    print("="*70)
    print(f"Timestamp:           {stats.get('timestamp', 'N/A')}")
    print(f"Threshold:           {stats.get('threshold', 0.0):.4f}")
    print(f"Total Candidates:    {stats.get('total_candidates', 0)}")
    print(f"Filtered (>thresh):  {stats.get('filtered_candidates', 0)}")
    print(f"\nBest Score:          {stats.get('best_score', 0.0):.4f}")
    print(f"Average Score:       {stats.get('avg_score', 0.0):.4f}")
    print(f"Median Score:        {stats.get('median_score', 0.0):.4f}")
    print(f"Top 10 Average:      {stats.get('top_10_avg', 0.0):.4f}")

    print("\nCategory Breakdown:")
    print("-" * 70)
    breakdown = stats.get('category_breakdown', {})
    for cat, data in sorted(breakdown.items(), key=lambda x: x[1]['top_score'], reverse=True):
        print(f"  {cat.upper():12s} | count={data['count']:3d} | "
              f"avg={data['avg_score']:.4f} | top_score={data['top_score']:.4f} | "
              f"top_edge={data['top_edge']:.4f}")

    print("\nPercentiles:")
    print("-" * 70)
    percentiles = stats.get('percentiles', {})
    for p, val in percentiles.items():
        print(f"  {p}: {val:.4f}")
    print("="*70 + "\n")
