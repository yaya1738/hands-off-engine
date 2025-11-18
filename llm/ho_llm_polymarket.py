#!/usr/bin/env python3
"""
Hands-Off LLM Polymarket Analyzer

Integration script that connects the LLM intelligence layer to the Polymarket pipeline.

Pipeline:
1. Read polymarket-compact.json (output from alpha/ho_alpha_polymarket.py)
2. For each market, invoke LLMMarketAnalyst
3. Produce structured LLM analysis output (llm_alpha_report.json)
4. Log all operations for audit trail

This script runs in DRYRUN mode by default and produces analysis-only output.
No real trades are placed.

Usage:
    python llm/ho_llm_polymarket.py [--input INPUT_JSON] [--output OUTPUT_JSON]

Environment variables:
    ANTHROPIC_API_KEY: Claude API key (optional, falls back to naive model)
    OPENROUTER_API_KEY: OpenRouter API key (optional)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.market_analyst import LLMMarketAnalyst, LLMOpinion
from llm.backend_selector import Priority


# Default paths (can be overridden via CLI)
DEFAULT_INPUT = Path.home() / "hands-off-out" / "state" / "polymarket-compact.json"
DEFAULT_OUTPUT = Path.home() / "hands-off-out" / "state" / "llm_alpha_report.json"


def load_markets(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load markets from polymarket-compact.json

    Args:
        input_path: Path to input JSON file

    Returns:
        List of market dicts
    """
    if not input_path.exists():
        print(f"[ho_llm_polymarket] ERROR: Input file not found: {input_path}")
        return []

    try:
        raw = json.loads(input_path.read_text(encoding="utf-8"))

        if isinstance(raw, dict) and "markets" in raw:
            markets = raw["markets"]
        elif isinstance(raw, list):
            markets = raw
        else:
            print(f"[ho_llm_polymarket] ERROR: Unexpected JSON structure")
            return []

        if not isinstance(markets, list):
            print(f"[ho_llm_polymarket] ERROR: Markets is not a list")
            return []

        print(f"[ho_llm_polymarket] Loaded {len(markets)} markets from {input_path}")
        return markets

    except Exception as e:
        print(f"[ho_llm_polymarket] ERROR: Failed to load markets: {e}")
        return []


def analyze_markets_with_llm(
    markets: List[Dict[str, Any]],
    analyst: LLMMarketAnalyst,
    max_markets: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Analyze markets using LLM analyst

    Args:
        markets: List of market dicts
        analyst: LLMMarketAnalyst instance
        max_markets: Optional limit on number of markets to analyze

    Returns:
        List of analysis results with LLM opinions
    """
    if max_markets:
        markets = markets[:max_markets]

    results = []

    for i, market in enumerate(markets, 1):
        market_id = market.get("id", "unknown")
        question = market.get("question", "Unknown question")

        print(f"\n[ho_llm_polymarket] [{i}/{len(markets)}] Analyzing: {question[:80]}")

        # Try LLM analysis
        llm_opinion = analyst.analyze_market(market)

        # Build result dict
        result = {
            "id": market_id,
            "question": question,
            "category": market.get("category", "other"),
            "yes_price": market.get("yes_price"),
            "volume": market.get("volume"),
            "closes_at": market.get("closes_at"),
        }

        if llm_opinion:
            # LLM analysis succeeded
            result["llm_analysis"] = llm_opinion.to_dict()
            result["analysis_source"] = "llm"

            print(f"[ho_llm_polymarket]   LLM: {llm_opinion.action} @ {llm_opinion.fair_probability:.1f}% "
                  f"(edge: {llm_opinion.edge_bps} bps, confidence: {llm_opinion.confidence})")
        else:
            # LLM failed, mark as unavailable
            result["llm_analysis"] = None
            result["analysis_source"] = "fallback_naive"

            print(f"[ho_llm_polymarket]   LLM analysis unavailable (no backends or DRYRUN simulation failed)")

        results.append(result)

    return results


def write_output(
    results: List[Dict[str, Any]],
    output_path: Path,
    analyst_status: Dict[str, Any],
) -> None:
    """
    Write LLM analysis results to output JSON

    Args:
        results: Analysis results
        output_path: Output file path
        analyst_status: Analyst status dict
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build output document
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analyst_status": analyst_status,
        "total_markets": len(results),
        "llm_analyzed": sum(1 for r in results if r["analysis_source"] == "llm"),
        "fallback_count": sum(1 for r in results if r["analysis_source"] == "fallback_naive"),
        "markets": results,
    }

    # Write JSON
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"\n[ho_llm_polymarket] Wrote {len(results)} market analyses to {output_path}")
    print(f"[ho_llm_polymarket]   - LLM analyzed: {output['llm_analyzed']}")
    print(f"[ho_llm_polymarket]   - Fallback: {output['fallback_count']}")


def main(argv: Optional[List[str]] = None) -> None:
    """
    Main entry point for LLM Polymarket analyzer

    Args:
        argv: Command line arguments (uses sys.argv if None)
    """
    parser = argparse.ArgumentParser(
        description="Analyze Polymarket markets using LLM intelligence layer"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input JSON file (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output JSON file (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--max-markets",
        type=int,
        default=None,
        help="Maximum number of markets to analyze (default: all)",
    )
    parser.add_argument(
        "--priority",
        type=str,
        choices=["quality", "speed", "cost"],
        default="quality",
        help="LLM backend priority (default: quality)",
    )
    parser.add_argument(
        "--no-dryrun",
        action="store_true",
        help="Disable DRYRUN mode (enable real API calls - requires API keys)",
    )

    args = parser.parse_args(argv)

    # Map priority string to enum
    priority_map = {
        "quality": Priority.QUALITY,
        "speed": Priority.SPEED,
        "cost": Priority.COST,
    }
    priority = priority_map[args.priority]

    print("[ho_llm_polymarket] Starting LLM Polymarket Analyzer")
    print(f"[ho_llm_polymarket] Input: {args.input}")
    print(f"[ho_llm_polymarket] Output: {args.output}")
    print(f"[ho_llm_polymarket] Priority: {args.priority}")
    print(f"[ho_llm_polymarket] DRYRUN mode: {not args.no_dryrun}")

    # Load markets
    markets = load_markets(args.input)
    if not markets:
        print("[ho_llm_polymarket] No markets to analyze, exiting")
        return

    # Initialize LLM analyst
    analyst = LLMMarketAnalyst(
        default_priority=priority,
        enable_fallback=True,
        dry_run=not args.no_dryrun,  # DRYRUN by default
    )

    # Get analyst status
    status = analyst.get_status()
    print(f"\n[ho_llm_polymarket] Analyst status:")
    print(f"  - DRYRUN mode: {status['dry_run']}")
    print(f"  - Has LLM backend: {status['has_llm_backend']}")
    print(f"  - Available backends: {status['available_backends']}")

    # Analyze markets
    results = analyze_markets_with_llm(markets, analyst, args.max_markets)

    # Write output
    write_output(results, args.output, status)

    print("\n[ho_llm_polymarket] Analysis complete")


if __name__ == "__main__":
    main()
