#!/usr/bin/env python3
"""
Server Sync Agent - Automated Repository Synchronization

This agent runs on the server (DigitalOcean droplet) and:
1. Monitors GitHub for new commits to main
2. Automatically pulls the latest code
3. Restarts affected services
4. Logs all sync operations
5. Notifies user via Telegram if issues occur

Designed to run as a systemd service for 24/7 operation.

Setup:
    sudo systemctl enable server-sync-agent
    sudo systemctl start server-sync-agent
"""

import os
import sys
import json
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple

# Configuration
REPO_ROOT = Path(__file__).parent.parent
CHECK_INTERVAL = 300  # 5 minutes - check for new commits
LOG_FILE = "/var/log/server-sync-agent.log"
STATE_FILE = REPO_ROOT / "state" / "server_sync_state.json"
SERVICES_TO_RESTART = [
    "self-healing-agent",
    "coordination-agent",
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE) if os.access(os.path.dirname(LOG_FILE), os.W_OK) else logging.StreamHandler(),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ServerSyncAgent:
    """Automated repository synchronization agent."""

    def __init__(self):
        self.last_commit = None
        self.syncs_performed = 0
        self.load_state()

    def load_state(self):
        """Load agent state from disk."""
        try:
            if STATE_FILE.exists():
                with open(STATE_FILE) as f:
                    state = json.load(f)
                    self.last_commit = state.get("last_commit")
                    self.syncs_performed = state.get("syncs_performed", 0)
                    logger.info(f"Loaded state: last_commit={self.last_commit}, syncs={self.syncs_performed}")
        except Exception as e:
            logger.warning(f"Could not load state: {e}")

    def save_state(self):
        """Save agent state to disk."""
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            state = {
                "last_commit": self.last_commit,
                "syncs_performed": self.syncs_performed,
                "last_check": datetime.now().isoformat(),
            }
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")

    def get_local_commit(self) -> Optional[str]:
        """Get current local commit SHA."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.error(f"Error getting local commit: {e}")
        return None

    def get_remote_commit(self) -> Optional[str]:
        """Get latest remote commit SHA from origin/main."""
        try:
            # First fetch
            fetch_result = subprocess.run(
                ["git", "fetch", "origin", "main"],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=60
            )
            if fetch_result.returncode != 0:
                logger.warning(f"Git fetch warning: {fetch_result.stderr}")

            # Get remote commit
            result = subprocess.run(
                ["git", "rev-parse", "origin/main"],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.error(f"Error getting remote commit: {e}")
        return None

    def check_for_updates(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Check if there are new commits to pull.
        
        Returns:
            Tuple of (has_updates, local_commit, remote_commit)
        """
        local = self.get_local_commit()
        remote = self.get_remote_commit()

        if not local or not remote:
            return False, local, remote

        has_updates = local != remote
        if has_updates:
            logger.info(f"Updates available: {local[:8]} -> {remote[:8]}")
        
        return has_updates, local, remote

    def pull_updates(self) -> bool:
        """Pull latest changes from origin/main."""
        try:
            logger.info("Pulling latest changes...")

            # Handle potential git lock
            lock_file = REPO_ROOT / ".git" / "index.lock"
            if lock_file.exists():
                age = time.time() - lock_file.stat().st_mtime
                if age > 300:  # Stale lock (>5 min)
                    logger.warning("Removing stale git lock")
                    lock_file.unlink()
                else:
                    logger.warning("Git lock exists and is recent - waiting")
                    return False

            # Try to pull with rebase to avoid merge commits
            result = subprocess.run(
                ["git", "pull", "--rebase", "origin", "main"],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=120
            )

            if result.returncode == 0:
                logger.info(f"Pull successful: {result.stdout.strip()}")
                return True
            else:
                # If rebase fails, try regular pull
                logger.warning(f"Rebase failed, trying regular pull: {result.stderr}")
                
                # Abort any ongoing rebase
                subprocess.run(
                    ["git", "rebase", "--abort"],
                    capture_output=True,
                    cwd=str(REPO_ROOT),
                    timeout=30
                )

                # Try regular pull
                result = subprocess.run(
                    ["git", "pull", "origin", "main"],
                    capture_output=True,
                    text=True,
                    cwd=str(REPO_ROOT),
                    timeout=120
                )

                if result.returncode == 0:
                    logger.info(f"Regular pull successful: {result.stdout.strip()}")
                    return True
                else:
                    logger.error(f"Pull failed: {result.stderr}")
                    self.send_alert(f"Git pull failed: {result.stderr[:200]}")
                    return False

        except Exception as e:
            logger.error(f"Error pulling updates: {e}")
            self.send_alert(f"Error pulling updates: {e}")
            return False

    def restart_services(self) -> Dict[str, bool]:
        """Restart affected systemd services."""
        results = {}
        
        for service in SERVICES_TO_RESTART:
            try:
                result = subprocess.run(
                    ["sudo", "systemctl", "restart", service],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                success = result.returncode == 0
                results[service] = success
                
                if success:
                    logger.info(f"✓ Restarted {service}")
                else:
                    logger.warning(f"✗ Failed to restart {service}: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error restarting {service}: {e}")
                results[service] = False

        return results

    def get_changed_files(self, from_commit: str, to_commit: str) -> list:
        """Get list of files changed between commits."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", from_commit, to_commit],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=30
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                # Return empty list if no changes, otherwise split by newline
                return output.split('\n') if output else []
        except Exception as e:
            logger.error(f"Error getting changed files: {e}")
        return []

    def should_restart_services(self, changed_files: list) -> bool:
        """Determine if services need restarting based on changed files."""
        # Files that trigger service restart
        restart_triggers = [
            "scripts/self_healing_agent.py",
            "scripts/coordination_agent.py",
            "scripts/server_sync_agent.py",
            "telegram/",
            "ai/",
            "executor/",
            "decider/",
            "alpha/",
        ]

        for file in changed_files:
            for trigger in restart_triggers:
                if file.startswith(trigger) or file == trigger.rstrip('/'):
                    return True
        
        return False

    def send_alert(self, message: str):
        """Send alert via Telegram."""
        try:
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")

            if not bot_token or not chat_id:
                logger.warning("Telegram not configured - alert not sent")
                return

            import requests
            
            full_message = f"🔄 **Server Sync Agent**\n\n{message}"
            
            response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": full_message,
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
            response.raise_for_status()
            logger.info("Alert sent to Telegram")

        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")

    def send_sync_notification(self, from_commit: str, to_commit: str, 
                                changed_files: list, services_restarted: Dict[str, bool]):
        """Send notification about successful sync."""
        try:
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")

            if not bot_token or not chat_id:
                return

            import requests

            # Build message
            files_summary = f"{len(changed_files)} files" if len(changed_files) > 5 else ", ".join(changed_files[:5])
            
            services_msg = ""
            if services_restarted:
                success = [s for s, ok in services_restarted.items() if ok]
                failed = [s for s, ok in services_restarted.items() if not ok]
                if success:
                    services_msg += f"\n✅ Restarted: {', '.join(success)}"
                if failed:
                    services_msg += f"\n❌ Failed: {', '.join(failed)}"

            message = f"""✅ **Server Synced Successfully**

📦 {from_commit[:8]} → {to_commit[:8]}
📁 Changed: {files_summary}
{services_msg}
🕐 {datetime.now().strftime('%H:%M')} UTC"""

            response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
            response.raise_for_status()

        except Exception as e:
            logger.error(f"Failed to send sync notification: {e}")

    def run_sync_cycle(self) -> bool:
        """Run one sync cycle.
        
        Returns:
            True if sync was performed, False otherwise
        """
        logger.info("Checking for updates...")

        has_updates, local, remote = self.check_for_updates()

        if not has_updates:
            logger.info("No updates available")
            return False

        logger.info(f"Updates found: {local[:8]} -> {remote[:8]}")

        # Get changed files before pulling
        changed_files = self.get_changed_files(local, remote)
        logger.info(f"Changed files: {len(changed_files)}")

        # Pull updates
        if not self.pull_updates():
            logger.error("Failed to pull updates")
            return False

        # Track the sync
        self.last_commit = remote
        self.syncs_performed += 1
        self.save_state()

        # Restart services if needed
        services_restarted = {}
        if self.should_restart_services(changed_files):
            logger.info("Restarting affected services...")
            services_restarted = self.restart_services()

        # Notify user
        self.send_sync_notification(local, remote, changed_files, services_restarted)

        logger.info(f"✓ Sync complete. Total syncs: {self.syncs_performed}")
        return True

    def run_forever(self):
        """Run continuously, checking for updates."""
        logger.info("Server Sync Agent starting...")
        logger.info(f"Repository: {REPO_ROOT}")
        logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
        logger.info(f"Services to restart: {SERVICES_TO_RESTART}")

        while True:
            try:
                self.run_sync_cycle()

            except KeyboardInterrupt:
                logger.info("Shutting down gracefully...")
                self.save_state()
                break
            except Exception as e:
                logger.error(f"Error in sync cycle: {e}")
                self.send_alert(f"Sync agent error: {e}")

            # Wait for next check
            time.sleep(CHECK_INTERVAL)


def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Server Sync Agent")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--force", action="store_true", help="Force sync even if no updates")
    args = parser.parse_args()

    agent = ServerSyncAgent()

    if args.once:
        if args.force:
            # Force pull regardless of current state
            agent.pull_updates()
            agent.restart_services()
        else:
            agent.run_sync_cycle()
    else:
        agent.run_forever()


if __name__ == "__main__":
    main()
