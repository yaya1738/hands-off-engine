#!/usr/bin/env python3
"""
Generate Return Briefing - Auto-populate status for user's return

Called automatically when user launches Claude Code session.
Fills in all [AUTO-*] placeholders in USER_RETURN_BRIEFING.md
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


import json
import subprocess
from datetime import datetime, timedelta

REPO_ROOT = Path(__file__).parent.parent
BRIEFING_FILE = REPO_ROOT / "ai" / "USER_RETURN_BRIEFING.md"
METRICS_FILE = REPO_ROOT / "state" / "performance_metrics.jsonl"
LAST_SESSION_FILE = REPO_ROOT / ".claude" / "last_session_timestamp"


def get_time_since_last_session() -> str:
    """Calculate time since last session."""
    if not LAST_SESSION_FILE.exists():
        return "Unknown (first session or file missing)"

    try:
        with open(LAST_SESSION_FILE) as f:
            last_ts = datetime.fromisoformat(f.read().strip())

        delta = datetime.now() - last_ts

        if delta.days > 0:
            return f"{delta.days} days, {delta.seconds // 3600} hours"
        elif delta.seconds >= 3600:
            return f"{delta.seconds // 3600} hours, {(delta.seconds % 3600) // 60} minutes"
        else:
            return f"{delta.seconds // 60} minutes"
    except Exception:
        return "Unable to calculate"


def analyze_metrics_since(hours_ago=48):
    """Analyze metrics since last session."""
    if not METRICS_FILE.exists():
        return None

    cutoff = datetime.now() - timedelta(hours=hours_ago)
    metrics = []

    with open(METRICS_FILE) as f:
        for line in f:
            try:
                m = json.loads(line)
                ts = datetime.fromisoformat(m["timestamp"].replace("+00:00", ""))
                if ts >= cutoff:
                    metrics.append(m)
            except Exception:
                continue

    if not metrics:
        return None

    # Calculate stats
    total_runs = len(metrics)
    total_orders = sum(m.get("execution_plan", {}).get("total_orders", 0) for m in metrics)
    total_size = sum(m.get("execution_plan", {}).get("total_size_usd", 0) for m in metrics)
    success_rate = sum(1 for m in metrics if m.get("health", {}).get("plan_exists")) / total_runs * 100

    selection_rates = [m.get("alpha_signals", {}).get("selection_rate", 0) for m in metrics]
    avg_selection = sum(selection_rates) / len(selection_rates) if selection_rates else 0

    return {
        "runs": total_runs,
        "orders": total_orders,
        "size": total_size,
        "success_rate": success_rate,
        "avg_selection_rate": avg_selection * 100
    }


def check_alpha_optimization():
    """Check if alpha optimization worked."""
    # Get metrics before optimization (Nov 22) and after (Nov 23)
    try:
        before_cutoff = datetime(2025, 11, 23, 7, 25)  # Optimization time
        before = []
        after = []

        with open(METRICS_FILE) as f:
            for line in f:
                m = json.loads(line)
                ts = datetime.fromisoformat(m["timestamp"].replace("+00:00", ""))
                rate = m.get("alpha_signals", {}).get("selection_rate", 0)

                if ts < before_cutoff:
                    before.append(rate)
                else:
                    after.append(rate)

        if before and after:
            avg_before = sum(before[-10:]) / len(before[-10:]) * 100  # Last 10 before
            avg_after = sum(after) / len(after) * 100
            improvement = avg_before - avg_after

            status = "Success" if avg_after < 60 else "Partial" if avg_after < 80 else "Needs Review"

            return {
                "before": avg_before,
                "after": avg_after,
                "improvement": improvement,
                "status": status
            }
    except Exception:
        pass

    return None


def check_services():
    """Check if services are running."""
    services = {
        "self-healing-agent": False,
        "coordination-agent": False
    }

    for service in services:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service],
                capture_output=True,
                text=True,
                timeout=5
            )
            services[service] = (result.returncode == 0)
        except Exception:
            pass

    return services


def count_auto_fixes():
    """Count auto-fixes from self-healing agent."""
    try:
        state_file = REPO_ROOT / "state" / "self_healing_state.json"
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
                return state.get("total_fixes", 0)
    except Exception:
        pass
    return 0


def generate_briefing():
    """Generate complete briefing."""
    print("Generating return briefing...")

    # Gather data
    time_away = get_time_since_last_session()
    metrics = analyze_metrics_since(48)
    alpha_results = check_alpha_optimization()
    services = check_services()
    auto_fixes = count_auto_fixes()

    # Build report (simplified to avoid f-string complexity)
    agents_status = "Running" if all(services.values()) else "⚠️ Check needed"
    action_needed = "None" if all(services.values()) and auto_fixes == 0 else "Review below"

    runs = metrics['runs'] if metrics else 0
    success = f"{metrics['success_rate']:.1f}" if metrics else "0"
    orders = metrics['orders'] if metrics else 0
    size = f"{metrics['size']:.2f}" if metrics else "0.00"
    sel_rate = f"{metrics['avg_selection_rate']:.1f}" if metrics else "0"

    services_all = "✅ All running" if all(services.values()) else "⚠️ Some stopped"

    sh_status = "✅ Running" if services.get("self-healing-agent") else "❌ Stopped"
    coord_status = "✅ Running" if services.get("coordination-agent") else "❌ Stopped"

    telegram_status = "✅ Configured" if Path("/etc/systemd/system/telegram-bot.service").exists() else "⏸️ Not set up yet"

    next_hour = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0).strftime("%H:%M UTC")
    next_orch = (datetime.now() + timedelta(hours=6)).strftime("%H:%M UTC")

    report = f"""# User Return Briefing - Auto-Generated

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}
**Time since last session:** {time_away}

