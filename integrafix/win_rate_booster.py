#!/usr/bin/env python3
"""
INTEGRAFIX: Win Rate Booster
============================

Improve win rate from 54.4% → 60%+ through:
1. Stricter signal filtering
2. Historical pattern recognition
3. Category-based filtering
4. Confidence thresholds

Current blockers to Tier 1:
- Win rate 54.4% < required 55%

Strategy: Only take highest-quality signals until win rate improves.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
LOGS_DIR = PROJECT_ROOT / "logs"
BOOSTER_STATE = STATE_DIR / "win_rate_booster.json"


@dataclass
class SignalFilter:
    """Configuration for signal filtering."""
    min_edge: float  # Minimum edge required
    min_confidence: float  # Minimum confidence required
    min_composite_score: float  # Minimum composite score
    max_price_extreme: float  # Max distance from 0.5
    allowed_categories: List[str]  # Which market categories to trade
    blocked_keywords: List[str]  # Keywords to avoid


# Aggressive filtering for win rate improvement
BOOST_MODE_FILTER = SignalFilter(
    min_edge=0.08,  # 8% minimum edge (was 3%)
    min_confidence=0.65,  # 65% confidence (was 50%)
    min_composite_score=0.75,  # High composite score
    max_price_extreme=0.4,  # Avoid extreme prices (< 0.1 or > 0.9)
    allowed_categories=[
        "politics_us",  # 62% historical WR
        "tech",  # 61% historical WR
        "finance",  # 60% historical WR
        "science",  # 59% historical WR
    ],
    blocked_keywords=[
        "sports", "nfl", "nba", "mlb",  # 52% WR - avoid
        "entertainment", "celebrity", "movie",  # 54% WR - avoid
    ]
)

# Normal mode filter (less strict)
NORMAL_MODE_FILTER = SignalFilter(
    min_edge=0.05,
    min_confidence=0.55,
    min_composite_score=0.65,
    max_price_extreme=0.45,
    allowed_categories=[
        "politics_us", "tech", "finance", "science",
        "crypto", "politics_intl"
    ],
    blocked_keywords=["sports", "nfl", "nba"]
)


class WinRateBooster:
    """Boost win rate through intelligent filtering."""

    def __init__(self):
        self.state = self._load_state()
        self.current_win_rate = self._get_current_win_rate()

    def _load_state(self) -> Dict:
        """Load booster state."""
        if BOOSTER_STATE.exists():
            with open(BOOSTER_STATE) as f:
                return json.load(f)
        return {
            "mode": "boost",  # boost or normal
            "signals_filtered": 0,
            "signals_passed": 0,
            "started_at": datetime.now(timezone.utc).isoformat()
        }

    def _save_state(self):
        """Save booster state."""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(BOOSTER_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _get_current_win_rate(self) -> float:
        """Get current win rate from HFT logs."""
        hft_log = LOGS_DIR / "hft_economics.jsonl"
        if not hft_log.exists():
            return 0.5

        wins = 0
        total = 0
        with open(hft_log) as f:
            for line in f:
                try:
                    d = json.loads(line)
                    if d.get("type") == "trade_close":
                        total += 1
                        if d.get("cost", 0) > 0:
                            wins += 1
                except:
                    pass

        return wins / total if total > 0 else 0.5

    def get_active_filter(self) -> SignalFilter:
        """Get the currently active filter based on win rate."""
        if self.current_win_rate < 0.55:
            return BOOST_MODE_FILTER
        elif self.current_win_rate < 0.58:
            return NORMAL_MODE_FILTER
        else:
            # Winning, can relax slightly
            return NORMAL_MODE_FILTER

    def categorize_market(self, title: str) -> str:
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

    def should_take_signal(
        self,
        market_title: str,
        edge: float,
        confidence: float,
        price: float,
        composite_score: float = 0.5
    ) -> Tuple[bool, str]:
        """
        Determine if a signal should be taken.

        Returns (should_take, reason)
        """
        filter_config = self.get_active_filter()
        category = self.categorize_market(market_title)

        # Check edge
        if edge < filter_config.min_edge:
            self.state["signals_filtered"] += 1
            self._save_state()
            return False, f"Edge {edge*100:.1f}% < min {filter_config.min_edge*100:.0f}%"

        # Check confidence
        if confidence < filter_config.min_confidence:
            self.state["signals_filtered"] += 1
            self._save_state()
            return False, f"Confidence {confidence*100:.0f}% < min {filter_config.min_confidence*100:.0f}%"

        # Check composite score
        if composite_score < filter_config.min_composite_score:
            self.state["signals_filtered"] += 1
            self._save_state()
            return False, f"Composite {composite_score:.2f} < min {filter_config.min_composite_score:.2f}"

        # Check price extremes
        price_distance = abs(price - 0.5)
        if price_distance > filter_config.max_price_extreme:
            self.state["signals_filtered"] += 1
            self._save_state()
            return False, f"Price {price:.2f} too extreme"

        # Check category
        if category not in filter_config.allowed_categories and category != "unknown":
            self.state["signals_filtered"] += 1
            self._save_state()
            return False, f"Category '{category}' not in allowed list"

        # Check blocked keywords
        title_lower = market_title.lower()
        for keyword in filter_config.blocked_keywords:
            if keyword in title_lower:
                self.state["signals_filtered"] += 1
                self._save_state()
                return False, f"Blocked keyword: {keyword}"

        # Signal passed all filters
        self.state["signals_passed"] += 1
        self._save_state()
        return True, "Signal approved"

    def get_status(self) -> Dict:
        """Get booster status."""
        filter_config = self.get_active_filter()
        mode = "BOOST" if filter_config == BOOST_MODE_FILTER else "NORMAL"

        total = self.state["signals_filtered"] + self.state["signals_passed"]
        pass_rate = self.state["signals_passed"] / total if total > 0 else 0

        return {
            "mode": mode,
            "current_win_rate": self.current_win_rate,
            "target_win_rate": 0.55,
            "gap": max(0, 0.55 - self.current_win_rate),
            "signals_filtered": self.state["signals_filtered"],
            "signals_passed": self.state["signals_passed"],
            "pass_rate": pass_rate,
            "filter_config": {
                "min_edge": filter_config.min_edge,
                "min_confidence": filter_config.min_confidence,
                "min_composite": filter_config.min_composite_score,
                "allowed_categories": filter_config.allowed_categories
            }
        }


def get_booster() -> WinRateBooster:
    """Get singleton booster instance."""
    return WinRateBooster()


def status_report() -> str:
    """Generate booster status report."""
    booster = WinRateBooster()
    status = booster.get_status()

    mode_emoji = "🔥" if status["mode"] == "BOOST" else "🟢"

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║             WIN RATE BOOSTER                                 ║",
        "╠══════════════════════════════════════════════════════════════╣",
        f"║  Mode: {mode_emoji} {status['mode']:<52} ║",
        f"║  Current Win Rate: {status['current_win_rate']*100:>6.1f}%                               ║",
        f"║  Target Win Rate: {status['target_win_rate']*100:>6.0f}%                                ║",
        f"║  Gap: {status['gap']*100:>+6.1f}%                                            ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║  FILTER STATS:                                               ║",
        f"║    Signals Filtered: {status['signals_filtered']:>6}                                ║",
        f"║    Signals Passed: {status['signals_passed']:>6}                                  ║",
        f"║    Pass Rate: {status['pass_rate']*100:>6.1f}%                                     ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║  ACTIVE FILTERS:                                             ║",
        f"║    Min Edge: {status['filter_config']['min_edge']*100:>5.0f}%                                       ║",
        f"║    Min Confidence: {status['filter_config']['min_confidence']*100:>5.0f}%                                 ║",
        f"║    Min Composite: {status['filter_config']['min_composite']:>6.2f}                                  ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║  ALLOWED CATEGORIES:                                         ║",
    ]

    for cat in status['filter_config']['allowed_categories']:
        lines.append(f"║    • {cat:<52} ║")

    lines.extend([
        "╠══════════════════════════════════════════════════════════════╣",
        "║  Strategy: Only take high-quality signals until WR > 55%    ║",
        "╚══════════════════════════════════════════════════════════════╝",
    ])

    return "\n".join(lines)


def main():
    print(status_report())


if __name__ == "__main__":
    main()
