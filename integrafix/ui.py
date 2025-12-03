#!/usr/bin/env python3
"""
INTEGRAFIX: Unified UI
======================

Beautiful terminal UI for the $5M/month trading system.

Features:
- Live dashboard with all metrics
- Interactive menu navigation
- Real-time updates
- Color-coded status indicators
- One-command access to everything

Run: python3 integrafix/ui.py
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ANSI color codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name == 'posix' else 'cls')


def colored(text: str, color: str) -> str:
    """Add color to text."""
    return f"{color}{text}{Colors.RESET}"


def bold(text: str) -> str:
    """Make text bold."""
    return f"{Colors.BOLD}{text}{Colors.RESET}"


def get_metrics() -> Dict:
    """Get all system metrics."""
    from integrafix.golden_state import GoldenState
    from integrafix.system_hardening import SystemHardening

    # HFT data
    hft_log = PROJECT_ROOT / "logs" / "hft_economics.jsonl"
    total_trades = 0
    total_pnl = 0.0
    wins = 0
    recent = []

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
                        recent.append(pnl)
                except:
                    pass

    win_rate = wins / total_trades if total_trades > 0 else 0
    recent_5 = recent[-5:] if recent else []

    # Golden state
    golden = GoldenState.load()
    tier = golden.get_tier_config()

    # System health
    hardening = SystemHardening()
    health = hardening.check_system_health()

    return {
        "trades": total_trades,
        "pnl": total_pnl,
        "win_rate": win_rate,
        "wins": wins,
        "losses": total_trades - wins,
        "recent": recent_5,
        "tier": golden.current_tier,
        "tier_name": tier.name,
        "tier_trades": golden.tier_trades,
        "tier_required": tier.required_trades,
        "tier_wr_required": tier.required_win_rate,
        "max_exposure": tier.max_exposure,
        "max_position": tier.max_position,
        "projection": golden.monthly_projection(),
        "health_status": health.status,
        "processes_running": health.processes_running,
        "processes_total": health.processes_total,
        "golden_achieved": golden.golden_achieved
    }


def render_header() -> str:
    """Render UI header."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "",
        colored("╔══════════════════════════════════════════════════════════════════════════════╗", Colors.CYAN),
        colored("║", Colors.CYAN) + colored("                        INTEGRAFIX CONTROL CENTER                            ", Colors.BOLD + Colors.WHITE) + colored("║", Colors.CYAN),
        colored("║", Colors.CYAN) + colored(f"                        {now}                               ", Colors.DIM) + colored("║", Colors.CYAN),
        colored("╚══════════════════════════════════════════════════════════════════════════════╝", Colors.CYAN),
    ]
    return "\n".join(lines)


def render_metrics_panel(metrics: Dict) -> str:
    """Render main metrics panel."""
    # Win rate coloring
    wr = metrics["win_rate"]
    if wr >= 0.55:
        wr_color = Colors.GREEN
        wr_icon = "🟢"
    elif wr >= 0.52:
        wr_color = Colors.YELLOW
        wr_icon = "🟡"
    else:
        wr_color = Colors.RED
        wr_icon = "🔴"

    # P&L coloring
    pnl = metrics["pnl"]
    pnl_color = Colors.GREEN if pnl >= 0 else Colors.RED

    # Health coloring
    health = metrics["health_status"]
    if health == "healthy":
        health_color = Colors.GREEN
        health_icon = "🟢"
    elif health == "degraded":
        health_color = Colors.YELLOW
        health_icon = "🟡"
    else:
        health_color = Colors.RED
        health_icon = "🔴"

    lines = [
        "",
        colored("┌─────────────────────────────────────┬─────────────────────────────────────┐", Colors.BLUE),
        colored("│", Colors.BLUE) + bold(" PERFORMANCE                         ") + colored("│", Colors.BLUE) + bold(" SYSTEM STATUS                       ") + colored("│", Colors.BLUE),
        colored("├─────────────────────────────────────┼─────────────────────────────────────┤", Colors.BLUE),
        colored("│", Colors.BLUE) + f"  {wr_icon} Win Rate: " + colored(f"{wr*100:>6.2f}%", wr_color) + "                " + colored("│", Colors.BLUE) + f"  {health_icon} Health: " + colored(f"{health.upper():<20}", health_color) + "       " + colored("│", Colors.BLUE),
        colored("│", Colors.BLUE) + f"  P&L: " + colored(f"${pnl:>+12.2f}", pnl_color) + "                " + colored("│", Colors.BLUE) + f"  Processes: {metrics['processes_running']}/{metrics['processes_total']} running            " + colored("│", Colors.BLUE),
        colored("│", Colors.BLUE) + f"  Trades: {metrics['trades']:>6}                       " + colored("│", Colors.BLUE) + f"  Tier: {metrics['tier']} ({metrics['tier_name']})              " + colored("│", Colors.BLUE),
        colored("│", Colors.BLUE) + f"  W/L: {metrics['wins']}/{metrics['losses']}                            " + colored("│", Colors.BLUE) + f"  Max Exposure: ${metrics['max_exposure']:>10,.0f}        " + colored("│", Colors.BLUE),
        colored("└─────────────────────────────────────┴─────────────────────────────────────┘", Colors.BLUE),
    ]
    return "\n".join(lines)


