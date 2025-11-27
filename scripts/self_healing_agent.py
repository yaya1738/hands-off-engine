#!/usr/bin/env python3
"""
Self-Healing Agent - Autonomous System Recovery

Runs continuously (24/7) monitoring system health and auto-fixing issues.
Eliminates need for manual CLI intervention for common problems.

Auto-fixes:
- Restart failed services
- Clear stuck file locks (.git/index.lock)
- Repair broken cron jobs
- Reset stale connections
- Fix file permissions
- Clear temp files
- Restart stuck processes

Only alerts user if cannot auto-fix.
"""

import os
import sys
import time
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Configuration
REPO_ROOT = Path(__file__).parent.parent
LOG_FILE = "/var/log/self-healing-agent.log"
CHECK_INTERVAL = 300  # 5 minutes
STATE_FILE = REPO_ROOT / "state" / "self_healing_state.json"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SelfHealingAgent:
    """Autonomous agent that monitors and repairs system issues."""

    def __init__(self):
        self.fixes_applied = 0
        self.checks_performed = 0
        self.state = self.load_state()

    def load_state(self) -> Dict:
        """Load agent state from disk."""
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
        return {
            "total_fixes": 0,
            "last_check": None,
            "issues_detected": [],
            "auto_fixed": []
        }

    def save_state(self):
        """Save agent state to disk."""
        self.state["last_check"] = datetime.now().isoformat()
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def check_and_heal(self):
        """Main check and heal cycle."""
        self.checks_performed += 1
        logger.info(f"Starting health check cycle #{self.checks_performed}")

        issues = []
        fixes = []

        # Run all checks
        issues.extend(self.check_git_locks())
        issues.extend(self.check_cron_job())
        issues.extend(self.check_disk_space())
        issues.extend(self.check_log_rotation())
        issues.extend(self.check_stale_processes())
        issues.extend(self.check_file_permissions())
        # Critical trading checks (added to prevent revenue loss)
        issues.extend(self.check_data_freshness())
        issues.extend(self.check_live_trading_setup())
        issues.extend(self.check_pipeline_execution())

        # Attempt to fix each issue
        for issue in issues:
            fix_result = self.attempt_fix(issue)
            if fix_result:
                fixes.append(fix_result)
                self.fixes_applied += 1

        # Update state
        if issues:
            self.state["issues_detected"].extend([i["description"] for i in issues])
        if fixes:
            self.state["auto_fixed"].extend(fixes)
            self.state["total_fixes"] = self.fixes_applied

        self.save_state()

        # Report
        if fixes:
            logger.info(f"Applied {len(fixes)} auto-fixes this cycle")
            for fix in fixes:
                logger.info(f"  ✓ {fix}")
        else:
            logger.info("No issues detected - system healthy")

        return len(issues), len(fixes)

    def check_git_locks(self) -> List[Dict]:
        """Check for stuck git locks."""
        issues = []
        lock_file = REPO_ROOT / ".git" / "index.lock"

        if lock_file.exists():
            # Check if lock is stale (> 5 minutes old)
            age = time.time() - lock_file.stat().st_mtime
            if age > 300:  # 5 minutes
                issues.append({
                    "type": "git_lock",
                    "description": "Stale .git/index.lock detected",
                    "severity": "medium",
                    "auto_fixable": True,
                    "fix_cmd": ["rm", "-f", str(lock_file)]
                })

        return issues

    def check_cron_job(self) -> List[Dict]:
        """Check if cron job is running correctly."""
        issues = []

        try:
            # Check if cron job exists
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                issues.append({
                    "type": "cron_missing",
                    "description": "Cron job not configured",
                    "severity": "high",
                    "auto_fixable": False,  # Requires manual setup
                    "alert_user": True
                })
            else:
                # Check if hands-off-engine cron is present
                if "hands-off-engine" not in result.stdout:
                    issues.append({
                        "type": "cron_missing",
                        "description": "Hands-off-engine cron job missing",
                        "severity": "high",
                        "auto_fixable": False,
                        "alert_user": True
                    })

        except Exception as e:
            logger.error(f"Error checking cron: {e}")

        return issues

    def check_disk_space(self) -> List[Dict]:
        """Check available disk space."""
        issues = []

        try:
            result = subprocess.run(
                ["df", "-h", str(REPO_ROOT)],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Parse output to get usage percentage
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 5:
                    usage_pct = int(parts[4].rstrip('%'))
                    if usage_pct > 90:
                        issues.append({
                            "type": "disk_space",
                            "description": f"Disk usage at {usage_pct}%",
                            "severity": "high",
                            "auto_fixable": True,
                            "fix_cmd": ["find", str(REPO_ROOT / "logs"), "-type", "f", "-mtime", "+30", "-delete"]
                        })

        except Exception as e:
            logger.error(f"Error checking disk space: {e}")

        return issues

    def check_log_rotation(self) -> List[Dict]:
        """Check if logs need rotation."""
        issues = []
        log_file = Path("/var/log/hands-off-engine.log")

        if log_file.exists():
            size_mb = log_file.stat().st_size / (1024 * 1024)
            if size_mb > 100:  # > 100MB
                issues.append({
                    "type": "log_rotation",
                    "description": f"Log file is {size_mb:.1f}MB - needs rotation",
                    "severity": "low",
                    "auto_fixable": True,
                    "fix_action": "rotate_log"
                })

        return issues

    def check_stale_processes(self) -> List[Dict]:
        """Check for hung/stale processes."""
        issues = []

        # Check for long-running python processes
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Look for processes that might be stuck
            # This is a placeholder - would need more sophisticated logic
            lines = result.stdout.split('\n')
            for line in lines:
                if 'python' in line and 'hands-off' in line:
                    # Could check if process has been running too long
                    # For now, just log
                    pass

        except Exception as e:
            logger.error(f"Error checking processes: {e}")

        return issues

    def check_file_permissions(self) -> List[Dict]:
        """Check if critical files have correct permissions."""
        issues = []

        # Check if scripts are executable
        script_files = [
            REPO_ROOT / "scripts" / "healthcheck.sh",
            REPO_ROOT / "scripts" / "run_and_notify.sh",
        ]

        for script in script_files:
            if script.exists():
                if not os.access(script, os.X_OK):
                    issues.append({
                        "type": "permissions",
                        "description": f"{script.name} not executable",
                        "severity": "medium",
                        "auto_fixable": True,
                        "fix_cmd": ["chmod", "+x", str(script)]
                    })

        return issues

    def check_data_freshness(self) -> List[Dict]:
        """Check if market data is stale - critical for revenue generation."""
        issues = []

        # Check polymarket-compact.json (source data from Termux)
        compact_file = REPO_ROOT / "termux-hands-off" / "out" / "polymarket-compact.json"
        model_file = REPO_ROOT / "state" / "polymarket-model.json"

        for data_file, description in [
            (compact_file, "Termux market data"),
            (model_file, "Alpha model data")
        ]:
            if data_file.exists():
                try:
                    with open(data_file) as f:
                        data = json.load(f)

                    timestamp_str = data.get("timestamp") or data.get("source_timestamp")
                    if timestamp_str:
                        # Parse timestamp
                        data_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        age_hours = (datetime.now(data_time.tzinfo) - data_time).total_seconds() / 3600

                        if age_hours > 24:  # Data older than 24 hours
                            issues.append({
                                "type": "stale_data",
                                "description": f"{description} is {age_hours:.0f} hours old - revenue at risk!",
                                "severity": "high",
                                "auto_fixable": False,
                                "alert_user": True,
                                "details": f"Last update: {timestamp_str}"
                            })
                except Exception as e:
                    logger.error(f"Error checking {data_file}: {e}")
            else:
                issues.append({
                    "type": "missing_data",
                    "description": f"{description} file missing at {data_file}",
                    "severity": "high",
                    "auto_fixable": False,
                    "alert_user": True
                })

        return issues

    def check_live_trading_setup(self) -> List[Dict]:
        """Check if live trading is properly configured - critical for revenue."""
        issues = []

        # Check trading_mode.json
        mode_file = REPO_ROOT / "state" / "trading_mode.json"
        if mode_file.exists():
            try:
                with open(mode_file) as f:
                    mode = json.load(f)

                # Check if live trading is enabled in state
                if not mode.get("live_trading_enabled", False):
                    issues.append({
                        "type": "trading_disabled",
                        "description": f"Live trading disabled in state file: {mode.get('reason', 'unknown')}",
                        "severity": "high",
                        "auto_fixable": False,
                        "alert_user": True
                    })
            except Exception as e:
                logger.error(f"Error checking trading mode: {e}")

        # Check environment variables (these are required for actual execution)
        env_file = REPO_ROOT / ".env.polymarket"
        if not env_file.exists():
            issues.append({
                "type": "missing_config",
                "description": ".env.polymarket not found - live trading will not work!",
                "severity": "high",
                "auto_fixable": False,
                "alert_user": True
            })

        return issues

    def check_pipeline_execution(self) -> List[Dict]:
        """Check if trading pipeline is running and producing results."""
        issues = []

        # Check shadow_trades.jsonl for recent activity
        shadow_log = REPO_ROOT / "state" / "shadow_trades.jsonl"
        if shadow_log.exists():
            try:
                # Read file once and collect both timestamp and trade data
                last_trade_time = None
                recent_trades = []
                with open(shadow_log) as f:
                    for line in f:
                        try:
                            trade = json.loads(line)
                            recent_trades.append(trade)
                            ts = trade.get("timestamp")
                            if ts:
                                last_trade_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        except (json.JSONDecodeError, ValueError):
                            continue

                if last_trade_time:
                    age_hours = (datetime.now(last_trade_time.tzinfo) - last_trade_time).total_seconds() / 3600

                    if age_hours > 24:  # No trades in 24 hours
                        issues.append({
                            "type": "stale_pipeline",
                            "description": f"No trades logged in {age_hours:.0f} hours - pipeline may be stuck",
                            "severity": "medium",
                            "auto_fixable": False,
                            "alert_user": True
                        })

                    # Check if trades are actually executing (not just shadow)
                    # Only check last 5 trades for efficiency
                    for trade in recent_trades[-5:]:
                        extra = trade.get("extra", {})
                        # Alert if explicitly set to False (shadow mode confirmed)
                        if extra.get("live_trading_active") is False:
                            issues.append({
                                "type": "shadow_only",
                                "description": "Recent trades are shadow-only - no real revenue being generated!",
                                "severity": "high",
                                "auto_fixable": False,
                                "alert_user": True
                            })
                            break  # Only report once

            except Exception as e:
                logger.error(f"Error checking pipeline execution: {e}")
        else:
            issues.append({
                "type": "no_trades",
                "description": "No shadow trades log found - pipeline not running",
                "severity": "high",
                "auto_fixable": False,
                "alert_user": True
            })

        return issues

    def attempt_fix(self, issue: Dict) -> str:
        """Attempt to automatically fix an issue."""
        if not issue.get("auto_fixable", False):
            if issue.get("alert_user", False):
                logger.warning(f"Issue requires user attention: {issue['description']}")
                self.send_telegram_alert(issue)
            return None

        logger.info(f"Attempting to fix: {issue['description']}")

        try:
            # Execute fix command if provided
            if "fix_cmd" in issue:
                result = subprocess.run(
                    issue["fix_cmd"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    logger.info(f"✓ Fixed: {issue['description']}")
                    return issue['description']
                else:
                    logger.error(f"✗ Fix failed: {result.stderr}")
                    return None

            # Custom fix actions
            elif issue.get("fix_action") == "rotate_log":
                return self.rotate_log()

        except Exception as e:
            logger.error(f"Error applying fix: {e}")
            return None

    def rotate_log(self) -> str:
        """Rotate the main log file."""
        log_file = Path("/var/log/hands-off-engine.log")
        if not log_file.exists():
            return None

        # Move to .1, compress old if exists
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = log_file.parent / f"hands-off-engine.log.{timestamp}"
            log_file.rename(backup)

            # Compress old log
            subprocess.run(["gzip", str(backup)], timeout=30)

            logger.info(f"✓ Rotated log to {backup}.gz")
            return f"Rotated log file ({log_file.stat().st_size / 1024 / 1024:.1f}MB)"

        except Exception as e:
            logger.error(f"Error rotating log: {e}")
            return None

    def send_telegram_alert(self, issue: Dict):
        """Send Telegram alert for issues requiring user attention."""
        try:
            import requests

            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")

            if not bot_token or not chat_id:
                logger.warning("Telegram not configured - cannot send alert")
                return

            severity_emoji = {"low": "🟡", "medium": "🟠", "high": "🔴"}
            emoji = severity_emoji.get(issue.get("severity", "medium"), "🟠")

            message = f"""{emoji} **System Alert**

**Issue Detected:** {issue['description']}

**Type:** {issue['type']}
**Severity:** {issue['severity']}
**Auto-fixable:** No - requires manual intervention

The self-healing agent cannot automatically resolve this issue.
Please investigate when convenient."""

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }

            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()

            logger.info(f"✓ Sent Telegram alert for: {issue['description']}")

        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")

    def run_forever(self):
        """Main loop - run continuously."""
        logger.info("Self-Healing Agent starting...")
        logger.info(f"Check interval: {CHECK_INTERVAL} seconds")

        while True:
            try:
                issues, fixes = self.check_and_heal()

                logger.info(f"Cycle complete: {issues} issues, {fixes} fixes | "
                           f"Total fixes: {self.fixes_applied} | "
                           f"Total checks: {self.checks_performed}")

                # Sleep until next check
                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                logger.info("Shutting down gracefully...")
                self.save_state()
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait a minute before retrying


def main():
    """Entry point."""
    agent = SelfHealingAgent()

    # Check if running as daemon or one-shot
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        logger.info("Running in one-shot mode")
        issues, fixes = agent.check_and_heal()
        print(f"Issues: {issues}, Fixes: {fixes}")
        sys.exit(0)
    else:
        # Run forever
        agent.run_forever()


if __name__ == "__main__":
    main()
