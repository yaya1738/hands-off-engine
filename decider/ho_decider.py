#!/usr/bin/env python3
"""
ho_decider.py - Decision logic for scored candidates (DRYRUN-safe)

Reads alpha/alpha_candidates_scored.json and applies decision rules to generate
decider/decisions.json with trading decisions.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

ALPHA_DIR = Path(__file__).parent.parent / "alpha"
INPUT_FILE = ALPHA_DIR / "alpha_candidates_scored.json"
OUTPUT_FILE = Path(__file__).parent / "decisions.json"

SCORE_THRESHOLD = 0.15  # Minimum score to consider
EDGE_THRESHOLD = 0.08   # Minimum edge to act


def load_candidates() -> List[Dict[str, Any]]:
    """Load scored candidates from alpha pipeline"""
    if not INPUT_FILE.exists():
        print(f"[decider] Input file not found: {INPUT_FILE}")
        return []

    try:
        data = json.loads(INPUT_FILE.read_text())
        return data.get('ranked_candidates', [])
    except Exception as e:
        print(f"[decider] Failed to load candidates: {e}")
        return []


def make_decisions(candidates: List[Dict[str, Any]], dryrun: bool = True) -> List[Dict[str, Any]]:
    """Generate trading decisions from scored candidates"""
    decisions = []

    for cand in candidates:
        score = cand.get('score', 0)
        edge = abs(cand.get('edge_raw', 0))
        rec = cand.get('rec', 'hold')

        # Decision rules
        if score < SCORE_THRESHOLD or edge < EDGE_THRESHOLD:
            action = 'skip'
            reason = f'Score {score:.4f} or edge {edge:.3f} below threshold'
        elif rec == 'hold':
            action = 'skip'
            reason = 'Recommendation is HOLD'
        else:
            action = rec  # buy_yes or buy_no
            reason = f'Score {score:.4f} > threshold, edge {edge:.3f}'

        decision = {
            'candidate_id': cand.get('key', 'unknown'),
            'question': cand.get('question', ''),
            'action': action,
            'score': score,
            'edge': cand.get('edge_raw', 0),
            'category': cand.get('category', 'other'),
            'reason': reason,
            'dryrun': dryrun
        }
        decisions.append(decision)

    return decisions


def main():
    # Default to DRYRUN unless explicitly disabled
    dryrun = '--live' not in sys.argv

    print(f"[decider] Running in {'DRYRUN' if dryrun else 'LIVE'} mode")

    candidates = load_candidates()
    if not candidates:
        print("[decider] No candidates to process")
        return

    print(f"[decider] Processing {len(candidates)} candidates...")
    decisions = make_decisions(candidates, dryrun=dryrun)

    # Count actions
    actions = {}
    for d in decisions:
        action = d['action']
        actions[action] = actions.get(action, 0) + 1

    print(f"[decider] Decisions: {dict(actions)}")

    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output_data = {
        'decisions': decisions,
        'summary': actions,
        'dryrun': dryrun
    }
    OUTPUT_FILE.write_text(json.dumps(output_data, indent=2))

    print(f"[decider] Wrote {len(decisions)} decisions to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
