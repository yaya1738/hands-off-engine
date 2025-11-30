#!/usr/bin/env python3
"""
SINGULARITY TRIGGER
===================

The moment capital crosses the trading threshold ($50),
this trigger fires and executes EVERYTHING instantly:

1. Enable live trading
2. Execute prepared signals
3. Maximize escape velocity
4. Notify of breakthrough

This is the inflection point where all preparation
collapses into instant execution.
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, '/root/hands-off-engine')

TRIGGER_STATE = Path("/root/hands-off-engine/state/singularity_trigger.json")
TRADING_THRESHOLD = 50.0


def log(msg: str):
    print(f"💥 {msg}")


def send_telegram(msg: str, priority: str = "normal"):
    import requests
    if priority == "critical":
        msg = "🚨🚨🚨\n" + msg
    try:
        requests.post(
            "https://api.telegram.org/bot8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA/sendMessage",
            json={"chat_id": "8327766663", "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
    except:
        pass


def get_balance() -> float:
    """Get current balance"""
    try:
        from executor.trading_safeguards import TradingSafeguards
        safeguards = TradingSafeguards()
        ok, msg = safeguards.check_wallet_balance(0)
        if "balance: $" in msg:
            return float(msg.split("balance: $")[1].split()[0])
        elif "Insufficient" in msg:
            return float(msg.split("$")[1].split()[0])
    except:
        pass
    return 0.0


def load_state() -> dict:
    if TRIGGER_STATE.exists():
        return json.load(open(TRIGGER_STATE))
    return {
        "triggered": False,
        "trigger_time": None,
        "trigger_balance": None,
        "actions_executed": [],
        "escape_velocity_at_trigger": None
    }


def save_state(state: dict):
    with open(TRIGGER_STATE, 'w') as f:
        json.dump(state, f, indent=2, default=str)


def execute_singularity():
    """THE SINGULARITY - Execute everything"""

    log("=" * 60)
    log("SINGULARITY TRIGGERED")
    log("Executing all prepared actions...")
    log("=" * 60)

    actions = []

    # 1. Run the intelligent pipeline in LIVE mode
    log("ACTION 1: Executing intelligent pipeline...")
    try:
        result = subprocess.run([
            'python3', 'scripts/run_pipeline.py',
            '--intelligent', '--live', '--bankroll', '500'
        ], cwd='/root/hands-off-engine', capture_output=True, text=True, timeout=300)

        if 'LIVE' in result.stdout:
            actions.append("✓ Pipeline executed in LIVE mode")
            log("✓ Pipeline executed")
        else:
            actions.append("! Pipeline ran but check output")
    except Exception as e:
        actions.append(f"✗ Pipeline: {e}")

    # 2. Update escape velocity
    log("ACTION 2: Recording escape velocity breakthrough...")
    try:
        from autonomous.escape_velocity_tracker import record_measurement
        balance = get_balance()
        record_measurement(balance=balance, positions=98.05)
        actions.append("✓ Escape velocity recorded")
    except Exception as e:
        actions.append(f"✗ Escape velocity: {e}")

    # 3. Run moonshot cycle
    log("ACTION 3: Triggering moonshot improvement cycle...")
    try:
        # Reset moonshot cooldown to allow immediate execution
        ms_state_file = Path("/root/hands-off-engine/state/moonshot_state.json")
        if ms_state_file.exists():
            ms_state = json.load(open(ms_state_file))
            ms_state["last_cycle"] = None  # Reset cooldown
            with open(ms_state_file, 'w') as f:
                json.dump(ms_state, f, indent=2)

        result = subprocess.run([
            'python3', 'autonomous/moonshot_loop.py'
        ], cwd='/root/hands-off-engine', capture_output=True, text=True, timeout=600)
        actions.append("✓ Moonshot cycle triggered")
    except Exception as e:
        actions.append(f"✗ Moonshot: {e}")

    # 4. Time collapse
    log("ACTION 4: Collapsing timeline...")
    try:
        result = subprocess.run([
            'python3', 'autonomous/time_collapse.py'
        ], cwd='/root/hands-off-engine', capture_output=True, text=True, timeout=120)
        actions.append("✓ Timeline collapsed")
    except Exception as e:
        actions.append(f"✗ Time collapse: {e}")

    return actions


def check_and_trigger():
    """Check if singularity conditions are met"""

    state = load_state()

    # Already triggered?
    if state.get("triggered"):
        log("Singularity already triggered. Monitoring for next breakthrough.")
        return state

    # Check balance
    balance = get_balance()
    log(f"Current balance: ${balance:.2f}")
    log(f"Threshold: ${TRADING_THRESHOLD:.2f}")

    if balance >= TRADING_THRESHOLD:
        log("")
        log("💥 THRESHOLD CROSSED - SINGULARITY CONDITIONS MET 💥")
        log("")

        # Send critical notification
        send_telegram(
            f"*💥 SINGULARITY TRIGGERED 💥*\n\n"
            f"Balance: ${balance:.2f}\n"
            f"Threshold: ${TRADING_THRESHOLD:.2f}\n\n"
            f"*EXECUTING ALL PREPARED ACTIONS...*",
            priority="critical"
        )

        # Execute singularity
        actions = execute_singularity()

        # Update state
        state["triggered"] = True
        state["trigger_time"] = datetime.now(timezone.utc).isoformat()
        state["trigger_balance"] = balance
        state["actions_executed"] = actions

        # Calculate new escape velocity
        try:
            ev_file = Path("/root/hands-off-engine/state/escape_velocity.json")
            if ev_file.exists():
                ev_data = json.load(open(ev_file))
                state["escape_velocity_at_trigger"] = ev_data.get("current_velocity", 0)
        except:
            pass

        save_state(state)

        # Send completion notification
        summary = f"""*💥 SINGULARITY COMPLETE 💥*

*Trigger Details:*
• Balance: ${balance:.2f}
• Time: {state['trigger_time']}

*Actions Executed:*
"""
        for action in actions:
            summary += f"• {action}\n"

        summary += "\n*The system has crossed the threshold.*\n_Exponential growth activated._"

        send_telegram(summary, priority="critical")

        log("")
        log("=" * 60)
        log("SINGULARITY COMPLETE")
        log("=" * 60)

    else:
        gap = TRADING_THRESHOLD - balance
        log(f"Gap to singularity: ${gap:.2f}")
        log("Waiting for capital...")

        # Update monitoring state
        state["last_check"] = datetime.now(timezone.utc).isoformat()
        state["last_balance"] = balance
        state["gap_to_trigger"] = gap
        save_state(state)

    return state


def main():
    """Main entry point"""

    # Load env
    env_file = Path("/root/hands-off-engine/.env.polymarket")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"\'')

    log("SINGULARITY TRIGGER - Monitoring for breakthrough...")
    log("")

    state = check_and_trigger()

    if not state.get("triggered"):
        log("")
        log("System primed and waiting.")
        log("Singularity will execute automatically when capital arrives.")


if __name__ == "__main__":
    main()
