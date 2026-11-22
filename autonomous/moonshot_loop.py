#!/usr/bin/env python3
"""
MOONSHOT RECURSIVE LOOP - Escape Velocity Engine
=================================================

Self-prompting Claude CLI loop that continuously improves the system
toward escape velocity (self-sustaining autonomous income).

Each cycle:
1. Evaluates current state
2. Identifies highest-impact improvement
3. Executes improvement
4. Measures progress
5. Triggers next cycle with compounding context

Exponential by design: each improvement enables more improvements.
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import time

# UNIFIED AI - All systems serve Yair Siegel
sys.path.insert(0, str(Path(__file__).parent.parent))
from ai.unified_ai import announce_agent, get_master, log_action, MASTER

BASE_DIR = Path(__file__).resolve().parent.parent
MOONSHOT_STATE = BASE_DIR / "state" / "moonshot_state.json"
MOONSHOT_LOG = BASE_DIR / "state" / "logs" / "moonshot.log"
MAX_CYCLES_PER_DAY = 12  # Rate limit
CYCLE_COOLDOWN_MINUTES = 30  # Minimum time between cycles


def load_state() -> dict:
    if MOONSHOT_STATE.exists():
        return json.load(open(MOONSHOT_STATE))
    return {
        "total_cycles": 0,
        "cycles_today": 0,
        "last_cycle": None,
        "last_cycle_date": None,
        "escape_velocity_score": 0.0,
        "improvements_made": [],
        "current_focus": "capital_recovery",
        "milestones": {
            "first_dollar": False,
            "trading_enabled": False,
            "positive_pnl": False,
            "daily_profit": False,
            "escape_velocity": False
        },
        "momentum": []
    }


def save_state(state: dict):
    MOONSHOT_STATE.parent.mkdir(parents=True, exist_ok=True)
    with open(MOONSHOT_STATE, 'w') as f:
        json.dump(state, f, indent=2, default=str)


def log(msg: str):
    MOONSHOT_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(MOONSHOT_LOG, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[MOONSHOT] {msg}")


def send_telegram(message: str):
    """Send notifications only with explicitly configured credentials."""
    import requests
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception:
        return False


def get_system_metrics() -> dict:
    """Collect operational metrics without promoting stale caches into financial truth."""
    metrics = {
        "balance": None,
        "balance_verified": False,
        "position_value": None,
        "trading_enabled": False,
        "monitors_active": 0,
        "income_channels": 0,
        "last_improvement": None,
        "monthly_burn": None,
        "ai_spend": None,
        "runway_days": None,
        "total_resources": None,
        "cost_cut_opportunities": [],
        "roi_status": "unverified",
        "financial_truth_status": "unknown",
    }

    try:
        from executor.trading_safeguards import TradingSafeguards
        ok, message = TradingSafeguards().check_wallet_balance(0)
        if ok and "balance: $" in message:
            metrics["balance"] = float(message.split("balance: $", 1)[1].split()[0])
            metrics["balance_verified"] = True
            metrics["financial_truth_status"] = "verified_wallet_only"
    except Exception:
        pass

    # Trading remains disabled until a separate governed execution grant exists.
    metrics["trading_enabled"] = False

    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        metrics["monitors_active"] = result.stdout.count("*/") + result.stdout.count("0 ")
    except Exception:
        pass

    # Web applications and model signals are not evidence of earned income.
    metrics["income_channels"] = 0
    return metrics


def calculate_escape_velocity_score(metrics: dict, state: dict) -> float:
    """
    Calculate progress toward escape velocity (0-100).

    Escape velocity = system generates more value than it consumes

    Components:
    - Capital availability (can trade)
    - Active income channels
    - Automation coverage
    - Historical momentum
    """
    score = 0.0

    # Capital score is awarded only from a fresh verified wallet balance.
    balance = metrics.get("balance")
    if metrics.get("balance_verified") and isinstance(balance, (int, float)) and balance >= 0:
        if balance >= 200:
            score += 30
        elif balance >= 50:
            score += 20
        elif balance >= 10:
            score += 10
        else:
            score += balance

    # Trading capability (0-20 points)
    if metrics["trading_enabled"]:
        score += 20

    # Automation score (0-20 points)
    score += min(20, metrics["monitors_active"] * 2.5)

    # Income channels (0-15 points)
    score += min(15, metrics["income_channels"] * 7.5)

    # Momentum bonus (0-15 points) - based on recent improvements
    recent_improvements = len([m for m in state.get("momentum", [])[-10:]])
    score += min(15, recent_improvements * 1.5)

    return min(100, score)


def build_claude_prompt(state: dict, metrics: dict) -> str:
    """Build a self-improvement prompt with explicit unknown financial fields."""
    cost_cuts = ", ".join(metrics.get("cost_cut_opportunities", [])) or "None verified"
    balance = metrics.get("balance")
    balance_label = "$" + format(balance, ".2f") if metrics.get("balance_verified") and isinstance(balance, (int, float)) else "UNKNOWN"
    monthly_burn = metrics.get("monthly_burn")
    burn_label = "$" + format(monthly_burn, ".2f") if isinstance(monthly_burn, (int, float)) else "UNKNOWN"
    ai_spend = metrics.get("ai_spend")
    ai_label = "$" + format(ai_spend, ".2f") if isinstance(ai_spend, (int, float)) else "UNKNOWN"
    runway = metrics.get("runway_days")
    runway_label = format(runway, ".0f") + " days" if isinstance(runway, (int, float)) else "UNKNOWN"

    improvement_context = os.environ.get("IMPROVEMENT_CONTEXT", "")
    context_section = f"\nIMPROVEMENT CONTEXT:\n{improvement_context}\n" if improvement_context else ""

    return f"""You are the autonomous engineering and revenue-operations agent.
{context_section}
MISSION: Build sustainable, verified earned income while reducing operating cost and manual effort.

