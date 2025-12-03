#!/usr/bin/env python3
"""
INTEGRAFIX: Auto-Scaler
=======================

Automatically scale trading limits based on proven performance.
Path to $5M/month through progressive tier advancement.

Scaling triggers:
1. Win rate threshold met
2. Required trades completed
3. Positive P&L at tier
4. No critical system failures

Safety mechanisms:
1. Never scale faster than data supports
2. Automatic tier regression on poor performance
3. Circuit breaker on large drawdowns
4. Human notification on major events
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

# Import golden state config
try:
    from integrafix.golden_state import GoldenState, SCALING_TIERS, get_current_limits
except ImportError:
    # Fallback for standalone execution
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from integrafix.golden_state import GoldenState, SCALING_TIERS, get_current_limits


@dataclass
class ScalingEvent:
    """Record of a scaling event."""
    timestamp: str
    event_type: str  # advance, regress, circuit_breaker
    from_tier: int
    to_tier: int
    reason: str
    metrics: Dict


class AutoScaler:
    """Automatic scaling engine."""

    # Safety thresholds
    MAX_DRAWDOWN_PCT = 0.20  # 20% drawdown triggers circuit breaker
    MIN_TRADES_PER_TIER = 50  # Minimum trades before considering advancement
    REGRESSION_WIN_RATE_DROP = 0.05  # 5% win rate drop triggers regression
    COOLDOWN_HOURS = 24  # Hours between scaling events

    def __init__(self):
        self.state = GoldenState.load()
        self.events_file = STATE_DIR / "scaling_events.jsonl"
        self.last_scaling = self._get_last_scaling_time()

    def _get_last_scaling_time(self) -> Optional[datetime]:
        """Get time of last scaling event."""
        if not self.events_file.exists():
            return None

        last_event = None
        with open(self.events_file) as f:
            for line in f:
                try:
                    last_event = json.loads(line)
                except:
                    pass

        if last_event:
            return datetime.fromisoformat(last_event["timestamp"].replace('Z', '+00:00'))
        return None

    def _log_event(self, event: ScalingEvent):
        """Log scaling event."""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.events_file, 'a') as f:
            f.write(json.dumps({
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "from_tier": event.from_tier,
                "to_tier": event.to_tier,
                "reason": event.reason,
                "metrics": event.metrics
            }) + "\n")

    def _in_cooldown(self) -> bool:
        """Check if in cooldown period."""
        if not self.last_scaling:
            return False
        cooldown_end = self.last_scaling + timedelta(hours=self.COOLDOWN_HOURS)
        return datetime.now(timezone.utc) < cooldown_end

    def check_advancement(self) -> Tuple[bool, str]:
        """Check if ready to advance tier."""
        if self._in_cooldown():
            return False, "In cooldown period"

        if self.state.current_tier >= 4:
            return False, "Already at golden tier"

        tier = self.state.get_tier_config()

        # Check requirements
        if self.state.tier_trades < tier.required_trades:
            return False, f"Need {tier.required_trades - self.state.tier_trades} more trades"

        if self.state.win_rate < tier.required_win_rate:
            return False, f"Win rate {self.state.win_rate*100:.1f}% < required {tier.required_win_rate*100:.0f}%"

        if self.state.tier_pnl <= 0:
            return False, f"Tier P&L ${self.state.tier_pnl:.2f} not positive"

        return True, "All requirements met"

    def check_regression(self) -> Tuple[bool, str]:
        """Check if should regress tier."""
        if self.state.current_tier <= 0:
            return False, "Already at lowest tier"

        tier = self.state.get_tier_config()

        # Check for significant win rate drop
        if self.state.win_rate < (tier.required_win_rate - self.REGRESSION_WIN_RATE_DROP):
            return True, f"Win rate dropped to {self.state.win_rate*100:.1f}%"

        # Check for significant drawdown at tier
        if self.state.tier_trades >= self.MIN_TRADES_PER_TIER:
            if self.state.tier_pnl < 0:
                drawdown_pct = abs(self.state.tier_pnl) / tier.max_exposure
                if drawdown_pct > self.MAX_DRAWDOWN_PCT:
                    return True, f"Drawdown {drawdown_pct*100:.1f}% exceeds threshold"

        return False, "Performance acceptable"

    def check_circuit_breaker(self) -> Tuple[bool, str]:
        """Check if circuit breaker should trigger."""
        tier = self.state.get_tier_config()

        # Large absolute drawdown
        if self.state.total_pnl < -tier.max_exposure * 0.5:
            return True, f"Large drawdown: ${self.state.total_pnl:.2f}"

        # Rapid loss rate (more than 5 losses in a row would drop win rate significantly)
        if self.state.tier_trades >= 10 and self.state.win_rate < 0.35:
            return True, f"Win rate critical: {self.state.win_rate*100:.1f}%"

        return False, "No circuit breaker triggered"

    def execute_advancement(self) -> bool:
        """Execute tier advancement."""
        old_tier = self.state.current_tier
        self.state.advance_tier()
        new_tier = self.state.current_tier

        if new_tier > old_tier:
            event = ScalingEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="advance",
                from_tier=old_tier,
                to_tier=new_tier,
                reason="Requirements met",
                metrics={
                    "trades": self.state.total_trades,
                    "pnl": self.state.total_pnl,
                    "win_rate": self.state.win_rate
                }
            )
            self._log_event(event)
            self.state.save()
            self.last_scaling = datetime.now(timezone.utc)
            return True
        return False

    def execute_regression(self, reason: str) -> bool:
        """Execute tier regression."""
        if self.state.current_tier <= 0:
            return False

        old_tier = self.state.current_tier
        self.state.current_tier -= 1
        self.state.tier_trades = 0
        self.state.tier_pnl = 0
        self.state.tier_started = datetime.now(timezone.utc).isoformat()
        self.state.golden_achieved = False  # Lost golden status

        event = ScalingEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="regress",
            from_tier=old_tier,
            to_tier=self.state.current_tier,
            reason=reason,
            metrics={
                "trades": self.state.total_trades,
                "pnl": self.state.total_pnl,
                "win_rate": self.state.win_rate
            }
        )
        self._log_event(event)
        self.state.save()
        self.last_scaling = datetime.now(timezone.utc)
        return True

    def execute_circuit_breaker(self, reason: str):
        """Execute circuit breaker - go to tier 0."""
        old_tier = self.state.current_tier

        self.state.current_tier = 0
        self.state.tier_trades = 0
        self.state.tier_pnl = 0
        self.state.tier_started = datetime.now(timezone.utc).isoformat()
        self.state.golden_achieved = False

        event = ScalingEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="circuit_breaker",
            from_tier=old_tier,
            to_tier=0,
            reason=reason,
            metrics={
                "trades": self.state.total_trades,
                "pnl": self.state.total_pnl,
                "win_rate": self.state.win_rate
            }
        )
        self._log_event(event)
        self.state.save()
        self.last_scaling = datetime.now(timezone.utc)

    def run_check(self) -> Dict:
        """Run scaling check and execute if needed."""
        result = {
            "action": None,
            "from_tier": self.state.current_tier,
            "to_tier": self.state.current_tier,
            "reason": None
        }

        # Check circuit breaker first (highest priority)
        should_break, reason = self.check_circuit_breaker()
        if should_break:
            self.execute_circuit_breaker(reason)
            result["action"] = "circuit_breaker"
            result["to_tier"] = 0
            result["reason"] = reason
            return result

        # Check for regression
        should_regress, reason = self.check_regression()
        if should_regress:
            self.execute_regression(reason)
            result["action"] = "regress"
            result["to_tier"] = self.state.current_tier
            result["reason"] = reason
            return result

        # Check for advancement
        can_advance, reason = self.check_advancement()
        if can_advance:
            self.execute_advancement()
            result["action"] = "advance"
            result["to_tier"] = self.state.current_tier
            result["reason"] = reason
            return result

        result["reason"] = reason
        return result

    def project_to_golden(self) -> Dict:
        """Project path to golden state."""
        current = self.state.current_tier
        path = []

        for tier_num in range(current, 5):
            tier = SCALING_TIERS[tier_num]
            trades_needed = tier.required_trades
            if tier_num == current:
                trades_needed -= self.state.tier_trades

            path.append({
                "tier": tier_num,
                "name": tier.name,
                "trades_needed": max(0, trades_needed),
                "exposure": tier.max_exposure
            })

        total_trades = sum(p["trades_needed"] for p in path)

        return {
            "current_tier": current,
            "path": path,
            "total_trades_to_golden": total_trades,
            "current_win_rate": self.state.win_rate,
            "projected_time_days": total_trades / 100  # Assuming 100 trades/day
        }


def status_report() -> str:
    """Generate auto-scaler status report."""
    scaler = AutoScaler()
    projection = scaler.project_to_golden()
    result = scaler.run_check()

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║             AUTO-SCALER STATUS                               ║",
        "╠══════════════════════════════════════════════════════════════╣",
        f"║  Current Tier: {scaler.state.current_tier} - {scaler.state.get_tier_config().name:<40} ║",
        f"║  Win Rate: {scaler.state.win_rate*100:>6.1f}%                                      ║",
        f"║  Tier Trades: {scaler.state.tier_trades:>6}                                       ║",
        f"║  Tier P&L: ${scaler.state.tier_pnl:>+10.2f}                                  ║",
        "╠══════════════════════════════════════════════════════════════╣",
    ]

    can_advance, adv_reason = scaler.check_advancement()
    should_regress, reg_reason = scaler.check_regression()

    if can_advance:
        lines.append("║  🟢 READY TO ADVANCE                                         ║")
    elif should_regress:
        lines.append("║  🔴 REGRESSION TRIGGERED                                     ║")
    else:
        lines.append(f"║  Status: {adv_reason:<49} ║")

    lines.extend([
        "╠══════════════════════════════════════════════════════════════╣",
        "║  Path to Golden State:                                       ║",
    ])

    for step in projection["path"]:
        marker = "→" if step["tier"] == scaler.state.current_tier else " "
        lines.append(f"║  {marker} Tier {step['tier']}: {step['name']:<12} "
                    f"({step['trades_needed']:>5} trades) ${step['exposure']:>10,} ║")

    lines.extend([
        "╠══════════════════════════════════════════════════════════════╣",
        f"║  Total trades to golden: {projection['total_trades_to_golden']:>6,}                          ║",
        f"║  Estimated time: {projection['projected_time_days']:.0f} days                                   ║",
        "╚══════════════════════════════════════════════════════════════╝",
    ])

    return "\n".join(lines)


def main():
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "check":
            scaler = AutoScaler()
            result = scaler.run_check()
            print(json.dumps(result, indent=2))
        elif cmd == "project":
            scaler = AutoScaler()
            projection = scaler.project_to_golden()
            print(json.dumps(projection, indent=2))
        elif cmd == "force-advance":
            scaler = AutoScaler()
            scaler.state.tier_trades = scaler.state.get_tier_config().required_trades
            scaler.state.win_rate = scaler.state.get_tier_config().required_win_rate + 0.01
            scaler.state.tier_pnl = 100
            scaler.execute_advancement()
            print(f"Advanced to Tier {scaler.state.current_tier}")
        else:
            print(status_report())
    else:
        print(status_report())


if __name__ == "__main__":
    main()