def render_tier_progress(metrics: Dict) -> str:
    """Render tier progress bar."""
    progress = min(1.0, metrics["tier_trades"] / metrics["tier_required"])
    bar_width = 40
    filled = int(progress * bar_width)
    empty = bar_width - filled

    wr_gap = metrics["tier_wr_required"] - metrics["win_rate"]

    lines = [
        "",
        colored("┌──────────────────────────────────────────────────────────────────────────────┐", Colors.MAGENTA),
        colored("│", Colors.MAGENTA) + bold(" TIER PROGRESS                                                                ") + colored("│", Colors.MAGENTA),
        colored("├──────────────────────────────────────────────────────────────────────────────┤", Colors.MAGENTA),
        colored("│", Colors.MAGENTA) + f"  Tier {metrics['tier']} → Tier {metrics['tier'] + 1}                                                           " + colored("│", Colors.MAGENTA),
        colored("│", Colors.MAGENTA) + "  [" + colored("█" * filled, Colors.GREEN) + colored("░" * empty, Colors.DIM) + f"] {progress*100:.0f}%                        " + colored("│", Colors.MAGENTA),
        colored("│", Colors.MAGENTA) + f"  Trades: {metrics['tier_trades']}/{metrics['tier_required']}                                                          " + colored("│", Colors.MAGENTA),
    ]

    if wr_gap > 0:
        lines.append(colored("│", Colors.MAGENTA) + colored(f"  ⚠ Need WR +{wr_gap*100:.1f}% to advance                                             ", Colors.YELLOW) + colored("│", Colors.MAGENTA))
    else:
        lines.append(colored("│", Colors.MAGENTA) + colored(f"  ✓ Win rate requirement met                                                 ", Colors.GREEN) + colored("│", Colors.MAGENTA))

    lines.append(colored("└──────────────────────────────────────────────────────────────────────────────┘", Colors.MAGENTA))

    return "\n".join(lines)


def render_recent_trades(metrics: Dict) -> str:
    """Render recent trades."""
    lines = [
        "",
        colored("┌──────────────────────────────────────────────────────────────────────────────┐", Colors.YELLOW),
        colored("│", Colors.YELLOW) + bold(" RECENT TRADES                                                                ") + colored("│", Colors.YELLOW),
        colored("├──────────────────────────────────────────────────────────────────────────────┤", Colors.YELLOW),
    ]

    for pnl in metrics["recent"]:
        if pnl > 0:
            icon = colored("✓", Colors.GREEN)
            pnl_str = colored(f"${pnl:>+7.2f}", Colors.GREEN)
        else:
            icon = colored("✗", Colors.RED)
            pnl_str = colored(f"${pnl:>+7.2f}", Colors.RED)

        lines.append(colored("│", Colors.YELLOW) + f"  {icon} {pnl_str}                                                                " + colored("│", Colors.YELLOW))

    if not metrics["recent"]:
        lines.append(colored("│", Colors.YELLOW) + "  No recent trades                                                           " + colored("│", Colors.YELLOW))

    lines.append(colored("└──────────────────────────────────────────────────────────────────────────────┘", Colors.YELLOW))

    return "\n".join(lines)


