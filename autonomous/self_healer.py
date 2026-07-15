#!/usr/bin/env python3
"""
SELF-HEALER - Autonomous Recovery & Protection System

Handles:
1. CLI session termination protection
2. Process crash recovery
3. Node failure detection and mitigation
4. State corruption repair
5. Network partition handling
6. Orphaned resource cleanup

RULES:
- NEVER turn off any droplet
- NEVER restart droplets via API
- Recover by adding redundancy, not by restarting
- Protect all critical processes from termination

Standard: Yair Siegel Master Level Operations - Self-Preservation
"""

import json
import os
import sys
import time
import signal
import socket
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
import urllib.request

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
LOG_DIR = BASE_DIR / 'logs'

STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ProcessGuard:
    """Configuration for a guarded process."""
    name: str
    command: str
    working_dir: str = str(BASE_DIR)
    restart_delay_sec: int = 10
    max_restarts_per_hour: int = 5
    critical: bool = True  # If True, system is degraded when down
    code_file: str = ''  # Path to main code file for staleness check


@dataclass
class HealingAction:
    """A healing action taken."""
    timestamp: str
    action_type: str
    target: str
    reason: str
    success: bool
    details: Dict = field(default_factory=dict)


class SelfHealer:
    """
    Autonomous self-healing system.

    Monitors and recovers:
    - Critical processes
    - Node connectivity
    - State file integrity
    - System resources
    """

    # Critical processes that must always run
    GUARDED_PROCESSES = [
        ProcessGuard(
            name='backend-loop',
            command='python3 /data/data/com.termux/files/home/hands-off-engine-forensic-jan9/autonomous/backend_loop.py',
            critical=True,
            restart_delay_sec=5,  # Fast restart - this is the main orchestrator
            max_restarts_per_hour=10,
            code_file=str(BASE_DIR) + '/autonomous/backend_loop.py'
        ),
        ProcessGuard(
            name='hardware-brain',
            command='python3 /data/data/com.termux/files/home/hands-off-engine-forensic-jan9/autonomous/hardware_brain.py run',
            critical=True
        ),
        ProcessGuard(
            name='scaling-engine',
            command='python3 /data/data/com.termux/files/home/hands-off-engine-forensic-jan9/autonomous/scaling_engine.py run',
            critical=True
        ),
        ProcessGuard(
            name='infra-monitor',
            command='python3 /data/data/com.termux/files/home/hands-off-engine-forensic-jan9/autonomous/infra_manager.py monitor',
            critical=True
        ),
        # NOTE: position_monitor is a check-and-exit script, not a daemon
        # It runs via cron, not as a persistent process
    ]

    # Protected systemd services
    PROTECTED_SERVICES = [
        'hands-off-autonomous.service',
        'infra-monitor.service',
        'self-healing-agent.service',
    ]

    def __init__(self):
        self.hostname = socket.gethostname()
        self.start_time = datetime.utcnow()
        self.healing_history: List[HealingAction] = []
        self.restart_counts: Dict[str, List[datetime]] = {}
        self._shutdown = threading.Event()

        # Setup signal handlers for CLI protection
        self._setup_signal_handlers()

        self._log("Self-Healer initialized", {'hostname': self.hostname})

    def _setup_signal_handlers(self):
        """
        Setup signal handlers to protect against CLI termination.

        SIGHUP: Sent when SSH session disconnects - IGNORE IT
        SIGTERM: Sent by systemd for graceful shutdown - handle gracefully
        SIGINT: Ctrl+C - handle gracefully
        """
        # Ignore hangup - this is what kills processes when CLI disconnects
        signal.signal(signal.SIGHUP, signal.SIG_IGN)

        # Handle termination gracefully
        signal.signal(signal.SIGTERM, self._graceful_shutdown_handler)
        signal.signal(signal.SIGINT, self._graceful_shutdown_handler)

        # Detach from controlling terminal
        try:
            os.setsid()
        except OSError:
            pass  # May already be session leader

        self._log("Signal handlers configured - CLI protection active")

    def _graceful_shutdown_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self._log(f"Received signal {signum} - initiating graceful shutdown")
        self._shutdown.set()
        self._save_state()
        # Don't exit immediately - let main loop clean up

    def _log(self, message: str, data: Dict = None, level: str = 'info'):
        """Log a message."""
        timestamp = datetime.utcnow().isoformat()
        log_line = f"[{timestamp}] [HEALER] [{level.upper()}] {message}"
        if data:
            log_line += f" | {json.dumps(data)}"

        print(log_line)

        log_file = LOG_DIR / 'self_healer.log'
        try:
            with open(log_file, 'a') as f:
                f.write(log_line + '\n')
        except:
            pass

    def _save_state(self):
        """Save healing state."""
        state = {
            'last_save': datetime.utcnow().isoformat(),
            'hostname': self.hostname,
            'uptime_hours': (datetime.utcnow() - self.start_time).total_seconds() / 3600,
            'healing_actions': [
                {**vars(a)} for a in self.healing_history[-100:]
            ],
            'restart_counts': {
                k: [t.isoformat() for t in v]
                for k, v in self.restart_counts.items()
            },
        }
        state_file = STATE_DIR / 'self_healer_state.json'
        state_file.write_text(json.dumps(state, indent=2, default=str))

    # ========================================================================
    # PROCESS MONITORING & RECOVERY
    # ========================================================================

    def check_process_running(self, process: ProcessGuard) -> Tuple[bool, Optional[int]]:
        """
        Check if a guarded process is running.

        Returns: (is_running, pid)
        """
        try:
            # Use pgrep to find the process
            result = subprocess.run(
                ['pgrep', '-f', process.command[:50]],  # Use partial match
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                return True, int(pids[0])

            return False, None

        except Exception as e:
            self._log(f"Error checking process {process.name}: {e}", level='error')
            return False, None

    def check_code_stale(self, process: ProcessGuard, pid: int) -> bool:
        """
        INTEGRAFIX: Check if process is running stale code.

        Compares code file mtime to process start time.
        If code is newer than process, code is stale and needs restart.

        Returns: True if code is stale (needs restart)
        """
        if not process.code_file:
            return False

        try:
            code_path = Path(process.code_file)
            if not code_path.exists():
                return False

            # Get code file modification time
            code_mtime = code_path.stat().st_mtime

            # Get process start time from /proc
            proc_stat = Path(f'/proc/{pid}/stat')
            if not proc_stat.exists():
                return False

            # Get system boot time and process start time in jiffies
            with open('/proc/uptime') as f:
                uptime_seconds = float(f.read().split()[0])

            with open(f'/proc/{pid}/stat') as f:
                stat_fields = f.read().split()
                # Field 22 is starttime in clock ticks since boot
                starttime_ticks = int(stat_fields[21])

            # Convert to epoch time
            clock_ticks_per_sec = os.sysconf('SC_CLK_TCK')
            boot_time = time.time() - uptime_seconds
            process_start_time = boot_time + (starttime_ticks / clock_ticks_per_sec)

            # Check if code is newer than process
            is_stale = code_mtime > process_start_time

            if is_stale:
                code_age = datetime.fromtimestamp(code_mtime).strftime('%H:%M:%S')
                proc_age = datetime.fromtimestamp(process_start_time).strftime('%H:%M:%S')
                self._log(f"STALE CODE: {process.name} - code updated {code_age}, process started {proc_age}")

            return is_stale

        except Exception as e:
            self._log(f"Error checking code staleness for {process.name}: {e}", level='error')
            return False

    def _can_restart_process(self, process: ProcessGuard) -> bool:
        """Check if we can restart a process (rate limiting)."""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)

        # Get restart history
        restarts = self.restart_counts.get(process.name, [])

        # Filter to last hour
        recent_restarts = [t for t in restarts if t > hour_ago]
        self.restart_counts[process.name] = recent_restarts

        return len(recent_restarts) < process.max_restarts_per_hour

    def restart_process(self, process: ProcessGuard) -> bool:
        """
        Restart a guarded process.

        Uses nohup and disown to ensure process survives CLI disconnect.
        """
        if not self._can_restart_process(process):
            self._log(f"Rate limit reached for {process.name}", level='warning')
            return False

        self._log(f"Restarting process: {process.name}")

        try:
            # Kill existing if any
            subprocess.run(['pkill', '-f', process.command[:50]], capture_output=True)
            time.sleep(2)

            # Start with nohup to survive terminal disconnect
            log_file = LOG_DIR / f"{process.name}.log"
            cmd = f"nohup {process.command} >> {log_file} 2>&1 &"

            subprocess.Popen(
                cmd,
                shell=True,
                cwd=process.working_dir,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,  # Detach from terminal
            )

            # Record restart
            if process.name not in self.restart_counts:
                self.restart_counts[process.name] = []
            self.restart_counts[process.name].append(datetime.utcnow())

            # Record healing action
            self.healing_history.append(HealingAction(
                timestamp=datetime.utcnow().isoformat(),
                action_type='restart_process',
                target=process.name,
                reason='Process not running',
                success=True,
            ))

            time.sleep(process.restart_delay_sec)

            # Verify it started
            running, pid = self.check_process_running(process)
            if running:
                self._log(f"Process {process.name} started with PID {pid}")
                return True
            else:
                self._log(f"Process {process.name} failed to start", level='error')
                return False

        except Exception as e:
            self._log(f"Error restarting {process.name}: {e}", level='error')
            self.healing_history.append(HealingAction(
                timestamp=datetime.utcnow().isoformat(),
                action_type='restart_process',
                target=process.name,
                reason='Process not running',
                success=False,
                details={'error': str(e)},
            ))
            return False

    def check_and_heal_processes(self) -> Dict:
        """Check all guarded processes and restart any that are down."""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'processes': {},
            'actions_taken': [],
        }

        for process in self.GUARDED_PROCESSES:
            running, pid = self.check_process_running(process)

            status = {
                'running': running,
                'pid': pid,
                'critical': process.critical,
            }

            if not running:
                self._log(f"Process {process.name} is DOWN", level='warning')

                if self.restart_process(process):
                    status['action'] = 'restarted'
                    results['actions_taken'].append(f"Restarted {process.name}")
                else:
                    status['action'] = 'restart_failed'

            # INTEGRAFIX: Check for stale code even if running
            elif pid and self.check_code_stale(process, pid):
                self._log(f"Process {process.name} running STALE CODE - restarting", level='warning')

                if self.restart_process(process):
                    status['action'] = 'restarted_stale_code'
                    status['stale'] = True
                    results['actions_taken'].append(f"Restarted {process.name} (stale code)")
                else:
                    status['action'] = 'restart_failed'

            results['processes'][process.name] = status

        return results

    # ========================================================================
    # SYSTEMD SERVICE MONITORING
    # ========================================================================

    def check_service_status(self, service_name: str) -> Tuple[bool, str]:
        """Check if a systemd service is running."""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True
            )
            status = result.stdout.strip()
            return status == 'active', status
        except:
            return False, 'unknown'

    def ensure_services_running(self) -> Dict:
        """Ensure all protected services are running."""
        results = {}

        for service in self.PROTECTED_SERVICES:
            active, status = self.check_service_status(service)
            results[service] = {'active': active, 'status': status}

            if not active and status != 'unknown':
                self._log(f"Service {service} is not active (status: {status})")

                try:
                    subprocess.run(['systemctl', 'start', service], capture_output=True)
                    time.sleep(2)
                    active, status = self.check_service_status(service)
                    results[service] = {'active': active, 'status': status, 'action': 'started'}

                    self.healing_history.append(HealingAction(
                        timestamp=datetime.utcnow().isoformat(),
                        action_type='start_service',
                        target=service,
                        reason=f'Service was {status}',
                        success=active,
                    ))
                except Exception as e:
                    self._log(f"Failed to start service {service}: {e}", level='error')

        return results

    # ========================================================================
    # STATE FILE INTEGRITY
    # ========================================================================

    def check_state_files(self) -> Dict:
        """Check and repair state files."""
        results = {}

        critical_files = [
            'brain_state.json',
            'scaling_state.json',
            'infra_state.json',
            'cluster_state.json',
        ]

        for filename in critical_files:
            filepath = STATE_DIR / filename

            if not filepath.exists():
                results[filename] = {'exists': False, 'action': 'created_empty'}
                filepath.write_text('{}')
                continue

            try:
                content = filepath.read_text()
                if content.strip():
                    json.loads(content)  # Validate JSON
                    results[filename] = {'exists': True, 'valid': True}
                else:
                    results[filename] = {'exists': True, 'valid': False, 'action': 'repaired_empty'}
                    filepath.write_text('{}')

            except json.JSONDecodeError:
                results[filename] = {'exists': True, 'valid': False, 'action': 'repaired_corrupt'}
                # Backup corrupt file and create fresh
                backup = filepath.with_suffix('.json.corrupt')
                filepath.rename(backup)
                filepath.write_text('{}')

                self.healing_history.append(HealingAction(
                    timestamp=datetime.utcnow().isoformat(),
                    action_type='repair_state_file',
                    target=filename,
                    reason='JSON parse error',
                    success=True,
                ))

        return results

    # ========================================================================
    # DISK SPACE MONITORING
    # ========================================================================

    def check_disk_space(self) -> Dict:
        """Check disk space and clean up if needed."""
        try:
            result = subprocess.run(
                ['df', '-h', '/'],
                capture_output=True,
                text=True
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                used_pct = int(parts[4].rstrip('%'))

                status = {
                    'total': parts[1],
                    'used': parts[2],
                    'available': parts[3],
                    'used_pct': used_pct,
                }

                if used_pct > 90:
                    self._log(f"Disk space critical: {used_pct}%", level='warning')
                    status['action'] = 'cleanup_needed'

                    # Clean up old logs
                    self._cleanup_old_logs()

                return status

        except Exception as e:
            return {'error': str(e)}

    def _cleanup_old_logs(self):
        """Clean up old log files."""
        try:
            # Remove logs older than 7 days
            subprocess.run([
                'find', str(LOG_DIR), '-type', 'f', '-name', '*.log',
                '-mtime', '+7', '-delete'
            ], capture_output=True)

            # Truncate large log files
            for log_file in LOG_DIR.glob('*.log'):
                if log_file.stat().st_size > 100 * 1024 * 1024:  # 100MB
                    # Keep last 10000 lines
                    subprocess.run([
                        'tail', '-n', '10000', str(log_file)
                    ], capture_output=True)

            self._log("Cleaned up old logs")

        except Exception as e:
            self._log(f"Error cleaning logs: {e}", level='error')

    # ========================================================================
    # NETWORK CONNECTIVITY
    # ========================================================================

    def check_network(self) -> Dict:
        """Check network connectivity to critical endpoints."""
        endpoints = [
            ('api.digitalocean.com', 443),
            ('github.com', 443),
            ('api.openai.com', 443),
        ]

        results = {}

        for host, port in endpoints:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                results[host] = result == 0
            except:
                results[host] = False

        return results

    # ========================================================================
    # MAIN HEALING LOOP
    # ========================================================================

    def run_healing_loop(self, interval_sec: int = 60):
        """
        Run continuous healing loop.

        Checks and heals:
        1. Critical processes
        2. Systemd services
        3. State file integrity
        4. Disk space
        5. Network connectivity
        """
        self._log("Starting self-healing loop", {'interval': interval_sec})

        iteration = 0

        while not self._shutdown.is_set():
            iteration += 1

            try:
                self._log(f"[Iteration {iteration}] Running health checks")

                # Check processes
                process_results = self.check_and_heal_processes()
                down_count = sum(1 for p in process_results['processes'].values() if not p['running'])
                if down_count > 0:
                    self._log(f"  Processes: {down_count} were down")

                # Check services (less frequently)
                if iteration % 5 == 0:
                    service_results = self.ensure_services_running()
                    inactive = [s for s, v in service_results.items() if not v['active']]
                    if inactive:
                        self._log(f"  Services: {len(inactive)} inactive")

                # Check state files
                if iteration % 10 == 0:
                    state_results = self.check_state_files()
                    repaired = [f for f, v in state_results.items() if 'action' in v]
                    if repaired:
                        self._log(f"  State files: {len(repaired)} repaired")

                # Check disk space
                if iteration % 30 == 0:
                    disk_result = self.check_disk_space()
                    if disk_result.get('used_pct', 0) > 80:
                        self._log(f"  Disk: {disk_result['used_pct']}% used")

                # Check network
                if iteration % 10 == 0:
                    network_results = self.check_network()
                    offline = [h for h, v in network_results.items() if not v]
                    if offline:
                        self._log(f"  Network: {len(offline)} endpoints unreachable")

                # Save state
                self._save_state()

            except Exception as e:
                self._log(f"Error in healing loop: {e}", level='error')

            # Sleep until next iteration
            self._shutdown.wait(timeout=interval_sec)

        self._log("Self-healer shutting down")

    def status(self) -> Dict:
        """Get current healer status."""
        return {
            'hostname': self.hostname,
            'uptime_hours': (datetime.utcnow() - self.start_time).total_seconds() / 3600,
            'processes': {
                p.name: {'running': self.check_process_running(p)[0], 'critical': p.critical}
                for p in self.GUARDED_PROCESSES
            },
            'services': {
                s: self.check_service_status(s)
                for s in self.PROTECTED_SERVICES
            },
            'recent_actions': len(self.healing_history),
            'network': self.check_network(),
            'disk': self.check_disk_space(),
        }


def main():
    import sys

    healer = SelfHealer()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == 'run':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            healer.run_healing_loop(interval)

        elif cmd == 'status':
            status = healer.status()
            print(json.dumps(status, indent=2, default=str))

        elif cmd == 'check':
            # One-time check
            print("Checking processes...")
            process_results = healer.check_and_heal_processes()
            print(json.dumps(process_results, indent=2))

            print("\nChecking services...")
            service_results = healer.ensure_services_running()
            print(json.dumps(service_results, indent=2))

            print("\nChecking state files...")
            state_results = healer.check_state_files()
            print(json.dumps(state_results, indent=2))

        else:
            print(f"Unknown command: {cmd}")
            print("Commands: run [interval], status, check")
    else:
        print("Self-Healer Status:")
        status = healer.status()
        print(json.dumps(status, indent=2, default=str))


if __name__ == '__main__':
    main()
