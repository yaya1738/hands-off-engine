#!/usr/bin/env python3
"""
Autonomous Recalibration Engine

Analyzes trading performance and automatically adjusts risk parameters.
This is the "self-tuning" component that allows the system to optimize itself.

Run daily via cron to:
- Analyze recent performance metrics
- Adjust risk profile (position size, confidence threshold, etc.)
- Auto-resume trading if conditions improve
- Progress through phases: baby_mode → scale_up → full_deployment
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from executor.trading_safeguards import (
    load_risk_profile,
    save_risk_profile,
    load_mode,
    save_mode,
    maybe_auto_resume,
    enforce_hard_limits,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOG = logging.getLogger(__name__)

PERFORMANCE_LOG = Path(__file__).parent.parent / "logs" / "trading_performance.jsonl"


def load_recent_trades(days: int = 7) -> List[dict]:
    """
    Load trades from the last N days.

    Args:
        days: Number of days to look back

    Returns:
        List of trade entries
    """
    if not PERFORMANCE_LOG.exists():
        LOG.warning("No performance log found")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    trades = []

    try:
        with open(PERFORMANCE_LOG) as f:
            for line in f:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))

                if ts >= cutoff:
                    trades.append(entry)

    except Exception as e:
        LOG.error(f"Failed to load trades: {e}")
        return []

    LOG.info(f"Loaded {len(trades)} trades from last {days} days")
    return trades


def compute_metrics(trades: List[dict]) -> Dict[str, float]:
    """
    Compute performance metrics from trade history.

    Returns:
        Dictionary with:
        - hit_rate: % of winning trades
        - total_pnl: Total profit/loss
        - pnl_per_dollar_risked: Return on capital
        - max_drawdown: Largest peak-to-trough decline
        - avg_trade_size: Average position size
        - trade_count: Number of trades
    """
    if not trades:
        return {
            "hit_rate": 0.0,
            "total_pnl": 0.0,
            "pnl_per_dollar_risked": 0.0,
            "max_drawdown": 0.0,
            "avg_trade_size": 0.0,
            "trade_count": 0,
        }

    # Filter successful trades only
    successful_trades = [t for t in trades if t.get("success", False)]

    if not successful_trades:
        LOG.warning("No successful trades found")
        return {
            "hit_rate": 0.0,
            "total_pnl": 0.0,
            "pnl_per_dollar_risked": 0.0,
            "max_drawdown": 0.0,
            "avg_trade_size": 0.0,
            "trade_count": 0,
        }

    # Hit rate (% winning trades)
    winning_trades = [t for t in successful_trades if t.get("realized_pnl_usd", 0) > 0]
    hit_rate = len(winning_trades) / len(successful_trades) if successful_trades else 0.0

    # Total PnL
    total_pnl = sum(t.get("realized_pnl_usd", 0.0) for t in successful_trades)

    # Capital deployed
    total_capital_deployed = sum(t.get("size_usd", 0.0) for t in successful_trades)

    # PnL per dollar risked
    pnl_per_dollar = total_pnl / total_capital_deployed if total_capital_deployed > 0 else 0.0

    # Max drawdown (simplified - peak to trough)
    cumulative_pnl = 0.0
    peak = 0.0
    max_drawdown = 0.0

    for trade in successful_trades:
        cumulative_pnl += trade.get("realized_pnl_usd", 0.0)
        peak = max(peak, cumulative_pnl)
        drawdown = peak - cumulative_pnl
        max_drawdown = max(max_drawdown, drawdown)

    # Average trade size
    avg_trade_size = total_capital_deployed / len(successful_trades) if successful_trades else 0.0

    metrics = {
        "hit_rate": hit_rate,
        "total_pnl": total_pnl,
        "pnl_per_dollar_risked": pnl_per_dollar,
        "max_drawdown": max_drawdown,
        "avg_trade_size": avg_trade_size,
        "trade_count": len(successful_trades),
    }

    LOG.info(f"Metrics: hit_rate={hit_rate:.1%}, total_pnl=${total_pnl:.2f}, "
             f"pnl_per_$={pnl_per_dollar:.3f}, max_dd=${max_drawdown:.2f}")

    return metrics


def adjust_risk_profile(
    current_profile: dict,
    metrics: Dict[str, float]
) -> Tuple[dict, List[str]]:
    """
    Adjust risk profile based on performance metrics.

    Conservative phase progression rules:
    - Require minimum trades AND minimum days per phase
    - Require low drawdown before upgrading
    - Lock phases for minimum duration
    - Never exceed hard limits

    Rules:
    1. If hit_rate > 55% and total_pnl > 0 and phase criteria met: Scale up
    2. If hit_rate < 45% or total_pnl < -$500: Scale down
    3. If max_drawdown > 50% of max_daily_loss: Scale down
    4. Progress through phases: baby_mode → scale_up → full_deployment

    Args:
        current_profile: Current risk profile
        metrics: Performance metrics

    Returns:
        (updated_profile, changes_made)
    """
    profile = current_profile.copy()
    changes = []

    hit_rate = metrics["hit_rate"]
    total_pnl = metrics["total_pnl"]
    max_dd = metrics["max_drawdown"]
    trade_count = metrics["trade_count"]

    current_phase = profile.get("phase", "baby_mode")
    scale_factor = profile.get("scale_factor", 1.0)

    # Check how long we've been in current phase
    phase_entry_time = profile.get("phase_entry_time")
    if not phase_entry_time:
        # First time - set entry time
        profile["phase_entry_time"] = datetime.now(timezone.utc).isoformat()
        phase_entry_time = profile["phase_entry_time"]

    days_in_phase = (
        datetime.now(timezone.utc) -
        datetime.fromisoformat(phase_entry_time.replace("Z", "+00:00"))
    ).days

    # Conservative phase requirements
    PHASE_REQUIREMENTS = {
        "baby_mode": {
            "min_trades": 30,
            "min_days": 7,
            "min_hit_rate": 0.52,
            "max_drawdown_pct": 0.05,  # 5% of bankroll
        },
        "scale_up": {
            "min_trades": 50,
            "min_days": 14,
            "min_hit_rate": 0.53,
            "max_drawdown_pct": 0.08,  # 8% of bankroll
        },
    }

    # Need minimum trades to make decisions
    if trade_count < 10:
        LOG.info(f"Only {trade_count} trades - waiting for more data before adjusting")
        changes.append(f"insufficient_data_{trade_count}_trades")
        return profile, changes

    # Rule 1: Scale up if performing well AND phase criteria met
    if hit_rate > 0.55 and total_pnl > 0 and trade_count >= 20:
        if current_phase == "baby_mode" and scale_factor < 5.0:
            # Check if we meet requirements for scale_up
            req = PHASE_REQUIREMENTS["baby_mode"]
            can_upgrade = (
                trade_count >= req["min_trades"] and
                days_in_phase >= req["min_days"] and
                hit_rate >= req["min_hit_rate"]
            )

            if can_upgrade:
                # Progress to scale_up phase
                profile["phase"] = "scale_up"
                profile["max_position_usd"] = 250
                profile["max_daily_loss_usd"] = 1000
                profile["scale_factor"] = 2.5
                profile["phase_entry_time"] = datetime.now(timezone.utc).isoformat()
                changes.append(
                    f"phase_upgrade_baby→scale_up "
                    f"({trade_count}trades, {days_in_phase}days, {hit_rate:.1%}hit)"
                )
                LOG.info(
                    f"📈 Upgrading to scale_up phase: "
                    f"{trade_count} trades, {days_in_phase} days, {hit_rate:.1%} hit rate"
                )
            else:
                LOG.info(
                    f"Not ready for scale_up: need {req['min_trades']} trades "
                    f"(have {trade_count}), {req['min_days']} days (have {days_in_phase}), "
                    f"{req['min_hit_rate']:.1%} hit rate (have {hit_rate:.1%})"
                )
                changes.append("phase_locked_insufficient_criteria")

        elif current_phase == "scale_up" and scale_factor < 10.0:
            # Check if we meet requirements for full_deployment
            req = PHASE_REQUIREMENTS["scale_up"]
            can_upgrade = (
                trade_count >= req["min_trades"] and
                days_in_phase >= req["min_days"] and
                hit_rate >= req["min_hit_rate"]
            )

            if can_upgrade:
                # Progress to full_deployment
                profile["phase"] = "full_deployment"
                profile["max_position_usd"] = 1000
                profile["max_daily_loss_usd"] = 3000
                profile["scale_factor"] = 5.0
                profile["phase_entry_time"] = datetime.now(timezone.utc).isoformat()
                changes.append(
                    f"phase_upgrade_scale_up→full_deployment "
                    f"({trade_count}trades, {days_in_phase}days, {hit_rate:.1%}hit)"
                )
                LOG.info(
                    f"📈 Upgrading to full_deployment phase: "
                    f"{trade_count} trades, {days_in_phase} days, {hit_rate:.1%} hit rate"
                )
            else:
                LOG.info(
                    f"Not ready for full_deployment: need {req['min_trades']} trades "
                    f"(have {trade_count}), {req['min_days']} days (have {days_in_phase}), "
                    f"{req['min_hit_rate']:.1%} hit rate (have {hit_rate:.1%})"
                )
                changes.append("phase_locked_insufficient_criteria")

        else:
            # Just scale up within current phase
            new_scale = min(scale_factor * 1.2, 10.0)
            profile["scale_factor"] = round(new_scale, 2)
            changes.append(f"scale_up_{scale_factor}→{profile['scale_factor']}")
            LOG.info(f"📈 Scaling up: {scale_factor} → {profile['scale_factor']}")

    # Rule 2: Scale down if struggling
    elif hit_rate < 0.45 or total_pnl < -500:
        if current_phase == "full_deployment":
            # Downgrade to scale_up
            profile["phase"] = "scale_up"
            profile["max_position_usd"] = 250
            profile["max_daily_loss_usd"] = 1000
            profile["scale_factor"] = 2.5
            changes.append("phase_downgrade_full_deployment→scale_up")
            LOG.warning("📉 Downgrading to scale_up phase")

        elif current_phase == "scale_up":
            # Downgrade to baby_mode
            profile["phase"] = "baby_mode"
            profile["max_position_usd"] = 50
            profile["max_daily_loss_usd"] = 200
            profile["scale_factor"] = 1.0
            changes.append("phase_downgrade_scale_up→baby_mode")
            LOG.warning("📉 Downgrading to baby_mode phase")

        else:
            # Scale down within current phase
            new_scale = max(scale_factor * 0.8, 0.5)
            profile["scale_factor"] = round(new_scale, 2)
            changes.append(f"scale_down_{scale_factor}→{profile['scale_factor']}")
            LOG.warning(f"📉 Scaling down: {scale_factor} → {profile['scale_factor']}")

    # Rule 3: Check drawdown
    max_daily_loss = profile.get("max_daily_loss_usd", 200)
    if max_dd > max_daily_loss * 0.5:
        # Drawdown is too large - scale down
        new_scale = max(scale_factor * 0.7, 0.5)
        profile["scale_factor"] = round(new_scale, 2)
        changes.append(f"drawdown_protection_{scale_factor}→{profile['scale_factor']}")
        LOG.warning(f"⚠️ Large drawdown detected: ${max_dd:.2f} - scaling down")

    # Update calibration history
    if "calibration_history" not in profile:
        profile["calibration_history"] = []

    profile["calibration_history"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "changes": changes,
        "phase": profile["phase"],
        "scale_factor": profile["scale_factor"],
    })

    # Keep only last 30 calibrations
    if len(profile["calibration_history"]) > 30:
        profile["calibration_history"] = profile["calibration_history"][-30:]

    return profile, changes


def maybe_resume_trading(
    profile: dict,
    metrics: Dict[str, float],
    mode: dict
) -> bool:
    """
    Check if conditions are good enough to auto-resume trading.

    Args:
        profile: Current risk profile
        metrics: Performance metrics
        mode: Current trading mode

    Returns:
        True if trading was resumed
    """
    # Only resume if currently paused
    if mode.get("live_trading_enabled", False):
        return False

    # Only resume if auto-paused (not manually paused)
    if not mode.get("auto_paused", False):
        LOG.info("Trading manually paused - not auto-resuming")
        return False

    # Check conditions for resuming
    hit_rate = metrics.get("hit_rate", 0.0)
    total_pnl = metrics.get("total_pnl", 0.0)
    trade_count = metrics.get("trade_count", 0)

    # Need reasonable performance to resume
    can_resume = (
        trade_count >= 10 and
        hit_rate >= 0.50 and
        total_pnl >= 0
    )

    if can_resume:
        maybe_auto_resume(reason="recalibration_conditions_met", notify=True)
        LOG.info("✅ Auto-resuming trading after recalibration")
        return True
    else:
        LOG.info(
            f"Not resuming - hit_rate={hit_rate:.1%}, pnl=${total_pnl:.2f}, "
            f"trades={trade_count} (need hit_rate≥50%, pnl≥$0, trades≥10)"
        )
        return False


def main():
    """Main recalibration routine"""
    LOG.info("=" * 60)
    LOG.info("RECALIBRATION ENGINE STARTING")
    LOG.info("=" * 60)

    # Load current state
    profile = load_risk_profile()
    mode = load_mode()

    LOG.info(f"Current phase: {profile.get('phase')}")
    LOG.info(f"Current scale: {profile.get('scale_factor')}")
    LOG.info(f"Trading enabled: {mode.get('live_trading_enabled')}")

    # Load recent trades
    trades = load_recent_trades(days=7)

    if not trades:
        LOG.warning("No trades to analyze - skipping recalibration")
        return

    # Compute metrics
    metrics = compute_metrics(trades)

    # Adjust risk profile
    new_profile, changes = adjust_risk_profile(profile, metrics)

    # CRITICAL: Enforce hard limits before saving
    # This ensures recalibration can never exceed absolute caps
    new_profile = enforce_hard_limits(new_profile)

    if changes:
        LOG.info(f"Changes made: {', '.join(changes)}")
        save_risk_profile(new_profile)

        # Send notification about changes
        try:
            from notifications.telegram_notifier import send_telegram_message
            send_telegram_message(
                f"🔧 **RECALIBRATION COMPLETE**\n\n"
                f"Phase: {new_profile['phase']}\n"
                f"Scale: {new_profile['scale_factor']}x\n"
                f"Max Position: ${new_profile['max_position_usd']}\n"
                f"Max Daily Loss: ${new_profile['max_daily_loss_usd']}\n\n"
                f"Performance (7d):\n"
                f"• Hit rate: {metrics['hit_rate']:.1%}\n"
                f"• Total PnL: ${metrics['total_pnl']:.2f}\n"
                f"• Trades: {metrics['trade_count']}\n\n"
                f"Changes: {', '.join(changes)}"
            )
        except Exception as e:
            LOG.error(f"Failed to send notification: {e}")
    else:
        LOG.info("No changes needed")

    # Check if we should resume trading
    resumed = maybe_resume_trading(new_profile, metrics, mode)

    if resumed:
        LOG.info("Trading has been auto-resumed")

    LOG.info("=" * 60)
    LOG.info("RECALIBRATION ENGINE COMPLETE")
    LOG.info("=" * 60)


if __name__ == "__main__":
    main()