RESOURCE AWARENESS:
- Verified Polymarket wallet balance: {balance_label}
- Verified positions: UNKNOWN
- Monthly burn: {burn_label}
- AI spend: {ai_label}
- Runway: {runway_label}
- ROI status: {metrics.get("roi_status", "unverified")}
- Cost-cut opportunities: {cost_cuts}

SYSTEM STATE:
- Escape velocity score: {state.get("escape_velocity_score", 0):.1f}/100
- Live trading: DISABLED pending governed approval
- Active monitors: {metrics.get("monitors_active", 0)}
- Verified income channels: {metrics.get("income_channels", 0)}

PRIORITIES:
1. Establish verified financial truth and reconciled runway.
2. Find low-cost, customer-funded income opportunities.
3. Reduce recurring spend that has no demonstrated ROI.
4. Improve system reliability and automation coverage.
5. Preserve infrastructure; do not destroy productive assets.

ABSOLUTE PROHIBITION:
- Never infer income from websites, signals, estimates, or model activity.
- Never treat positions or cached balances as spendable cash.
- Never enable trading or move money without governed authorization.
- Never delete infrastructure to cut costs.
"""


def run_claude_cycle(state: dict, metrics: dict) -> dict:
    """Execute one Claude CLI improvement cycle"""

    prompt = build_claude_prompt(state, metrics)

    log(f"Starting cycle {state['total_cycles'] + 1}")
    log(f"Escape velocity score: {state['escape_velocity_score']:.1f}")

    # Write prompt to temp file for Claude CLI
    prompt_file = Path("/tmp/moonshot_prompt.txt")
    prompt_file.write_text(prompt)

    # Run Claude CLI with the prompt
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--allowedTools", "Edit,Write,Read,Bash,Glob,Grep"],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd="/root/hands-off-engine"
        )

        output = result.stdout + result.stderr
        log(f"Cycle completed. Output length: {len(output)}")

        # Check for improvements made
        improvements_file = Path("/root/hands-off-engine/state/moonshot_improvements.jsonl")
        if improvements_file.exists():
            lines = improvements_file.read_text().strip().split('\n')
            if lines:
                try:
                    latest = json.loads(lines[-1])
                    state["improvements_made"].append(latest)
                    state["momentum"].append({
                        "cycle": state["total_cycles"] + 1,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "improvement": latest.get("improvement", "unknown")[:100]
                    })
                    log(f"Improvement recorded: {latest.get('improvement', 'unknown')[:50]}")
                except:
                    pass

        return {"success": True, "output_length": len(output)}

    except subprocess.TimeoutExpired:
        log("Cycle timed out after 10 minutes")
        return {"success": False, "error": "timeout"}
    except Exception as e:
        log(f"Cycle error: {e}")
        return {"success": False, "error": str(e)}


def should_run_cycle(state: dict) -> tuple[bool, str]:
    """Check if we should run another cycle"""

    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    # Reset daily counter if new day
    if state.get("last_cycle_date") != today:
        state["cycles_today"] = 0
        state["last_cycle_date"] = today

    # Check rate limits
    if state["cycles_today"] >= MAX_CYCLES_PER_DAY:
        return False, f"Daily limit reached ({MAX_CYCLES_PER_DAY} cycles)"

    # Check cooldown
    if state.get("last_cycle"):
        last = datetime.fromisoformat(state["last_cycle"].replace("Z", "+00:00"))
        minutes_since = (now - last).total_seconds() / 60
        if minutes_since < CYCLE_COOLDOWN_MINUTES:
            return False, f"Cooldown: {CYCLE_COOLDOWN_MINUTES - minutes_since:.0f}min remaining"

    return True, "Ready"


def trigger_next_cycle():
    """Schedule the next cycle (recursive call)"""
    # Add to cron or use at command for next execution
    next_time = datetime.now(timezone.utc).timestamp() + (CYCLE_COOLDOWN_MINUTES * 60)
    log(f"Next cycle scheduled for {CYCLE_COOLDOWN_MINUTES} minutes from now")

    # Could use 'at' command or just let cron handle it
    # For now, we rely on cron to trigger cycles


def main():
    """Main moonshot loop entry point"""
    announce_agent("moonshot-loop")  # UNIFIED AI

    # Load environment
    env_file = Path("/root/hands-off-engine/.env.polymarket")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"\'')

    state = load_state()

    # Check if we should run
    can_run, reason = should_run_cycle(state)
    if not can_run:
        log(f"Skipping cycle: {reason}")
        return

    # Get current metrics
    metrics = get_system_metrics()

    # Calculate escape velocity score
    state["escape_velocity_score"] = calculate_escape_velocity_score(metrics, state)

    # Update milestones
    if metrics["balance"] > 0:
        state["milestones"]["first_dollar"] = True
    if metrics["trading_enabled"]:
        state["milestones"]["trading_enabled"] = True

    # Run the Claude improvement cycle
    send_telegram(f"🚀 *MOONSHOT CYCLE {state['total_cycles'] + 1}*\n\nEscape Velocity: {state['escape_velocity_score']:.1f}%\nBalance: ${metrics['balance']:.2f}")

    result = run_claude_cycle(state, metrics)

    # Update state
    state["total_cycles"] += 1
    state["cycles_today"] += 1
    state["last_cycle"] = datetime.now(timezone.utc).isoformat()

    # Recalculate score after improvements
    new_metrics = get_system_metrics()
    state["escape_velocity_score"] = calculate_escape_velocity_score(new_metrics, state)

    save_state(state)

    # Check for escape velocity achievement
    if state["escape_velocity_score"] >= 80 and not state["milestones"]["escape_velocity"]:
        state["milestones"]["escape_velocity"] = True
        send_telegram("🎯 *ESCAPE VELOCITY ACHIEVED!*\n\nThe system is now self-sustaining!")
        save_state(state)

    # Log completion
    log(f"Cycle {state['total_cycles']} complete. Score: {state['escape_velocity_score']:.1f}")

    # Trigger recursive continuation
    trigger_next_cycle()


if __name__ == "__main__":
    main()
