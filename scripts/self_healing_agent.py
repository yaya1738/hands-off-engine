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
- Monitor CPU/Memory usage and auto-scale droplet if needed
- Kill runaway processes consuming excessive resources

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
from typing import List, Dict, Tuple, Optional

# Configuration
REPO_ROOT = Path(__file__).parent.parent
LOG_FILE = "/var/log/self-healing-agent.log"
CHECK_INTERVAL = 300  # 5 minutes
STATE_FILE = REPO_ROOT / "state" / "self_healing_state.json"
RESOURCE_CONFIG_FILE = REPO_ROOT / "config" / "resource_limits.json"

# Resource thresholds (defaults, can be overridden by config file)
DEFAULT_RESOURCE_LIMITS = {
    "cpu_warning_threshold": 80,      # Warn at 80% CPU
    "cpu_critical_threshold": 95,     # Critical at 95% CPU
    "memory_warning_threshold": 80,   # Warn at 80% memory
    "memory_critical_threshold": 95,  # Critical at 95% memory
    "auto_scale_enabled": True,       # Enable DigitalOcean auto-scaling
    "auto_kill_runaway_enabled": True,  # Kill processes using >50% CPU for >10 min
    "runaway_cpu_threshold": 50,      # % CPU to consider runaway
    "runaway_duration_seconds": 600,  # 10 minutes before killing
    "droplet_upgrade_sizes": ["s-1vcpu-1gb", "s-1vcpu-2gb", "s-2vcpu-2gb", "s-2vcpu-4gb", "s-4vcpu-8gb"],
    "max_droplet_size": "s-4vcpu-8gb"  # Don't upgrade beyond this
}

# Setup logging - try file first, fall back to stderr if needed
try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
except (OSError, PermissionError):
    # Fall back to stderr only if log file isn't writable
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()]
    )
logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitor CPU, memory, and other system resources."""

    @staticmethod
    def get_cpu_usage() -> float:
        """Get current CPU usage percentage using /proc/stat."""
        try:
            # Use top for a quick sample
            result = subprocess.run(
                ["top", "-bn1"],
                capture_output=True,
                text=True,
                timeout=10
            )
            for line in result.stdout.split('\n'):
                if '%Cpu' in line or 'Cpu(s)' in line:
                    # Parse: %Cpu(s): 10.0 us, 5.0 sy, ...
                    parts = line.split(',')
                    idle = 0.0
                    for part in parts:
                        if 'id' in part:
                            idle = float(part.strip().split()[0])
                            break
                    return round(100.0 - idle, 1)
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
        return 0.0

    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get memory usage from /proc/meminfo."""
        try:
            result = subprocess.run(
                ["free", "-b"],
                capture_output=True,
                text=True,
                timeout=10
            )
            lines = result.stdout.strip().split('\n')
            # Parse: Mem: total used free shared buff/cache available
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 7:
                    total = int(parts[1])
                    used = int(parts[2])
                    available = int(parts[6])
                    used_pct = round((total - available) / total * 100, 1)
                    return {
                        "total_mb": round(total / (1024 * 1024), 1),
                        "used_mb": round(used / (1024 * 1024), 1),
                        "available_mb": round(available / (1024 * 1024), 1),
                        "used_percent": used_pct
                    }
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
        return {"total_mb": 0, "used_mb": 0, "available_mb": 0, "used_percent": 0}

    @staticmethod
    def get_high_cpu_processes() -> List[Dict]:
        """Get list of processes using high CPU."""
        processes = []
        try:
            result = subprocess.run(
                ["ps", "aux", "--sort=-%cpu"],
                capture_output=True,
                text=True,
                timeout=10
            )
            lines = result.stdout.strip().split('\n')[1:11]  # Top 10 processes
            for line in lines:
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    cpu_pct = float(parts[2])
                    if cpu_pct > 5:  # Only processes using >5% CPU
                        processes.append({
                            "pid": int(parts[1]),
                            "user": parts[0],
                            "cpu_percent": cpu_pct,
                            "mem_percent": float(parts[3]),
                            "command": parts[10][:50]  # Truncate command
                        })
        except Exception as e:
            logger.error(f"Error getting high CPU processes: {e}")
        return processes


