#!/usr/bin/env python3
"""
Analyze shadow-mode trades logged to state/shadow_trades.jsonl.

Safe: read-only, no network calls.
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


import json
from collections import Counter
from pathlib import Path
from statistics import mean

SHADOW_PATH = Path("state/shadow_trades.jsonl")


def load_trades(path: Path):
    """Load all trades from shadow log, skipping bad lines."""
    if not path.exists():
        print(f"[warn] No shadow trades file found at {path}")
        return []

    trades = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                trades.append(json.loads(line))
            except Exception as e:
                print(f"[warn] Skipping bad line: {e}")
    return trades


def main():
    """Analyze shadow trades and print summary statistics."""
    trades = load_trades(SHADOW_PATH)
    if not trades:
        print("[info] No trades to analyze.")
        return

    total = len(trades)

    # Helper to safely get 'extra' field
    def extra(t):
        return t.get("extra", {}) or {}

    # Split by allowed/blocked
    blocked = [t for t in trades if not extra(t).get("allowed_by_safeguards", True)]
    allowed = [t for t in trades if extra(t).get("allowed_by_safeguards", True)]

    print(f"Total trades logged: {total}")
    print(f"  Would execute (allowed_by_safeguards==True): {len(allowed)}")
    print(f"  Blocked by safeguards:                       {len(blocked)}")
    print()

    # Confidence distribution
    confidences = [t.get("confidence") for t in trades if isinstance(t.get("confidence"), (int, float))]
    if confidences:
        print(f"Confidence:")
        print(f"  avg={mean(confidences):.3f}  min={min(confidences):.3f}  max={max(confidences):.3f}")
    else:
        print("Confidence: no numeric confidence field found.")
    print()

    # Position size distribution
    sizes = [t.get("size_usd") for t in trades if isinstance(t.get("size_usd"), (int, float))]
    if sizes:
        print(f"Position sizes (USD):")
        print(f"  avg=${mean(sizes):.2f}  min=${min(sizes):.2f}  max=${max(sizes):.2f}")

        # Check hard limit violations
        max_allowed = 200  # From hard_limits.json
        violations = [s for s in sizes if s > max_allowed]
        if violations:
            print(f"  ⚠️  HARD LIMIT VIOLATIONS: {len(violations)} trades exceeded ${max_allowed}")
        else:
            print(f"  ✓ All trades within hard limit (${max_allowed})")
    print()

    # Health check stats
    healthy_count = sum(1 for t in trades if t.get("health_ok", False))
    print(f"Health checks:")
    print(f"  Passed: {healthy_count}/{total} ({100*healthy_count/total:.1f}%)")

    # Health reasons for failures
    unhealthy = [t for t in trades if not t.get("health_ok", False)]
    if unhealthy:
        reasons = [t.get("health_reason", "unknown") for t in unhealthy]
        print(f"  Failed reasons:")
        for reason, cnt in Counter(reasons).most_common(5):
            print(f"    {reason}: {cnt}")
    print()

    # Risk phase distribution
    phases = [t.get("risk_phase", "unknown") for t in trades]
    print(f"Risk phase distribution:")
    for phase, cnt in Counter(phases).most_common():
        print(f"  {phase}: {cnt} ({100*cnt/total:.1f}%)")
    print()

    # Side distribution
    sides = [t.get("side", "unknown") for t in trades]
    print(f"Side distribution:")
    for side, cnt in Counter(sides).most_common():
        print(f"  {side}: {cnt} ({100*cnt/total:.1f}%)")
    print()

    # Block reasons if present
    if blocked:
        # Try to extract reasons from safety_checks
        block_reasons = []
        for t in blocked:
            checks = t.get("safety_checks", [])
            # Find the first check that doesn't say "OK"
            for check in checks:
                if "OK" not in check:
                    block_reasons.append(check)
                    break
            else:
                block_reasons.append("unknown")

        print("Blocked reasons (from safety_checks):")
        for reason, cnt in Counter(block_reasons).most_common(10):
            print(f"  {reason}: {cnt}")
        print()

    # Per-market counts (best effort)
    markets = [t.get("market_name") or t.get("market_id") for t in trades]
    markets = [m for m in markets if m]
    if markets:
        print("Top markets by trade count:")
        for market, cnt in Counter(markets).most_common(10):
            # Truncate long market names
            display = market[:50] + "..." if len(market) > 50 else market
            print(f"  {display}: {cnt}")
        print()

    # Time range
    timestamps = [t.get("timestamp") for t in trades if t.get("timestamp")]
    if timestamps:
        print(f"Time range:")
        print(f"  First: {timestamps[0]}")
        print(f"  Last:  {timestamps[-1]}")
        print()

    print("[ok] Shadow trades analysis complete.")


if __name__ == "__main__":
    main()
