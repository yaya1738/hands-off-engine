#!/usr/bin/env python3
"""
Hands-Off Decider

Reads various alpha signals and produces a decision report for execution.
Currently integrates:
- LLM alpha report (from llm/ho_llm_polymarket.py)
- Future: risk metrics, infrastructure status, etc.

Output: decision_report.json with trading decisions and analysis
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(name)s] %(message)s'
)
logger = logging.getLogger('ho_decider')

# Paths
STATE_DIR = Path.home() / "hands-off-out" / "state"
LLM_ALPHA_REPORT_PATH = STATE_DIR / "llm_alpha_report.json"
DECISION_REPORT_PATH = STATE_DIR / "decision_report.json"

# Configuration
TOP_N_CANDIDATES = 10  # How many top LLM candidates to include


def load_llm_alpha_report(path: Path = LLM_ALPHA_REPORT_PATH) -> Optional[Dict[str, Any]]:
    """
    Load LLM alpha report with safe error handling.

    Returns None if file is missing or invalid, with appropriate logging.
    Never raises exceptions that would crash the decider.
    """
    if not path.exists():
        logger.warning(f"LLM alpha report not found at {path}")
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Basic validation
        if not isinstance(data, dict):
            logger.warning(f"LLM alpha report has invalid structure (not a dict)")
            return None

        # Check for expected fields
        required_fields = ['total_markets', 'llm_analyzed', 'markets']
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            logger.warning(f"LLM alpha report missing fields: {missing_fields}")
            return None

        logger.info(f"Loaded LLM alpha report: {data['llm_analyzed']}/{data['total_markets']} markets analyzed")
        return data

    except json.JSONDecodeError as e:
        logger.warning(f"LLM alpha report contains invalid JSON: {e}")
        return None
    except Exception as e:
        logger.warning(f"Failed to load LLM alpha report: {e}")
        return None


def extract_top_llm_candidates(
    llm_report: Dict[str, Any],
    top_n: int = TOP_N_CANDIDATES
) -> List[Dict[str, Any]]:
    """
    Extract top N candidates from LLM alpha report.

    Sorts by absolute edge and returns most promising opportunities.
    """
    markets = llm_report.get('markets', [])

    if not markets:
        return []

    # Filter to only markets with LLM analysis
    analyzed_markets = [
        m for m in markets
        if m.get('analysis_source') == 'llm' and m.get('llm_analysis')
    ]

    # Sort by absolute edge (descending)
    def get_abs_edge(market):
        analysis = market.get('llm_analysis', {})
        edge_bps = analysis.get('edge_bps', 0)
        return abs(edge_bps)

    sorted_markets = sorted(analyzed_markets, key=get_abs_edge, reverse=True)

    # Take top N and format for decision report
    top_candidates = []
    for market in sorted_markets[:top_n]:
        analysis = market['llm_analysis']
        edge_bps = analysis.get('edge_bps', 0)

        candidate = {
            'market_id': market.get('id', ''),
            'slug': market.get('slug', market.get('id', '')),
            'ticker': market.get('ticker', ''),
            'question': market.get('question', ''),
            'category': market.get('category', 'unknown'),
            'fair_probability': analysis.get('fair_probability'),
            'market_price': market.get('yes_price'),
            'edge_bps': edge_bps,
            'edge_pct_points': round(edge_bps / 100, 2),
            'recommendation': analysis.get('action', 'avoid'),
            'confidence': analysis.get('confidence', 'unknown'),
            'reasoning': analysis.get('reasoning', ''),
        }
        top_candidates.append(candidate)

    return top_candidates


def build_llm_alpha_section(llm_report: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build the llm_alpha section for decision_report.json

    If llm_report is None or invalid, returns a disabled section.
    """
    if llm_report is None:
        return {
            'enabled': False,
            'reason': 'LLM alpha report not available'
        }

    try:
        top_candidates = extract_top_llm_candidates(llm_report, TOP_N_CANDIDATES)

        analyst_status = llm_report.get('analyst_status', {})

        return {
            'enabled': True,
            'generated_at': llm_report.get('generated_at'),
            'total_markets': llm_report.get('total_markets'),
            'llm_analyzed': llm_report.get('llm_analyzed'),
            'fallback_count': llm_report.get('fallback_count', 0),
            'dry_run': analyst_status.get('dry_run', True),
            'top_candidates': top_candidates,
        }

    except Exception as e:
        logger.warning(f"Failed to build LLM alpha section: {e}")
        return {
            'enabled': False,
            'reason': f'Error processing LLM report: {e}'
        }


def build_decision_report(llm_report_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Build the complete decision report.

    This is the main entry point that assembles all decision components.

    Args:
        llm_report_path: Optional path to LLM alpha report (for testing)
    """
    # Load LLM alpha report
    if llm_report_path is None:
        llm_report_path = LLM_ALPHA_REPORT_PATH
    llm_report = load_llm_alpha_report(llm_report_path)

    # Build llm_alpha section
    llm_alpha_section = build_llm_alpha_section(llm_report)

    # Build complete decision report
    decision_report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0',
        'dry_run': True,  # Currently DRYRUN-only

        # LLM alpha integration
        'llm_alpha': llm_alpha_section,

        # Placeholder for future integrations
        'risk_metrics': {
            'enabled': False,
            'reason': 'Not yet implemented'
        },

        'infrastructure': {
            'enabled': False,
            'reason': 'Not yet implemented'
        },

        # Placeholder for orders (future: executor will use this)
        'polymarket': {
            'orders': [],
            'reason': 'DRYRUN mode - no orders generated yet'
        }
    }

    return decision_report


def write_decision_report(report: Dict[str, Any], path: Path = DECISION_REPORT_PATH) -> None:
    """Write decision report to JSON file"""
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write report
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Wrote decision report to {path}")


def main():
    """Main entry point for decider"""
    logger.info("Starting Hands-Off Decider")

    # Check for DRYRUN flag
    dry_run = '--live' not in sys.argv
    if not dry_run:
        logger.warning("LIVE mode requested but not yet supported - forcing DRYRUN")
        dry_run = True

    logger.info(f"Running in {'DRYRUN' if dry_run else 'LIVE'} mode")

    # Build decision report
    decision_report = build_decision_report()

    # Write output
    write_decision_report(decision_report)

    # Print summary
    llm_alpha = decision_report.get('llm_alpha', {})
    if llm_alpha.get('enabled'):
        logger.info(f"LLM Alpha: {llm_alpha.get('llm_analyzed', 0)} markets analyzed")
        logger.info(f"Top candidates: {len(llm_alpha.get('top_candidates', []))}")
    else:
        logger.info(f"LLM Alpha: disabled ({llm_alpha.get('reason', 'unknown')})")

    logger.info("Decider complete")


if __name__ == '__main__':
    main()
