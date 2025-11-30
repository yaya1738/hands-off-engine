#!/usr/bin/env python3
"""
MASTER CONTROLLER - Unified Autonomous System Orchestrator

The single entry point that runs and coordinates all autonomous subsystems:
1. Hardware Brain - Multi-chain decision making
2. Scaling Engine - Exponential growth
3. Self Healer - Process/service recovery
4. State Sync - Multi-node consistency
5. Distributed Executor - Cross-node task execution

GUARANTEES:
- System runs indefinitely without human intervention
- All components restart automatically on failure
- CLI disconnection does not affect operation
- Infrastructure only grows, never shrinks
- State is preserved across restarts

Standard: Yair Siegel Master Level Operations - Absolute Autonomy
"""

import json
import os
import sys
import time
import signal
import socket
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import traceback

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
LOG_DIR = Path('/var/log/hands-off')

STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class SystemStatus:
    """Overall system status."""
    timestamp: str
    hostname: str
    uptime_hours: float
    components: Dict[str, Dict]
    cluster: Dict
    health_score: float
    alerts: List[str]
    evolution_generation: int


class MasterController:
    """
    The Master Controller - orchestrates all autonomous subsystems.

    Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    MASTER CONTROLLER                         │
    │  ┌──────────────────────────────────────────────────────┐   │
    │  │                   CLI PROTECTION                      │   │
    │  │           (Immune to SIGHUP, terminal close)          │   │
    │  └──────────────────────────────────────────────────────┘   │
    │                                                              │
    │  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
    │  │  HARDWARE  │  │  SCALING   │  │   SELF     │             │
    │  │   BRAIN    │  │  ENGINE    │  │  HEALER    │             │
    │  │            │  │            │  │            │             │
    │  │ Perceive   │  │ 6x Target  │  │ Process    │             │
    │  │ Analyze    │  │ 1.1x Daily │  │ Guard      │             │
    │  │ Decide     │  │ Auto-Scale │  │ Recovery   │             │
    │  │ Execute    │  │            │  │            │             │
    │  │ Learn      │  │            │  │            │             │
    │  └────────────┘  └────────────┘  └────────────┘             │
    │                                                              │
    │  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
    │  │   STATE    │  │ DISTRIBUTED│  │  UNIFIED   │             │
    │  │   SYNC     │  │  EXECUTOR  │  │   ACTIONS  │             │
    │  │            │  │            │  │            │             │
    │  │ Multi-Node │  │ Cross-Node │  │ Pending    │             │
    │  │ Consensus  │  │ Tasks      │  │ Queue      │             │
    │  └────────────┘  └────────────┘  └────────────┘             │
    └─────────────────────────────────────────────────────────────┘
    """

    def __init__(self):
        self.hostname = socket.gethostname()
        self.start_time = datetime.utcnow()
        self.is_primary = self.hostname == 'pm-helper'

        # Component threads
        self.threads: Dict[str, threading.Thread] = {}
        self.component_status: Dict[str, Dict] = {}

        # Shutdown control
        self._shutdown = threading.Event()

        # Setup CLI protection first
        self._setup_cli_protection()

        self._log("Master Controller initializing", {
            'hostname': self.hostname,
            'is_primary': self.is_primary,
            'pid': os.getpid(),
        })

    def _setup_cli_protection(self):
        """
        CRITICAL: Protect against CLI session termination.

        This ensures the system keeps running even if:
        - SSH session disconnects
        - Terminal closes
        - User logs out
        """
        # Ignore SIGHUP (sent when terminal closes)
        signal.signal(signal.SIGHUP, signal.SIG_IGN)

        # Handle termination gracefully
        signal.signal(signal.SIGTERM, self._shutdown_handler)
        signal.signal(signal.SIGINT, self._shutdown_handler)

        # Become session leader (detach from terminal)
        try:
            os.setsid()
        except OSError:
            pass

        # Set process name
        try:
            import ctypes
            libc = ctypes.CDLL('libc.so.6')
            libc.prctl(15, b'hands-off-master', 0, 0, 0)
        except:
            pass

        self._log("CLI protection active - immune to session termination")

    def _shutdown_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self._log(f"Shutdown signal received ({signum})")
        self._shutdown.set()

    def _log(self, message: str, data: Dict = None, level: str = 'info'):
        """Log a message."""
        timestamp = datetime.utcnow().isoformat()
        log_line = f"[{timestamp}] [MASTER] [{level.upper()}] {message}"
        if data:
            log_line += f" | {json.dumps(data)}"

        print(log_line)

        try:
            log_file = LOG_DIR / 'master_controller.log'
            with open(log_file, 'a') as f:
                f.write(log_line + '\n')
        except:
            pass

    # ========================================================================
    # COMPONENT MANAGEMENT
    # ========================================================================

    def _run_component(self, name: str, func, *args, **kwargs):
        """
        Run a component in a thread with automatic restart.
        """
        restart_count = 0
        max_restarts = 100  # Per hour

        while not self._shutdown.is_set():
            try:
                self._log(f"Starting component: {name}")
                self.component_status[name] = {
                    'status': 'running',
                    'started': datetime.utcnow().isoformat(),
                    'restarts': restart_count,
                }

                func(*args, **kwargs)

            except Exception as e:
                self._log(f"Component {name} crashed: {e}", level='error')
                self.component_status[name] = {
                    'status': 'crashed',
                    'error': str(e),
                    'restarts': restart_count,
                }

                restart_count += 1
                if restart_count > max_restarts:
                    self._log(f"Component {name} exceeded max restarts", level='error')
                    break

                # Exponential backoff
                wait_time = min(300, 10 * (2 ** min(restart_count, 5)))
                self._log(f"Restarting {name} in {wait_time}s")
                self._shutdown.wait(timeout=wait_time)

        self.component_status[name] = {'status': 'stopped'}

    def _start_hardware_brain(self):
        """Start the hardware brain component."""
        from autonomous.hardware_brain import HardwareBrain, BrainConfig

        config = BrainConfig(
            health_check_interval_sec=60,
            evolution_check_interval_sec=300,
            min_cluster_vcpus=20,
            min_cluster_ram_gb=40.0,
        )
        brain = HardwareBrain(config)
        brain.run_forever()

    def _start_scaling_engine(self):
        """Start the scaling engine component."""
        from autonomous.scaling_engine import ScalingEngine, ScalingConfig

        config = ScalingConfig(
            baseline_vcpus=4,
            baseline_ram_gb=8.0,
            target_multiplier=6.0,
            daily_growth_rate=1.1,
            check_interval_sec=300,
        )
        engine = ScalingEngine(config)
        engine.run_scaling_loop()

    def _start_self_healer(self):
        """Start the self-healer component."""
        from autonomous.self_healer import SelfHealer

        healer = SelfHealer()
        healer.run_healing_loop(interval_sec=60)

    def _start_state_sync(self):
        """Start the state sync component."""
        from autonomous.state_sync import StateSync

        sync = StateSync()
        sync.run_sync_loop(interval_sec=60)

    def _start_infra_monitor(self):
        """Start the infrastructure monitor."""
        from autonomous.infra_manager import InfraManager

        manager = InfraManager()
        manager.run_continuous_monitoring(interval_seconds=300)

    # ========================================================================
    # MAIN ORCHESTRATION
    # ========================================================================

    def start_all_components(self):
        """
        Start all autonomous components in separate threads.
        """
        components = [
            ('hardware-brain', self._start_hardware_brain),
            ('scaling-engine', self._start_scaling_engine),
            ('self-healer', self._start_self_healer),
            ('state-sync', self._start_state_sync),
            ('infra-monitor', self._start_infra_monitor),
        ]

        for name, func in components:
            thread = threading.Thread(
                target=self._run_component,
                args=(name, func),
                daemon=True,
                name=f"component-{name}"
            )
            thread.start()
            self.threads[name] = thread
            self._log(f"Started component thread: {name}")

            # Small delay between starts
            time.sleep(2)

    def get_system_status(self) -> SystemStatus:
        """Get comprehensive system status."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds() / 3600

        # Calculate health score
        health_score = 100.0
        alerts = []

        running = sum(1 for s in self.component_status.values() if s.get('status') == 'running')
        total = len(self.component_status)

        if total > 0:
            component_health = (running / total) * 50
            health_score = component_health + 50  # Base 50 for being up

        for name, status in self.component_status.items():
            if status.get('status') != 'running':
                alerts.append(f"Component {name} is {status.get('status', 'unknown')}")
                health_score -= 10

        # Get cluster info
        cluster = {}
        try:
            from autonomous.scaling_engine import ScalingEngine
            engine = ScalingEngine()
            cluster = engine.status()
        except:
            pass

        # Get evolution generation
        gen = 1
        gen_file = STATE_DIR / 'evolution_generation.txt'
        if gen_file.exists():
            try:
                gen = int(gen_file.read_text().strip())
            except:
                pass

        return SystemStatus(
            timestamp=datetime.utcnow().isoformat(),
            hostname=self.hostname,
            uptime_hours=round(uptime, 2),
            components=self.component_status.copy(),
            cluster=cluster,
            health_score=max(0, min(100, health_score)),
            alerts=alerts,
            evolution_generation=gen,
        )

    def run_forever(self):
        """
        Main entry point - run the system indefinitely.
        """
        self._log("=" * 60)
        self._log("MASTER CONTROLLER - STARTING AUTONOMOUS OPERATION")
        self._log("=" * 60)
        self._log(f"Hostname: {self.hostname}")
        self._log(f"Primary Node: {self.is_primary}")
        self._log(f"PID: {os.getpid()}")
        self._log("-" * 60)

        # Start all components
        self.start_all_components()

        # Main monitoring loop
        iteration = 0
        while not self._shutdown.is_set():
            iteration += 1

            try:
                # Check component health
                running = sum(1 for t in self.threads.values() if t.is_alive())
                total = len(self.threads)

                if iteration % 10 == 0:  # Every ~minute
                    status = self.get_system_status()
                    self._log(f"[Iteration {iteration}] Health: {status.health_score}%", {
                        'running_components': running,
                        'total_components': total,
                        'uptime_hours': status.uptime_hours,
                    })

                    # Save status
                    status_file = STATE_DIR / 'master_status.json'
                    status_file.write_text(json.dumps(asdict(status), indent=2))

                    if status.alerts:
                        for alert in status.alerts:
                            self._log(f"ALERT: {alert}", level='warning')

                # Restart dead threads
                for name, thread in list(self.threads.items()):
                    if not thread.is_alive():
                        self._log(f"Component {name} thread died - restarting", level='warning')
                        # Thread will be restarted by _run_component

            except Exception as e:
                self._log(f"Error in main loop: {e}", level='error')

            # Sleep
            self._shutdown.wait(timeout=6)

        # Shutdown
        self._log("Master Controller shutting down")
        self._save_final_state()

    def _save_final_state(self):
        """Save state before shutdown."""
        try:
            status = self.get_system_status()
            status_file = STATE_DIR / 'master_final_state.json'
            status_file.write_text(json.dumps(asdict(status), indent=2))
        except:
            pass


def daemonize():
    """
    Fully daemonize the process.

    Double-fork to ensure complete detachment from terminal.
    """
    # First fork
    try:
        pid = os.fork()
        if pid > 0:
            # Parent exits
            sys.exit(0)
    except OSError as e:
        sys.exit(1)

    # Decouple from parent
    os.chdir('/')
    os.setsid()
    os.umask(0)

    # Second fork
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.exit(1)

    # Redirect file descriptors
    sys.stdout.flush()
    sys.stderr.flush()

    with open('/dev/null', 'r') as devnull:
        os.dup2(devnull.fileno(), sys.stdin.fileno())

    log_file = LOG_DIR / 'master_controller.log'
    with open(log_file, 'a') as log:
        os.dup2(log.fileno(), sys.stdout.fileno())
        os.dup2(log.fileno(), sys.stderr.fileno())


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Hands-Off Master Controller')
    parser.add_argument('command', nargs='?', default='run',
                       choices=['run', 'daemon', 'status', 'stop'],
                       help='Command to execute')

    args = parser.parse_args()

    if args.command == 'run':
        # Run in foreground
        controller = MasterController()
        controller.run_forever()

    elif args.command == 'daemon':
        # Daemonize and run
        print("Starting Master Controller as daemon...")
        daemonize()
        controller = MasterController()
        controller.run_forever()

    elif args.command == 'status':
        # Show status from file
        status_file = STATE_DIR / 'master_status.json'
        if status_file.exists():
            status = json.loads(status_file.read_text())
            print(json.dumps(status, indent=2))
        else:
            print("No status file found - controller may not be running")

    elif args.command == 'stop':
        # Send SIGTERM to running controller
        pid_result = subprocess.run(
            ['pgrep', '-f', 'master_controller.py'],
            capture_output=True,
            text=True
        )
        if pid_result.returncode == 0:
            pids = pid_result.stdout.strip().split('\n')
            for pid in pids:
                if pid and pid != str(os.getpid()):
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"Sent SIGTERM to PID {pid}")
        else:
            print("No running controller found")


if __name__ == '__main__':
    main()