class DigitalOceanManager:
    """Manage DigitalOcean droplet scaling via API."""

    def __init__(self):
        self.api_token = os.getenv("DIGITALOCEAN_API_TOKEN") or os.getenv("DO_API_TOKEN")
        self.droplet_id = os.getenv("DIGITALOCEAN_DROPLET_ID") or os.getenv("DO_DROPLET_ID")
        self.api_base = "https://api.digitalocean.com/v2"

    def is_configured(self) -> bool:
        """Check if DigitalOcean API is configured."""
        return bool(self.api_token and self.droplet_id)

    def _api_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request to DigitalOcean."""
        try:
            import requests
            url = f"{self.api_base}{endpoint}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            response = requests.request(method, url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            if response.text:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"DigitalOcean API error: {e}")
            return None

    def get_droplet_info(self) -> Optional[Dict]:
        """Get current droplet information."""
        if not self.is_configured():
            return None
        result = self._api_request("GET", f"/droplets/{self.droplet_id}")
        if result:
            return result.get("droplet")
        return None

    def get_current_size(self) -> Optional[str]:
        """Get current droplet size slug."""
        droplet = self.get_droplet_info()
        if droplet:
            return droplet.get("size", {}).get("slug")
        return None

    def resize_droplet(self, new_size: str, disk_resize: bool = False) -> bool:
        """Resize the droplet to a new size.

        Note: This requires a power-off for some resize types.
        disk_resize=False allows resizing CPU/RAM only (reversible).
        """
        if not self.is_configured():
            logger.warning("DigitalOcean API not configured - cannot resize")
            return False

        logger.info(f"Attempting to resize droplet to {new_size}...")

        # First, power off the droplet
        power_off = self._api_request("POST", f"/droplets/{self.droplet_id}/actions", {
            "type": "power_off"
        })

        if not power_off:
            logger.error("Failed to power off droplet for resize")
            return False

        # Wait for power off (check status)
        time.sleep(15)

        # Perform resize
        resize = self._api_request("POST", f"/droplets/{self.droplet_id}/actions", {
            "type": "resize",
            "disk": disk_resize,
            "size": new_size
        })

        if not resize:
            logger.error("Failed to resize droplet")
            # Try to power back on
            self._api_request("POST", f"/droplets/{self.droplet_id}/actions", {"type": "power_on"})
            return False

        # Wait for resize
        time.sleep(30)

        # Power back on
        power_on = self._api_request("POST", f"/droplets/{self.droplet_id}/actions", {
            "type": "power_on"
        })

        if power_on:
            logger.info(f"✓ Droplet resized to {new_size} and powered on")
            return True

        logger.error("Failed to power on droplet after resize")
        return False

    def get_next_size_up(self, current_size: str, size_list: List[str], max_size: str) -> Optional[str]:
        """Get the next larger size from the list."""
        try:
            if current_size not in size_list:
                # If current size not in list, return smallest
                return size_list[0] if size_list else None

            current_idx = size_list.index(current_size)
            max_idx = size_list.index(max_size) if max_size in size_list else len(size_list) - 1

            if current_idx >= max_idx:
                return None  # Already at max size

            return size_list[current_idx + 1]
        except Exception as e:
            logger.error(f"Error determining next size: {e}")
            return None


class SelfHealingAgent:
    """Autonomous agent that monitors and repairs system issues."""

    def __init__(self):
        self.fixes_applied = 0
        self.checks_performed = 0
        self.state = self.load_state()
        self.resource_limits = self.load_resource_config()
        self.resource_monitor = ResourceMonitor()
        self.do_manager = DigitalOceanManager()
        self.high_resource_start_times: Dict[int, float] = {}  # PID -> start time of high CPU

    def load_state(self) -> Dict:
        """Load agent state from disk."""
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
        return {
            "total_fixes": 0,
            "last_check": None,
            "issues_detected": [],
            "auto_fixed": [],
            "resource_history": [],
            "last_resize": None
        }

    def load_resource_config(self) -> Dict:
        """Load resource limits configuration."""
        if RESOURCE_CONFIG_FILE.exists():
            try:
                with open(RESOURCE_CONFIG_FILE) as f:
                    config = json.load(f)
                    # Merge with defaults
                    return {**DEFAULT_RESOURCE_LIMITS, **config}
            except Exception as e:
                logger.error(f"Error loading resource config: {e}")
        return DEFAULT_RESOURCE_LIMITS.copy()

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

        # NEW: Resource monitoring checks
        issues.extend(self.check_cpu_usage())
        issues.extend(self.check_memory_usage())
        issues.extend(self.check_runaway_processes())

        # Attempt to fix each issue
        for issue in issues:
            fix_result = self.attempt_fix(issue)
            if fix_result:
                fixes.append(fix_result)
                self.fixes_applied += 1

        # Update state with resource history
        cpu = self.resource_monitor.get_cpu_usage()
        mem = self.resource_monitor.get_memory_usage()
        resource_snapshot = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu,
            "memory_percent": mem.get("used_percent", 0),
            "memory_available_mb": mem.get("available_mb", 0)
        }

        # Keep last 100 snapshots
        if "resource_history" not in self.state:
            self.state["resource_history"] = []
        self.state["resource_history"].append(resource_snapshot)
        self.state["resource_history"] = self.state["resource_history"][-100:]

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

    def check_cpu_usage(self) -> List[Dict]:
        """Check CPU usage and trigger auto-scaling if needed."""
        issues = []
        cpu = self.resource_monitor.get_cpu_usage()
        warning_threshold = self.resource_limits.get("cpu_warning_threshold", 80)
        critical_threshold = self.resource_limits.get("cpu_critical_threshold", 95)

        logger.info(f"CPU usage: {cpu}%")

        if cpu >= critical_threshold:
            issues.append({
                "type": "cpu_critical",
                "description": f"CPU usage CRITICAL at {cpu}% (threshold: {critical_threshold}%)",
                "severity": "critical",
                "auto_fixable": self.resource_limits.get("auto_scale_enabled", True),
                "fix_action": "scale_droplet",
                "alert_user": True,
                "cpu_percent": cpu
            })
        elif cpu >= warning_threshold:
            issues.append({
                "type": "cpu_warning",
                "description": f"CPU usage HIGH at {cpu}% (threshold: {warning_threshold}%)",
                "severity": "high",
                "auto_fixable": False,  # Don't auto-scale on warning, just alert
                "alert_user": True,
                "cpu_percent": cpu
            })

        return issues

    def check_memory_usage(self) -> List[Dict]:
        """Check memory usage and trigger auto-scaling if needed."""
        issues = []
        mem = self.resource_monitor.get_memory_usage()
        mem_pct = mem.get("used_percent", 0)
        warning_threshold = self.resource_limits.get("memory_warning_threshold", 80)
        critical_threshold = self.resource_limits.get("memory_critical_threshold", 95)

        logger.info(f"Memory usage: {mem_pct}% (available: {mem.get('available_mb', 0)}MB)")

        if mem_pct >= critical_threshold:
            issues.append({
                "type": "memory_critical",
                "description": f"Memory usage CRITICAL at {mem_pct}% (available: {mem.get('available_mb', 0)}MB)",
                "severity": "critical",
                "auto_fixable": self.resource_limits.get("auto_scale_enabled", True),
                "fix_action": "scale_droplet",
                "alert_user": True,
                "memory_percent": mem_pct,
                "memory_available_mb": mem.get("available_mb", 0)
            })
        elif mem_pct >= warning_threshold:
            issues.append({
                "type": "memory_warning",
                "description": f"Memory usage HIGH at {mem_pct}% (available: {mem.get('available_mb', 0)}MB)",
                "severity": "high",
                "auto_fixable": False,  # Don't auto-scale on warning, just alert
                "alert_user": True,
                "memory_percent": mem_pct
            })

        return issues

    def check_runaway_processes(self) -> List[Dict]:
        """Check for runaway processes consuming excessive CPU."""
        if not self.resource_limits.get("auto_kill_runaway_enabled", True):
            return []

        issues = []
        runaway_threshold = self.resource_limits.get("runaway_cpu_threshold", 50)
        duration_threshold = self.resource_limits.get("runaway_duration_seconds", 600)

        high_cpu_procs = self.resource_monitor.get_high_cpu_processes()
        current_time = time.time()

        # Track which PIDs are still high
        current_high_pids = set()

        for proc in high_cpu_procs:
            pid = proc["pid"]
            cpu_pct = proc["cpu_percent"]

            if cpu_pct >= runaway_threshold:
                current_high_pids.add(pid)

                # Check if we've been tracking this PID
                if pid not in self.high_resource_start_times:
                    self.high_resource_start_times[pid] = current_time
                    logger.info(f"Tracking high CPU process: PID {pid} at {cpu_pct}% - {proc['command']}")
                else:
                    duration = current_time - self.high_resource_start_times[pid]
                    if duration >= duration_threshold:
                        issues.append({
                            "type": "runaway_process",
                            "description": f"Runaway process PID {pid} using {cpu_pct}% CPU for {int(duration/60)} min",
                            "severity": "high",
                            "auto_fixable": True,
                            "fix_action": "kill_process",
                            "pid": pid,
                            "command": proc["command"],
                            "cpu_percent": cpu_pct,
                            "duration_seconds": duration
                        })

        # Clean up PIDs that are no longer high CPU
        for pid in list(self.high_resource_start_times.keys()):
            if pid not in current_high_pids:
                del self.high_resource_start_times[pid]

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
            fix_action = issue.get("fix_action")
            if fix_action == "rotate_log":
                return self.rotate_log()
            elif fix_action == "scale_droplet":
                return self.scale_droplet(issue)
            elif fix_action == "kill_process":
                return self.kill_runaway_process(issue)

        except Exception as e:
            logger.error(f"Error applying fix: {e}")
            return None

    def scale_droplet(self, issue: Dict) -> Optional[str]:
        """Scale the DigitalOcean droplet to a larger size."""
        if not self.do_manager.is_configured():
            logger.warning("DigitalOcean API not configured - cannot auto-scale")
            # Still alert user
            self.send_telegram_alert({
                **issue,
                "description": f"{issue['description']} - AUTO-SCALE UNAVAILABLE (API not configured)"
            })
            return None

        current_size = self.do_manager.get_current_size()
        if not current_size:
            logger.error("Could not determine current droplet size")
            return None

        size_list = self.resource_limits.get("droplet_upgrade_sizes", [])
        max_size = self.resource_limits.get("max_droplet_size", "s-4vcpu-8gb")

        next_size = self.do_manager.get_next_size_up(current_size, size_list, max_size)

        if not next_size:
            logger.warning(f"Already at maximum size ({current_size}) - cannot scale further")
            self.send_telegram_alert({
                **issue,
                "description": f"{issue['description']} - AT MAX SIZE ({current_size}), cannot auto-scale"
            })
            return None

        # Attempt resize
        logger.info(f"Auto-scaling droplet from {current_size} to {next_size}")

        # Send alert before scaling (system will be briefly offline)
        self.send_telegram_alert({
            "type": "auto_scale",
            "description": f"AUTO-SCALING: Upgrading droplet from {current_size} to {next_size}",
            "severity": "high",
            "reason": issue['description']
        })

        if self.do_manager.resize_droplet(next_size):
            self.state["last_resize"] = {
                "timestamp": datetime.now().isoformat(),
                "from_size": current_size,
                "to_size": next_size,
                "reason": issue['description']
            }
            return f"Scaled droplet from {current_size} to {next_size}"
        else:
            logger.error("Droplet resize failed")
            return None

    def kill_runaway_process(self, issue: Dict) -> Optional[str]:
        """Kill a runaway process consuming excessive CPU."""
        pid = issue.get("pid")
        if not pid:
            return None

        try:
            # First try SIGTERM (graceful)
            logger.info(f"Sending SIGTERM to PID {pid}")
            subprocess.run(["kill", "-15", str(pid)], timeout=5)
            time.sleep(3)

            # Check if still running
            result = subprocess.run(
                ["ps", "-p", str(pid)],
                capture_output=True,
                timeout=5
            )

            if result.returncode == 0:
                # Still running, send SIGKILL
                logger.info(f"Process still alive, sending SIGKILL to PID {pid}")
                subprocess.run(["kill", "-9", str(pid)], timeout=5)

            # Remove from tracking
            if pid in self.high_resource_start_times:
                del self.high_resource_start_times[pid]

            logger.info(f"✓ Killed runaway process: PID {pid}")

            # Send notification
            self.send_telegram_alert({
                "type": "process_killed",
                "description": f"Killed runaway process: {issue.get('command', 'unknown')} (PID {pid})",
                "severity": "medium",
                "cpu_percent": issue.get("cpu_percent"),
                "duration_minutes": int(issue.get("duration_seconds", 0) / 60)
            })

            return f"Killed runaway process PID {pid} ({issue.get('command', 'unknown')[:30]})"

        except Exception as e:
            logger.error(f"Error killing process {pid}: {e}")
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