def render_target_gap(metrics: Dict) -> str:
    """Render target gap."""
    target = 5_000_000
    current = metrics["projection"]
    gap = target - current
    achieved = (current / target) * 100 if target > 0 else 0

    lines = [
        "",
        colored("┌──────────────────────────────────────────────────────────────────────────────┐", Colors.GREEN),
        colored("│", Colors.GREEN) + bold(" TARGET: $5,000,000/month                                                     ") + colored("│", Colors.GREEN),
        colored("├──────────────────────────────────────────────────────────────────────────────┤", Colors.GREEN),
        colored("│", Colors.GREEN) + f"  Current Projection: ${current:>14,.0f}/month                                " + colored("│", Colors.GREEN),
        colored("│", Colors.GREEN) + f"  Gap: ${gap:>+18,.0f}                                            " + colored("│", Colors.GREEN),
        colored("│", Colors.GREEN) + f"  Achieved: {achieved:>6.4f}%                                                      " + colored("│", Colors.GREEN),
        colored("└──────────────────────────────────────────────────────────────────────────────┘", Colors.GREEN),
    ]

    return "\n".join(lines)


def render_menu() -> str:
    """Render command menu."""
    lines = [
        "",
        colored("┌──────────────────────────────────────────────────────────────────────────────┐", Colors.WHITE),
        colored("│", Colors.WHITE) + bold(" COMMANDS                                                                     ") + colored("│", Colors.WHITE),
        colored("├──────────────────────────────────────────────────────────────────────────────┤", Colors.WHITE),
        colored("│", Colors.WHITE) + f"  [{colored('1', Colors.CYAN)}] Dashboard    [{colored('2', Colors.CYAN)}] Golden State    [{colored('3', Colors.CYAN)}] Analytics    [{colored('4', Colors.CYAN)}] Health      " + colored("│", Colors.WHITE),
        colored("│", Colors.WHITE) + f"  [{colored('5', Colors.CYAN)}] Booster      [{colored('6', Colors.CYAN)}] Scanner         [{colored('7', Colors.CYAN)}] Sync         [{colored('8', Colors.CYAN)}] Monitor     " + colored("│", Colors.WHITE),
        colored("│", Colors.WHITE) + f"  [{colored('r', Colors.CYAN)}] Refresh      [{colored('q', Colors.CYAN)}] Quit                                                " + colored("│", Colors.WHITE),
        colored("└──────────────────────────────────────────────────────────────────────────────┘", Colors.WHITE),
    ]
    return "\n".join(lines)


def render_full_ui() -> str:
    """Render complete UI."""
    metrics = get_metrics()

    parts = [
        render_header(),
        render_metrics_panel(metrics),
        render_tier_progress(metrics),
        render_recent_trades(metrics),
        render_target_gap(metrics),
        render_menu(),
    ]

    return "\n".join(parts)


def handle_command(cmd: str) -> Optional[str]:
    """Handle menu command."""
    if cmd == "1":
        from integrafix.live_dashboard import render_dashboard
        return render_dashboard()
    elif cmd == "2":
        from integrafix.golden_state import status_report
        return status_report()
    elif cmd == "3":
        from integrafix.performance_analytics import status_report
        return status_report()
    elif cmd == "4":
        from integrafix.system_hardening import status_report
        return status_report()
    elif cmd == "5":
        from integrafix.win_rate_booster import status_report
        return status_report()
    elif cmd == "6":
        from integrafix.smart_scanner import status_report
        return status_report()
    elif cmd == "7":
        from integrafix.state_sync import sync_golden_state
        result = sync_golden_state()
        return f"Synced: {result['old_state']['trades']} → {result['new_state']['trades']} trades\n" + \
               f"WR: {result['old_state']['win_rate']*100:.1f}% → {result['new_state']['win_rate']*100:.1f}%"
    elif cmd == "8":
        from integrafix.realtime_monitor import render_monitor
        return render_monitor()
    return None


def interactive_mode():
    """Run interactive UI mode."""
    while True:
        clear_screen()
        print(render_full_ui())

        try:
            cmd = input(f"\n{colored('>', Colors.CYAN)} ").strip().lower()

            if cmd == "q":
                print(colored("\nGoodbye! System continues running autonomously.", Colors.GREEN))
                break
            elif cmd == "r":
                continue
            elif cmd in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                clear_screen()
                output = handle_command(cmd)
                if output:
                    print(output)
                input(f"\n{colored('Press Enter to continue...', Colors.DIM)}")
            else:
                continue

        except KeyboardInterrupt:
            print(colored("\n\nGoodbye! System continues running autonomously.", Colors.GREEN))
            break
        except EOFError:
            break


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "dashboard":
            print(render_full_ui())
        elif cmd in ["1", "2", "3", "4", "5", "6", "7", "8"]:
            output = handle_command(cmd)
            if output:
                print(output)
        else:
            print(render_full_ui())
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
