#!/usr/bin/env python3
"""
AI System Monitor Runner - Continuous monitoring of AI agents and AI Nexus

This script provides ongoing monitoring of the full AI system:
- All AI agents (Copilot, ChatGPT, Claude, etc.)
- AI Nexus task and cost tracking
- Coordination system health
- Business-aligned metrics

Integrates with business logic for intelligent alerting.

Usage:
    python scripts/ai_system_monitor.py                # Run once
    python scripts/ai_system_monitor.py --continuous   # Run continuously
    python scripts/ai_system_monitor.py --json         # Output JSON only
"""

import argparse
import json
import sys
import time
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ai_nexus.system_monitor import (
    AISystemMonitor,
    SystemHealthReport,
    HealthStatus
)

# Configuration
DEFAULT_INTERVAL = 300  # 5 minutes
LOG_FILE = REPO_ROOT / "logs" / "ai_system_monitor.log"
STATE_FILE = REPO_ROOT / "state" / "ai_system_monitor_state.json"


def setup_logging():
    """Setup logging for the monitor"""
    import logging
    
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def send_telegram_alert(message: str, severity: str = "info"):
    """
    Send alert via Telegram for critical issues.
    
    Args:
        message: Alert message
        severity: Alert severity (info, warning, critical)
    """
    try:
        import requests
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not bot_token or not chat_id:
            return False
        
        # Format message with severity emoji
        severity_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨"
        }
        emoji = severity_emoji.get(severity, "ℹ️")
        
        formatted_message = f"{emoji} **AI System Monitor**\n\n{message}"
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": formatted_message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        return True
        
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")
        return False


def load_monitor_state() -> dict:
    """Load monitor state from disk"""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "runs": 0,
        "alerts_sent": 0,
        "last_status": None,
        "consecutive_warnings": 0
    }


def save_monitor_state(state: dict):
    """Save monitor state to disk"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def should_alert(
    report: SystemHealthReport,
    state: dict,
    always_alert_critical: bool = True
) -> tuple[bool, str]:
    """
    Determine if we should send an alert based on business logic.
    
    Business rules:
    - Always alert on CRITICAL status
    - Alert on WARNING only after 2 consecutive warnings (avoid noise)
    - Never alert more than once per hour for same issue
    - Alert on transition from healthy to any issue
    
    Returns:
        Tuple of (should_alert, alert_message)
    """
    current_status = report.overall_status.value
    last_status = state.get("last_status")
    consecutive_warnings = state.get("consecutive_warnings", 0)
    
    # Critical always alerts
    if report.overall_status == HealthStatus.CRITICAL and always_alert_critical:
        return True, f"CRITICAL: System requires attention\n\nWarnings:\n" + \
            "\n".join(f"• {w}" for w in report.warnings[:5])
    
    # Transition from healthy to any issue
    if last_status == "healthy" and current_status != "healthy":
        return True, f"Status changed: {last_status} → {current_status}\n\nWarnings:\n" + \
            "\n".join(f"• {w}" for w in report.warnings[:3])
    
    # Warning - only after consecutive occurrences to reduce noise
    if current_status == "warning" and consecutive_warnings >= 2:
        return True, f"Persistent warning (check #{consecutive_warnings})\n\n" + \
            "\n".join(f"• {w}" for w in report.warnings[:3])
    
    return False, ""


def run_once(
    monitor: AISystemMonitor,
    output_json: bool = False,
    state: Optional[dict] = None
) -> SystemHealthReport:
    """
    Run single monitoring check.
    
    Args:
        monitor: AISystemMonitor instance
        output_json: If True, output only JSON
        state: Monitor state for alerting logic
        
    Returns:
        SystemHealthReport
    """
    report = monitor.generate_health_report()
    
    if output_json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(monitor.get_summary_text(report))
    
    # Save report to state directory
    monitor.save_report(report)
    
    # Check if we should alert
    if state is not None:
        should_send, alert_msg = should_alert(report, state)
        if should_send:
            severity = "critical" if report.overall_status == HealthStatus.CRITICAL else "warning"
            send_telegram_alert(alert_msg, severity)
            state["alerts_sent"] = state.get("alerts_sent", 0) + 1
        
        # Update state
        if report.overall_status == HealthStatus.WARNING:
            state["consecutive_warnings"] = state.get("consecutive_warnings", 0) + 1
        else:
            state["consecutive_warnings"] = 0
        
        state["last_status"] = report.overall_status.value
        state["runs"] = state.get("runs", 0) + 1
        state["last_run"] = datetime.now(timezone.utc).isoformat()
    
    return report


def run_continuous(
    monitor: AISystemMonitor,
    interval: int,
    output_json: bool = False
):
    """
    Run continuous monitoring loop.
    
    Args:
        monitor: AISystemMonitor instance
        interval: Seconds between checks
        output_json: If True, output only JSON
    """
    logger = setup_logging()
    logger.info(f"Starting continuous AI system monitoring (interval: {interval}s)")
    
    state = load_monitor_state()
    check_count = 0
    
    try:
        while True:
            check_count += 1
            
            if not output_json:
                print(f"\n{'='*60}")
                print(f"  CHECK #{check_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*60}\n")
            
            try:
                report = run_once(monitor, output_json, state)
                save_monitor_state(state)
                
                # Log summary
                logger.info(
                    f"Check #{check_count}: {report.overall_status.value} | "
                    f"Agents: {len(report.agents)} | "
                    f"Warnings: {len(report.warnings)} | "
                    f"Cost 24h: ${report.business_metrics.get('ai_cost_24h', 0):.2f}"
                )
                
            except Exception as e:
                logger.error(f"Error during check #{check_count}: {e}")
                import traceback
                traceback.print_exc()
            
            if not output_json:
                print(f"\nNext check in {interval} seconds... (Ctrl+C to stop)")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info(f"Monitor stopped after {check_count} checks")
        save_monitor_state(state)
        print(f"\n\nMonitoring stopped. Total checks: {check_count}")


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(
        description="AI System Monitor - Unified AI monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously (default: run once)"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
        help=f"Check interval in seconds (default: {DEFAULT_INTERVAL})"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON only (no text formatting)"
    )
    
    parser.add_argument(
        "--repo-root",
        type=str,
        default=str(REPO_ROOT),
        help="Repository root path"
    )
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = AISystemMonitor(repo_root=args.repo_root)
    
    if args.continuous:
        run_continuous(monitor, args.interval, args.json)
    else:
        state = load_monitor_state()
        run_once(monitor, args.json, state)
        save_monitor_state(state)


if __name__ == "__main__":
    main()
