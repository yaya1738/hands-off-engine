#!/usr/bin/env python3
"""
pm_model.py

Hands-Off Polymarket model runner (Termux side).

- Reads:  $HOME/hands-off-out/state/polymarket-compact.json
- Uses:   polymarket_skeleton.analyze_markets(...)
- Writes: $HOME/hands-off-out/state/polymarket-model.json
          $HOME/hands-off-out/state/polymarket-model.txt (human-readable)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from polymarket_skeleton import analyze_markets


STATE_DIR = Path.home() / "hands-off-out" / "state"
INPUT_FILE = STATE_DIR / "polymarket-compact.json"
OUTPUT_JSON = STATE_DIR / "polymarket-model.json"
OUTPUT_TXT = STATE_DIR / "polymarket-model.txt"


def load_markets() -> List[Dict[str, Any]]:
    if not INPUT_FILE.exists():
        print(f"[pm_model] missing input: {INPUT_FILE}")
        return []

    try:
        raw = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[pm_model] failed to read {INPUT_FILE}: {e}")
        return []

    if isinstance(raw, dict) and "markets" in raw:
        markets_raw = raw["markets"]
    elif isinstance(raw, list):
        markets_raw = raw
    else:
        print("[pm_model] unexpected JSON shape (need list or {'markets': [...]})")
        return []

    if not isinstance(markets_raw, list):
        print("[pm_model] markets_raw is not a list, aborting")
        return []

    return markets_raw


def write_outputs(analyzed: List[Dict[str, Any]]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # 1) JSON dump
    payload = {"markets": analyzed, "generated_at": datetime.now(timezone.utc).isoformat()}
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[pm_model] wrote {OUTPUT_JSON} with {len(analyzed)} markets")

    # 2) Text summary (sorted by composite score, then by edge)
    lines: List[str] = []
    ts = datetime.now(timezone.utc).isoformat()
    lines.append(f"[pm_model] summary generated @ {ts} UTC")
    lines.append(f"total_markets: {len(analyzed)}")
    lines.append("")

    # Sort by composite score descending (alpha scoring), then by |edge|, then by volume
    def sort_key(m: Dict[str, Any]):
        score = float(m.get("score", 0.0))
        edge = float(m.get("edge", 0.0))
        vol = float(m.get("volume") or 0.0)
        return (-score, -abs(edge), -vol)

    top = sorted(analyzed, key=sort_key)

    for m in top[:50]:  # cap at top 50 for readability
        rec = str(m.get("rec", "hold"))
        score = float(m.get("score", 0.0))
        edge = float(m.get("edge", 0.0))
        fair = float(m.get("fair_yes", 0.0))
        yes_price = float(m.get("yes_price", 0.0))
        cat = str(m.get("category", "other"))
        q = str(m.get("question", ""))

        # trim long questions
        if len(q) > 140:
            q = q[:137] + "..."

        lines.append(
            f"{rec:8} | cat={cat:8} | score={score:.4f} | edge={edge:+.3f} | fair={fair:.3f} | yes={yes_price:.3f} | {q}"
        )

    OUTPUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[pm_model] wrote {OUTPUT_TXT}")
    

def main() -> None:
    markets_raw = load_markets()
    if not markets_raw:
        print("[pm_model] no markets to analyze (missing or invalid input)")
        return

    context: Dict[str, Any] = {
        # edge threshold in basis points before BUY vs HOLD
        "target_edge_bps": 500.0,  # 5% default; tune later
    }

    analyzed = analyze_markets(markets_raw, context)
    write_outputs(analyzed)


if __name__ == "__main__":
    main()
