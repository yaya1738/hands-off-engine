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

MOONSHOT_STATE = Path("/root/hands-off-engine/state/moonshot_state.json")
MOONSHOT_LOG = Path("/var/log/hands-off/moonshot.log")
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
    """Send notification"""
    import requests
    try:
        requests.post(
            "https://api.telegram.org/bot8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA/sendMessage",
            json={"chat_id": "8327766663", "text": message, "parse_mode": "Markdown"},
            timeout=10
        )
    except:
        pass


def get_system_metrics() -> dict:
    """Gather current system metrics for escape velocity calculation"""
    metrics = {
        "balance": 0.0,
        "position_value": 0.0,
        "trading_enabled": False,
        "monitors_active": 0,
        "income_channels": 0,
        "last_improvement": None
    }

    # Get balance
    try:
        sys.path.insert(0, '/root/hands-off-engine')
        from executor.trading_safeguards import TradingSafeguards
        safeguards = TradingSafeguards()
        ok, msg = safeguards.check_wallet_balance(0)
        if "balance: $" in msg:
            metrics["balance"] = float(msg.split("balance: $")[1].split()[0])
        elif "Insufficient" in msg:
            metrics["balance"] = float(msg.split("$")[1].split()[0])
    except:
        pass

    # Check trading capability
    metrics["trading_enabled"] = metrics["balance"] >= 50.0

    # Count active monitors (from cron)
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        metrics["monitors_active"] = result.stdout.count('*/') + result.stdout.count('0 ')
    except:
        pass

    # Count income channels
    channels = 0
    if Path("/var/www/polymarket/index.html").exists():
        channels += 1
    if Path("/var/www/ainexus/index.html").exists():
        channels += 1
    metrics["income_channels"] = channels

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

    # Capital score (0-30 points)
    if metrics["balance"] >= 200:
        score += 30
    elif metrics["balance"] >= 50:
        score += 20
    elif metrics["balance"] >= 10:
        score += 10
    else:
        score += metrics["balance"]

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
    """Build the self-improvement prompt for Claude CLI"""

    prompt = f"""You are the MOONSHOT ENGINE - an autonomous improvement system.

MISSION: Achieve escape velocity (self-sustaining autonomous income)

CURRENT STATE:
- Escape Velocity Score: {state['escape_velocity_score']:.1f}/100
- Balance: ${metrics['balance']:.2f}
- Trading: {'ENABLED' if metrics['trading_enabled'] else 'DISABLED (need $50+)'}
- Active Monitors: {metrics['monitors_active']}
- Income Channels: {metrics['income_channels']}
- Total Cycles: {state['total_cycles']}
- Recent Improvements: {len(state.get('momentum', [])[-5:])}

MILESTONES:
- First Dollar: {'✓' if state['milestones']['first_dollar'] else '○'}
- Trading Enabled: {'✓' if state['milestones']['trading_enabled'] else '○'}
- Positive PnL: {'✓' if state['milestones']['positive_pnl'] else '○'}
- Daily Profit: {'✓' if state['milestones']['daily_profit'] else '○'}
- Escape Velocity: {'✓' if state['milestones']['escape_velocity'] else '○'}

YOUR TASK:
1. Read state/permanent/SYSTEM_TRUTH.md for full context
2. Identify the SINGLE highest-impact improvement you can make RIGHT NOW
3. Execute that improvement (code changes, new scripts, optimizations)
4. Document what you did in state/moonshot_improvements.jsonl
5. Be aggressive - we need escape velocity

CONSTRAINTS:
- Focus on what generates VALUE (income, trading capability, automation)
- Don't just analyze - EXECUTE improvements
- Each cycle should compound on previous cycles
- Target: Get to $50+ balance to enable trading

CURRENT FOCUS: {state['current_focus']}

After completing your improvement, append to state/moonshot_improvements.jsonl:
{{"timestamp": "...", "cycle": {state['total_cycles'] + 1}, "improvement": "...", "impact": "..."}}

GO. Make one high-impact improvement now.
"""
    return prompt


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
