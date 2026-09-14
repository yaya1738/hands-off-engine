#!/usr/bin/env python3
"""Improvement Feedback — tracks whether improvements actually helped.

Compares before/after metrics for each applied improvement and determines
if the improvement had a positive, neutral, or negative impact. Feeds
this back into the candidate generator so future improvements are informed
by what actually works.

Metrics tracked:
  - bus_lines: fewer lines after cleanup = positive
  - state_files: more files after adding docs = positive  
  - health_rate: higher health rate = positive
  - test_files: more tests = positive
  - execution_time: faster execution = positive

The feedback loop:
  1. Applier records before/after metrics with each improvement
  2. Feedback analyzer compares and scores each improvement
  3. Summary statistics feed back into self_improvement.py
  4. Future candidates prefer categories that historically helped
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
FEEDBACK_FILE = STATE / "improvement_feedback.json"
APPLIER_STATE = STATE / "improvement_applier_state.json"
HISTORY_FILE = STATE / "feedback_history.json"


def load_feedback():
    if FEEDBACK_FILE.exists():
        try:
            return json.loads(FEEDBACK_FILE.read_text())
        except Exception:
            pass
    return {"improvements": [], "summary": {}}


def save_feedback(feedback):
    FEEDBACK_FILE.write_text(json.dumps(feedback, indent=2) + "\n")


def load_applier_state():
    if APPLIER_STATE.exists():
        try:
            return json.loads(APPLIER_STATE.read_text())
        except Exception:
            pass
    return {"applied": []}


def score_impact(impact: dict) -> float:
    """Score improvement impact from before/after metrics.

    Returns a score from -1.0 (harmful) to +1.0 (beneficial).
    """
    if not impact:
        return 0.0

    scores = []
    for metric, delta in impact.items():
        if isinstance(delta, dict) and "delta" in delta:
            d = delta["delta"]
            before = delta.get("before", 0)
            if metric == "bus_lines":
                # Fewer bus lines is better (cleanup worked)
                scores.append(min(1.0, max(-1.0, -d / max(before, 1))))
            elif metric == "state_files":
                # More state files is usually good (more tracking)
                scores.append(min(1.0, max(-1.0, d / max(before, 1) * 0.5)))
            elif metric == "health_rate":
                # Higher health rate is better
                scores.append(min(1.0, max(-1.0, d * 2)))
            elif metric == "test_files":
                # More tests is better
                scores.append(min(1.0, max(-1.0, d * 0.3)))
            else:
                # Default: any positive delta is slightly good
                scores.append(0.1 if d > 0 else (-0.1 if d < 0 else 0.0))

    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def analyze_feedback():
    """Analyze all applied improvements and compute summary statistics."""
    feedback = load_feedback()
    applied = load_applier_state().get("applied", [])

    # Score each improvement
    scored = []
    for entry in applied:
        impact = entry.get("impact", {})
        score = score_impact(impact)
        scored.append({
            "id": entry.get("id", ""),
            "category": entry.get("category", ""),
            "title": entry.get("title", ""),
            "action": entry.get("action", ""),
            "score": score,
            "impact": impact,
            "applied_at": entry.get("applied_at", ""),
        })

    # Category-level summary
    category_scores = {}
    for s in scored:
        cat = s["category"]
        if cat not in category_scores:
            category_scores[cat] = {"scores": [], "count": 0}
        category_scores[cat]["scores"].append(s["score"])
        category_scores[cat]["count"] += 1

    category_summary = {}
    for cat, data in category_scores.items():
        avg = sum(data["scores"]) / max(len(data["scores"]), 1)
        category_summary[cat] = {
            "avg_score": round(avg, 3),
            "count": data["count"],
            "recommendation": "prefer" if avg > 0.1 else ("avoid" if avg < -0.1 else "neutral"),
        }

    # Overall summary
    all_scores = [s["score"] for s in scored]
    summary = {
        "total_improvements": len(scored),
        "avg_score": round(sum(all_scores) / max(len(all_scores), 1), 3),
        "positive_count": sum(1 for s in all_scores if s > 0.1),
        "negative_count": sum(1 for s in all_scores if s < -0.1),
        "neutral_count": sum(1 for s in all_scores if -0.1 <= s <= 0.1),
        "category_summary": category_summary,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    feedback["summary"] = summary
    feedback["improvements"] = scored[-200:]
    save_feedback(feedback)

    # Also save to history for trend analysis
    history = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text())
        except Exception:
            pass
    history.append({"timestamp": summary["analyzed_at"], "summary": summary})
    if len(history) > 100:
        history = history[-100:]
    HISTORY_FILE.write_text(json.dumps(history, indent=2) + "\n")

    return summary


def get_recommendations() -> Dict[str, str]:
    """Get category recommendations for the candidate generator."""
    feedback = load_feedback()
    summary = feedback.get("summary", {})
    cats = summary.get("category_summary", {})
    return {cat: info["recommendation"] for cat, info in cats.items()}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Improvement Feedback Analyzer")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("analyze", help="Analyze feedback and compute summary")
    sub.add_parser("recommend", help="Get category recommendations")
    sub.add_parser("status", help="Show feedback status")

    args = parser.parse_args()

    if args.cmd == "analyze":
        summary = analyze_feedback()
        print(json.dumps(summary, indent=2))
    elif args.cmd == "recommend":
        recs = get_recommendations()
        if recs:
            for cat, rec in recs.items():
                icon = "✅" if rec == "prefer" else ("❌" if rec == "avoid" else "➖")
                print(f"  {icon} {cat}: {rec}")
        else:
            print("  No data yet — apply improvements first")
    elif args.cmd == "status":
        feedback = load_feedback()
        print(f"Improvements tracked: {len(feedback.get('improvements', []))}")
        s = feedback.get("summary", {})
        if s:
            print(f"  Avg score: {s.get('avg_score', 'N/A')}")
            print(f"  Positive: {s.get('positive_count', 0)}")
            print(f"  Negative: {s.get('negative_count', 0)}")
            print(f"  Neutral: {s.get('neutral_count', 0)}")
    else:
        parser.print_help()
