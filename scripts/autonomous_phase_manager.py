#!/usr/bin/env python3
"""
Autonomous Phase Manager - Auto-Progression System
====================================================

Automatically evaluates trading performance and progresses through
deployment phases without requiring manual verification.

Phases:
1. baby_mode: $50 max position, 30+ trades, 7 days min
2. scale_up: $200 max position, 50+ trades, 14 days min
3. full_deployment: $1000 max position, unlimited

Transition criteria (all must be met):
- Minimum number of trades
- Minimum time in phase
- Win rate > threshold
- Max drawdown < limit
- No critical errors
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import requests

REPO_ROOT = Path(__file__).parent.parent
CONFIG_DIR = REPO_ROOT / "config"
STATE_DIR = REPO_ROOT / "state"
LOGS_DIR = REPO_ROOT / "logs"

# Phase configuration
PHASES = {
    "baby_mode": {
        "max_position_usd": 50,
        "min_trades": 30,
        "min_days": 7,
        "required_win_rate": 0.52,
        "max_drawdown": 0.05,
        "next_phase": "scale_up"
    },
    "scale_up": {
        "max_position_usd": 200,
        "min_trades": 50,
        "min_days": 14,
        "required_win_rate": 0.53,
        "max_drawdown": 0.08,
        "next_phase": "full_deployment"
    },
    "full_deployment": {
        "max_position_usd": 1000,
        "min_trades": None,  # No limit
        "min_days": None,
        "required_win_rate": 0.50,
        "max_drawdown": 0.15,
        "next_phase": None  # Final phase
    }
}


def load_current_phase() -> Tuple[str, datetime]:
    """Load current phase and when it started."""
    state_file = STATE_DIR / "trading_mode.json"

    if not state_file.exists():
        # Default to baby_mode
        save_phase("baby_mode")
        return "baby_mode", datetime.utcnow()

    with open(state_file) as f:
        state = json.load(f)

    phase = state.get("phase", "baby_mode")
    started = state.get("phase_started")

    if started:
        started = datetime.fromisoformat(started.replace('Z', ''))
    else:
        started = datetime.utcnow()

    return phase, started


def save_phase(phase: str):
    """Save current phase to state file."""
    state_file = STATE_DIR / "trading_mode.json"

    state = {}
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)

    state["phase"] = phase
    state["phase_started"] = datetime.utcnow().isoformat() + "Z"
    state["updated_at"] = datetime.utcnow().isoformat() + "Z"

    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)


def load_performance_metrics() -> Dict:
    """Load trading performance metrics."""
    metrics = {
        "total_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
        "total_pnl": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0
    }

    # Read from trading performance log
    perf_log = LOGS_DIR / "trading_performance.jsonl"

    if not perf_log.exists():
        return metrics

    trades = []
    with open(perf_log) as f:
        for line in f:
            try:
                trade = json.loads(line)
                trades.append(trade)
            except json.JSONDecodeError:
                continue

    if not trades:
        return metrics

    # Calculate metrics
    metrics["total_trades"] = len(trades)

    running_pnl = 0.0
    peak_pnl = 0.0
    max_dd = 0.0

    for trade in trades:
        pnl = trade.get("pnl", 0)
        running_pnl += pnl

        if pnl > 0:
            metrics["winning_trades"] += 1
        elif pnl < 0:
            metrics["losing_trades"] += 1

        # Track drawdown
        if running_pnl > peak_pnl:
            peak_pnl = running_pnl

        current_dd = (peak_pnl - running_pnl) / max(peak_pnl, 1.0) if peak_pnl > 0 else 0
        max_dd = max(max_dd, current_dd)

    metrics["total_pnl"] = running_pnl
    metrics["max_drawdown"] = max_dd
    metrics["win_rate"] = metrics["winning_trades"] / max(metrics["total_trades"], 1)

    return metrics


def check_for_critical_errors() -> bool:
    """Check if any critical errors occurred recently."""
    error_indicators = [
        STATE_DIR / "critical_error.flag",
        STATE_DIR / "trading_paused.flag"
    ]

    for indicator in error_indicators:
        if indicator.exists():
            # Check if recent (last 24 hours)
            mtime = datetime.fromtimestamp(indicator.stat().st_mtime)
            if datetime.now() - mtime < timedelta(hours=24):
                return True

    return False


def evaluate_phase_transition(current_phase: str, phase_started: datetime, metrics: Dict) -> Tuple[bool, str]:
    """
    Evaluate if conditions are met to transition to next phase.

    Returns: (can_transition, reason)
    """
    phase_config = PHASES.get(current_phase)

    if not phase_config:
        return False, f"Unknown phase: {current_phase}"

    next_phase = phase_config["next_phase"]
    if not next_phase:
        return False, "Already at final phase (full_deployment)"

    reasons = []

    # Check minimum trades
    min_trades = phase_config["min_trades"]
    if min_trades and metrics["total_trades"] < min_trades:
        reasons.append(f"Need {min_trades - metrics['total_trades']} more trades")

    # Check minimum time
    min_days = phase_config["min_days"]
    if min_days:
        days_in_phase = (datetime.utcnow() - phase_started).days
        if days_in_phase < min_days:
            reasons.append(f"Need {min_days - days_in_phase} more days in phase")

    # Check win rate
    required_win_rate = phase_config["required_win_rate"]
    if metrics["win_rate"] < required_win_rate:
        reasons.append(f"Win rate {metrics['win_rate']:.1%} < {required_win_rate:.1%} required")

    # Check drawdown
    max_dd = phase_config["max_drawdown"]
    if metrics["max_drawdown"] > max_dd:
        reasons.append(f"Drawdown {metrics['max_drawdown']:.1%} > {max_dd:.1%} limit")

    # Check for critical errors
    if check_for_critical_errors():
        reasons.append("Critical errors detected in last 24h")

    if reasons:
        return False, "; ".join(reasons)

    return True, f"All criteria met for transition to {next_phase}"


def update_hard_limits(phase: str):
    """Update hard limits configuration for the new phase."""
    phase_config = PHASES.get(phase, {})
    max_position = phase_config.get("max_position_usd", 50)

    limits_file = CONFIG_DIR / "hard_limits.json"

    limits = {}
    if limits_file.exists():
        with open(limits_file) as f:
            limits = json.load(f)

    # Update limits based on phase
    limits["max_position_usd"] = max_position
    limits["phase"] = phase
    limits["updated_at"] = datetime.utcnow().isoformat() + "Z"
    limits["updated_by"] = "autonomous_phase_manager"

    with open(limits_file, 'w') as f:
        json.dump(limits, f, indent=2)


def send_notification(message: str, is_milestone: bool = False):
    """Send Telegram notification about phase status."""
    token = os.getenv('TELEGRAM_BOT_TOKEN', '8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '8327766663')

    emoji = "🎉" if is_milestone else "📊"

    try:
        url = f'https://api.telegram.org/bot{token}/sendMessage'
        requests.post(url, json={
            'chat_id': chat_id,
            'text': f"{emoji} <b>Phase Manager</b>\n\n{message}",
            'parse_mode': 'HTML'
        }, timeout=10)
    except Exception as e:
        print(f"Notification error: {e}")


def log_phase_event(event_type: str, details: Dict):
    """Log phase-related events."""
    log_file = LOGS_DIR / "phase_progression.jsonl"

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event_type,
        **details
    }

    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def run_phase_evaluation():
    """Main function: evaluate and potentially progress phase."""
    print("=" * 60)
    print("AUTONOMOUS PHASE MANAGER")
    print(f"Time: {datetime.utcnow().isoformat()}Z")
    print("=" * 60)

    # Load current state
    current_phase, phase_started = load_current_phase()
    metrics = load_performance_metrics()

    print(f"\nCurrent Phase: {current_phase}")
    print(f"Phase Started: {phase_started.isoformat()}Z")
    print(f"Days in Phase: {(datetime.utcnow() - phase_started).days}")
    print(f"\nPerformance Metrics:")
    print(f"  Total Trades: {metrics['total_trades']}")
    print(f"  Win Rate: {metrics['win_rate']:.1%}")
    print(f"  Max Drawdown: {metrics['max_drawdown']:.1%}")
    print(f"  Total P&L: ${metrics['total_pnl']:.2f}")

    # Evaluate transition
    can_transition, reason = evaluate_phase_transition(current_phase, phase_started, metrics)

    print(f"\nTransition Evaluation:")
    print(f"  Can Progress: {'Yes' if can_transition else 'No'}")
    print(f"  Reason: {reason}")

    if can_transition:
        next_phase = PHASES[current_phase]["next_phase"]

        print(f"\n🚀 PROGRESSING TO: {next_phase}")

        # Update phase
        save_phase(next_phase)
        update_hard_limits(next_phase)

        # Log event
        log_phase_event("phase_transition", {
            "from_phase": current_phase,
            "to_phase": next_phase,
            "metrics": metrics,
            "reason": reason
        })

        # Send celebration notification
        message = f'''<b>Phase Progression!</b>

{current_phase} → {next_phase}

<b>Performance:</b>
• {metrics['total_trades']} trades completed
• {metrics['win_rate']:.1%} win rate
• {metrics['max_drawdown']:.1%} max drawdown
• ${metrics['total_pnl']:.2f} total P&L

<b>New Limits:</b>
• Max position: ${PHASES[next_phase]['max_position_usd']}

System automatically upgraded based on performance.'''

        send_notification(message, is_milestone=True)

    else:
        # Log evaluation (for tracking progress)
        log_phase_event("phase_evaluation", {
            "current_phase": current_phase,
            "metrics": metrics,
            "can_transition": False,
            "reason": reason
        })

    print("\n" + "=" * 60)


if __name__ == '__main__':
    run_phase_evaluation()
