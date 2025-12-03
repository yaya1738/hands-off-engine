#!/usr/bin/env python3
"""
INTEGRAFIX: Golden State Configuration
======================================

Target: $5,000,000/month
Strategy: Progressive scaling based on proven performance

The golden state is reached when:
1. System has proven edge (win rate > 60%)
2. Risk management is battle-tested
3. Infrastructure is hardened for 24/7
4. Capital efficiency is maximized
5. Auto-scaling is operational

Scaling tiers:
- Tier 0 (Validation): $200 exposure, prove the edge
- Tier 1 (Foundation): $5,000 exposure, 10x scale
- Tier 2 (Growth): $50,000 exposure, 100x scale
- Tier 3 (Acceleration): $175,000 exposure, 875x scale
- Tier 4 (Golden): $500,000+ exposure, target $5M/month
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
GOLDEN_STATE_FILE = STATE_DIR / "golden_state.json"


@dataclass
class ScalingTier:
    """Configuration for a scaling tier."""
    name: str
    max_exposure: float
    max_position: float
    daily_trade_limit: int
    min_edge_threshold: float  # Minimum expected edge to execute
    kelly_fraction: float  # Fraction of Kelly to use (conservative)
    required_win_rate: float  # Must maintain this to stay in tier
    required_trades: int  # Trades needed to advance


SCALING_TIERS = {
    0: ScalingTier(
        name="Validation",
        max_exposure=200,
        max_position=25,
        daily_trade_limit=10,
        min_edge_threshold=0.02,
        kelly_fraction=0.25,
        required_win_rate=0.55,
        required_trades=100
    ),
    1: ScalingTier(
        name="Foundation",
        max_exposure=5000,
        max_position=500,
        daily_trade_limit=50,
        min_edge_threshold=0.03,
        kelly_fraction=0.30,
        required_win_rate=0.57,
        required_trades=500
    ),
    2: ScalingTier(
        name="Growth",
        max_exposure=50000,
        max_position=5000,
        daily_trade_limit=200,
        min_edge_threshold=0.03,
        kelly_fraction=0.35,
        required_win_rate=0.58,
        required_trades=2000
    ),
    3: ScalingTier(
        name="Acceleration",
        max_exposure=175000,
        max_position=20000,
        daily_trade_limit=500,
        min_edge_threshold=0.025,
        kelly_fraction=0.40,
        required_win_rate=0.58,
        required_trades=5000
    ),
    4: ScalingTier(
        name="Golden",
        max_exposure=500000,
        max_position=50000,
        daily_trade_limit=1000,
        min_edge_threshold=0.02,
        kelly_fraction=0.45,
        required_win_rate=0.57,
        required_trades=10000
    )
}


@dataclass
class GoldenState:
    """Track progress toward golden state."""
    current_tier: int
    total_trades: int
    total_pnl: float
    win_rate: float
    tier_trades: int  # Trades at current tier
    tier_pnl: float  # P&L at current tier
    tier_started: str
    last_updated: str
    golden_achieved: bool = False
    golden_achieved_at: Optional[str] = None

    def get_tier_config(self) -> ScalingTier:
        return SCALING_TIERS[self.current_tier]

    def check_tier_advancement(self) -> bool:
        """Check if ready to advance to next tier."""
        tier = self.get_tier_config()

        if self.current_tier >= 4:
            return False  # Already at golden

        meets_trades = self.tier_trades >= tier.required_trades
        meets_win_rate = self.win_rate >= tier.required_win_rate
        meets_profitability = self.tier_pnl > 0

        return meets_trades and meets_win_rate and meets_profitability

    def advance_tier(self):
        """Advance to next tier."""
        if self.current_tier < 4 and self.check_tier_advancement():
            self.current_tier += 1
            self.tier_trades = 0
            self.tier_pnl = 0
            self.tier_started = datetime.now(timezone.utc).isoformat()

            if self.current_tier == 4:
                self.golden_achieved = True
                self.golden_achieved_at = datetime.now(timezone.utc).isoformat()

    def record_trade(self, pnl: float, won: bool):
        """Record a trade result."""
        self.total_trades += 1
        self.tier_trades += 1
        self.total_pnl += pnl
        self.tier_pnl += pnl

        # Recalculate win rate (exponential moving average)
        alpha = 0.01  # Smoothing factor
        self.win_rate = alpha * (1 if won else 0) + (1 - alpha) * self.win_rate

        self.last_updated = datetime.now(timezone.utc).isoformat()

        # Check for tier advancement
        self.advance_tier()

    def monthly_projection(self) -> float:
        """Project monthly P&L at current rate."""
        if self.total_trades == 0:
            return 0
        avg_per_trade = self.total_pnl / self.total_trades
        tier = self.get_tier_config()
        # Assume we can hit daily trade limit
        daily_trades = tier.daily_trade_limit
        return avg_per_trade * daily_trades * 30

    def to_dict(self):
        return asdict(self)

    def save(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(GOLDEN_STATE_FILE, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls) -> 'GoldenState':
        if GOLDEN_STATE_FILE.exists():
            with open(GOLDEN_STATE_FILE) as f:
                data = json.load(f)
            return cls(**data)
        return cls.initialize()

    @classmethod
    def initialize(cls) -> 'GoldenState':
        """Initialize from current HFT logs."""
        # Load current performance
        hft_log = PROJECT_ROOT / "logs" / "hft_economics.jsonl"
        total_trades = 0
        total_pnl = 0
        wins = 0

        if hft_log.exists():
            with open(hft_log) as f:
                for line in f:
                    try:
                        d = json.loads(line)
                        if d.get("type") == "trade_close":
                            total_trades += 1
                            pnl = d.get("cost", 0)
                            total_pnl += pnl
                            if pnl > 0:
                                wins += 1
                    except:
                        pass

        win_rate = wins / total_trades if total_trades > 0 else 0.5
        now = datetime.now(timezone.utc).isoformat()

        state = cls(
            current_tier=0,
            total_trades=total_trades,
            total_pnl=total_pnl,
            win_rate=win_rate,
            tier_trades=total_trades,
            tier_pnl=total_pnl,
            tier_started=now,
            last_updated=now
        )

        # Check if we should already be at a higher tier
        while state.check_tier_advancement():
            state.advance_tier()

        state.save()
        return state


def get_current_limits() -> dict:
    """Get current trading limits based on golden state."""
    state = GoldenState.load()
    tier = state.get_tier_config()

    return {
        "tier": state.current_tier,
        "tier_name": tier.name,
        "max_exposure": tier.max_exposure,
        "max_position": tier.max_position,
        "daily_trade_limit": tier.daily_trade_limit,
        "min_edge": tier.min_edge_threshold,
        "kelly_fraction": tier.kelly_fraction,
        "golden_achieved": state.golden_achieved
    }


def status_report() -> str:
    """Generate golden state status report."""
    state = GoldenState.load()
    tier = state.get_tier_config()
    projection = state.monthly_projection()

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║             GOLDEN STATE PROGRESS TRACKER                    ║",
        "╠══════════════════════════════════════════════════════════════╣",
    ]

    if state.golden_achieved:
        lines.append("║  🏆 GOLDEN STATE ACHIEVED 🏆                                 ║")
        lines.append(f"║  Achieved: {state.golden_achieved_at[:19]:<43} ║")
    else:
        progress = min(100, (state.tier_trades / tier.required_trades) * 100)
        lines.append(f"║  Current Tier: {state.current_tier} - {tier.name:<42} ║")
        lines.append(f"║  Progress to next tier: {progress:>5.1f}%                            ║")

    lines.extend([
        "╠══════════════════════════════════════════════════════════════╣",
        f"║  Total Trades: {state.total_trades:>6,}                                      ║",
        f"║  Total P&L: ${state.total_pnl:>+12,.2f}                                ║",
        f"║  Win Rate: {state.win_rate*100:>6.1f}%                                       ║",
        "╠══════════════════════════════════════════════════════════════╣",
        f"║  Current Limits:                                             ║",
        f"║    Max Exposure: ${tier.max_exposure:>12,.0f}                            ║",
        f"║    Max Position: ${tier.max_position:>12,.0f}                            ║",
        f"║    Daily Trades: {tier.daily_trade_limit:>6}                                    ║",
        "╠══════════════════════════════════════════════════════════════╣",
        f"║  Monthly Projection: ${projection:>14,.0f}                       ║",
        f"║  Target: $5,000,000                                          ║",
        f"║  Gap: ${5_000_000 - projection:>+16,.0f}                         ║",
        "╚══════════════════════════════════════════════════════════════╝",
    ])

    # Show tier roadmap
    lines.append("\n  TIER ROADMAP:")
    for t_num, t_config in SCALING_TIERS.items():
        marker = "→" if t_num == state.current_tier else " "
        check = "✓" if t_num < state.current_tier else "○"
        if state.golden_achieved and t_num == 4:
            check = "🏆"
        lines.append(f"  {marker} [{check}] Tier {t_num}: {t_config.name:<12} ${t_config.max_exposure:>10,.0f} exposure")

    return "\n".join(lines)


def main():
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "init":
            state = GoldenState.initialize()
            print(f"Initialized at Tier {state.current_tier}")
        elif cmd == "limits":
            limits = get_current_limits()
            print(json.dumps(limits, indent=2))
        elif cmd == "advance":
            state = GoldenState.load()
            if state.check_tier_advancement():
                state.advance_tier()
                state.save()
                print(f"Advanced to Tier {state.current_tier}")
            else:
                print("Not ready to advance")
        else:
            print(status_report())
    else:
        print(status_report())


if __name__ == "__main__":
    main()