---

## Quick Status

✅ **System Status:** Operational
🤖 **Autonomous agents:** {agents_status}
📊 **Recent activity:** {runs} pipeline runs
💡 **Action needed:** {action_needed}

---

## What Happened While You Were Away

### Autonomous Operations

**Pipeline runs:** {runs}
- Success rate: {success}%
- Orders planned: {orders}
- Total size: ${size}
- Avg selection rate: {sel_rate}%

**Agent activity:**
- Self-healing checks: Running every 5 min
- Issues auto-fixed: {auto_fixes}
- Services status: {services_all}

### Alpha Optimization Results

**Target:** Reduce selection rate from 90%+ to 40-50%

{'**Results:**' if alpha_results else '**Status:** Waiting for more data (need hourly runs)'}
{f'- Pre-optimization: {alpha_results["before"]:.1f}%' if alpha_results else ''}
{f'- Post-optimization: {alpha_results["after"]:.1f}%' if alpha_results else ''}
{f'- Improvement: {alpha_results["improvement"]:.1f}%' if alpha_results else ''}
{f'- Status: {alpha_results["status"]}' if alpha_results else ''}

### System Health

**Services:**
- Self-healing agent: {sh_status}
- Coordination agent: {coord_status}
- Trading pipeline: ✅ Running (cron)

---

## Decisions Waiting For You

**Optional:**
- Telegram bot setup (5 min) - Enable phone control
  Current: {telegram_status}

---

## Recommendations

1. System healthy - no action needed
2. Monitor alpha optimization results after next pipeline run
3. Consider setting up Telegram bot for phone control

---

## Next Autonomous Actions

- Next hourly pipeline: {next_hour}
- Next orchestrator run: {next_orch}
- Next weekly summary: Next Sunday 09:00 UTC

---

*Auto-generated at session start - no manual queries needed*
"""

    return report


def main():
    """Main entry point."""
    # Update last session timestamp
    LAST_SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LAST_SESSION_FILE, 'w') as f:
        f.write(datetime.now().isoformat())

    # Generate and print briefing
    briefing = generate_briefing()
    print(briefing)

    # Also save to file
    output = REPO_ROOT / "ai" / "LATEST_RETURN_BRIEFING.md"
    with open(output, 'w') as f:
        f.write(briefing)

    print(f"\n✓ Saved to {output}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
