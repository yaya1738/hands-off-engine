#!/usr/bin/env python3
"""
MEGA INTEGRATION - Unified Hardware + AI System Coordination

Integrates all autonomous systems into one coherent mega-system:
- Hardware Brain (multi-chain algorithm)
- Scaling Engine (exponential growth)
- Self Healer (process protection)
- Unified System (business decisions)
- Unified AI (identity & directives)

This creates a fully integrated autonomous system that:
1. Hardware decisions flow through unified AI identity
2. Scaling is coordinated with business priorities
3. All actions serve Yair Siegel
4. State is shared across all components
5. Single source of truth for the entire system

Standard: Yair Siegel Master Level Operations - Mega Integration
"""

import json
import os
import sys
import time
import signal
import socket
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
LOG_DIR = BASE_DIR / 'logs'

STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Import unified AI identity
try:
    from ai.unified_ai import (
        MASTER, get_master, get_core, get_directive,
        should_execute, get_priorities, log_action,
        announce_agent, get_system_state, update_system_state,
        check_trading_allowed, send_master_notification,
        run_system_check
    )
    HAS_UNIFIED_AI = True
except ImportError:
    HAS_UNIFIED_AI = False
    MASTER = "Yair Siegel"
    def get_master(): return MASTER
    def should_execute(action, roi=0): return True
    def log_action(agent, action, result): pass
    def send_master_notification(msg, priority="normal"): pass


# ============================================================================
# MEGA SYSTEM STATE
# ============================================================================

@dataclass
class MegaSystemState:
    """Complete system state across all components."""
    timestamp: str
    master: str

    # Hardware state
    total_vcpus: int = 0
    total_ram_gb: float = 0.0
    total_disk_gb: int = 0
    healthy_nodes: int = 0
    total_nodes: int = 0

    # Scaling state
    target_vcpus: int = 0
    target_ram_gb: float = 0.0
    scaling_progress_pct: float = 0.0
    daily_growth_rate: float = 1.1
    evolution_generation: int = 1

    # Financial state
    balance_usd: float = 0.0
    monthly_infra_cost: float = 0.0
    trading_enabled: bool = False

    # Health state
    hardware_health_score: float = 100.0
    system_health_score: float = 100.0
    active_alerts: List[str] = field(default_factory=list)

    # Component status
    components_running: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        d = asdict(self)
        return d


# ============================================================================
# MEGA COORDINATOR
# ============================================================================

class MegaCoordinator:
    """
    The Mega Coordinator - unifies all autonomous systems.

    Architecture:
    ┌─────────────────────────────────────────────────────────────────────┐
    │                     MEGA COORDINATOR                                 │
    │                    Serving: Yair Siegel                              │
    │  ┌───────────────────────────────────────────────────────────────┐  │
    │  │                    UNIFIED AI IDENTITY                         │  │
    │  │   - Master: Yair Siegel                                        │  │
    │  │   - Priorities: Capital, Income, Cost, Automation, Improve     │  │
    │  │   - All decisions flow through unified identity                │  │
    │  └───────────────────────────────────────────────────────────────┘  │
    │                                                                      │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
    │  │   HARDWARE   │  │   SCALING    │  │    SELF      │               │
    │  │    BRAIN     │  │   ENGINE     │  │   HEALER     │               │
    │  │              │  │              │  │              │               │
    │  │  Perceive    │  │  6x Target   │  │  CLI Prot    │               │
    │  │  Analyze     │  │  1.1x Daily  │  │  Process     │               │
    │  │  Decide      │  │  Auto-Scale  │  │  Recovery    │               │
    │  │  Execute     │  │              │  │              │               │
    │  │  Learn       │  │              │  │              │               │
    │  └──────────────┘  └──────────────┘  └──────────────┘               │
    │                                                                      │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
    │  │   UNIFIED    │  │   STATE      │  │   TELEGRAM   │               │
    │  │   SYSTEM     │  │   SYNC       │  │   ALERTS     │               │
    │  │              │  │              │  │              │               │
    │  │  Business    │  │  Multi-Node  │  │  Critical    │               │
    │  │  Decisions   │  │  Consensus   │  │  Notifs      │               │
    │  │  Trading     │  │              │  │              │               │
    │  └──────────────┘  └──────────────┘  └──────────────┘               │
    └─────────────────────────────────────────────────────────────────────┘
    """

    def __init__(self):
        self.hostname = socket.gethostname()
        self.start_time = datetime.utcnow()
        self.master = get_master()

        # Component handles
        self._brain = None
        self._scaler = None
        self._healer = None

        # State
        self.mega_state = MegaSystemState(
            timestamp=datetime.utcnow().isoformat(),
            master=self.master
        )

        # Threading
        self._shutdown = threading.Event()
        self._threads: Dict[str, threading.Thread] = {}

        # Signal protection
        self._setup_signals()

        self._log(f"MegaCoordinator initialized - Serving {self.master}")

        if HAS_UNIFIED_AI:
            announce_agent("MegaCoordinator")

    def _setup_signals(self):
        """Setup signal handlers."""
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, self._shutdown_handler)
        signal.signal(signal.SIGINT, self._shutdown_handler)
        try:
            os.setsid()
        except:
            pass

    def _shutdown_handler(self, signum, frame):
        """Handle shutdown."""
        self._log(f"Shutdown signal {signum} received")
        self._shutdown.set()

    def _log(self, message: str, data: Dict = None, level: str = 'info'):
        """Log with unified format."""
        timestamp = datetime.utcnow().isoformat()
        log_line = f"[{timestamp}] [MEGA] [{level.upper()}] {message}"
        if data:
            log_line += f" | {json.dumps(data)}"

        print(log_line)

        try:
            log_file = LOG_DIR / 'mega_coordinator.log'
            with open(log_file, 'a') as f:
                f.write(log_line + '\n')
        except:
            pass

        # Log to unified AI
        if HAS_UNIFIED_AI:
            log_action("MegaCoordinator", message, level)

    # ========================================================================
    # COMPONENT LOADING
    # ========================================================================

    def _get_brain(self):
        """Get or create hardware brain."""
        if self._brain is None:
            try:
                from autonomous.hardware_brain import HardwareBrain, BrainConfig
                config = BrainConfig(
                    health_check_interval_sec=60,
                    min_cluster_vcpus=20,
                    min_cluster_ram_gb=40.0,
                )
                self._brain = HardwareBrain(config)
            except Exception as e:
                self._log(f"Failed to load HardwareBrain: {e}", level='error')
        return self._brain

    def _get_scaler(self):
        """Get or create scaling engine."""
        if self._scaler is None:
            try:
                from autonomous.scaling_engine import ScalingEngine, ScalingConfig
                config = ScalingConfig(
                    baseline_vcpus=4,
                    baseline_ram_gb=8.0,
                    target_multiplier=6.0,
                    daily_growth_rate=1.1,
                )
                self._scaler = ScalingEngine(config)
            except Exception as e:
                self._log(f"Failed to load ScalingEngine: {e}", level='error')
        return self._scaler

    def _get_healer(self):
        """Get or create self healer."""
        if self._healer is None:
            try:
                from autonomous.self_healer import SelfHealer
                self._healer = SelfHealer()
            except Exception as e:
                self._log(f"Failed to load SelfHealer: {e}", level='error')
        return self._healer

    # ========================================================================
    # UNIFIED STATE GATHERING
    # ========================================================================

    def gather_mega_state(self) -> MegaSystemState:
        """
        Gather complete state from all components.

        This creates a single unified view of the entire system.
        """
        state = MegaSystemState(
            timestamp=datetime.utcnow().isoformat(),
            master=self.master
        )

        # Hardware state from brain
        brain = self._get_brain()
        if brain:
            try:
                cluster = brain.perceive_cluster()
                if cluster:
                    state.total_vcpus = cluster.total_vcpus
                    state.total_ram_gb = cluster.total_ram_gb
                    state.total_disk_gb = cluster.total_disk_gb
                    state.healthy_nodes = cluster.healthy_nodes
                    state.total_nodes = len(cluster.nodes)
                    state.hardware_health_score = 100.0 - (cluster.dead_nodes * 20) - (cluster.degraded_nodes * 10)
                    state.evolution_generation = cluster.evolution_generation
            except Exception as e:
                self._log(f"Error gathering brain state: {e}", level='error')

        # Scaling state
        scaler = self._get_scaler()
        if scaler:
            try:
                scaling_state = scaler.get_scaling_state()
                state.target_vcpus = scaling_state.target_vcpus
                state.target_ram_gb = scaling_state.target_ram_gb
                state.scaling_progress_pct = scaling_state.overall_pct
                state.monthly_infra_cost = scaling_state.current_monthly_cost
            except Exception as e:
                self._log(f"Error gathering scaler state: {e}", level='error')

        # AI system state
        if HAS_UNIFIED_AI:
            try:
                ai_state = get_system_state()
                state.balance_usd = ai_state.get('balance', 0)
                state.trading_enabled = ai_state.get('trading_enabled', False)
            except:
                pass

        # Component status
        state.components_running = {
            'hardware_brain': self._check_component_running('hardware_brain'),
            'scaling_engine': self._check_component_running('scaling_engine'),
            'self_healer': self._check_component_running('self_healer'),
            'state_sync': self._check_component_running('state_sync'),
            'infra_monitor': self._check_component_running('infra_monitor'),
        }

        # Overall health
        running = sum(1 for v in state.components_running.values() if v)
        total = len(state.components_running)
        component_health = (running / total * 50) if total > 0 else 0
        state.system_health_score = component_health + (state.hardware_health_score / 2)

        self.mega_state = state
        self._save_state()

        return state

    def _check_component_running(self, name: str) -> bool:
        """Check if a component is running."""
        import subprocess
        try:
            result = subprocess.run(
                ['pgrep', '-f', name],
                capture_output=True
            )
            return result.returncode == 0
        except:
            return False

    def _save_state(self):
        """Save mega state to file."""
        state_file = STATE_DIR / 'mega_state.json'
        state_file.write_text(json.dumps(self.mega_state.to_dict(), indent=2))

    # ========================================================================
    # UNIFIED DECISION MAKING
    # ========================================================================

    def make_unified_decision(self, action: str, context: Dict) -> Tuple[bool, str]:
        """
        Make a decision using unified AI identity.

        All decisions flow through the unified AI to ensure
        they serve Yair Siegel's interests.
        """
        # Check with unified AI
        if HAS_UNIFIED_AI:
            roi = context.get('estimated_roi', 0)
            if not should_execute(action, roi):
                return False, f"Unified AI declined: {action}"

        # Apply priorities
        priorities = get_priorities() if HAS_UNIFIED_AI else []

        # Capital protection is priority 1
        if 'destroy' in action.lower() or 'delete' in action.lower():
            if 'droplet' in action.lower() or 'server' in action.lower():
                return False, "Capital protection: cannot destroy infrastructure"

        # Cost analysis
        cost = context.get('cost_usd', 0)
        if cost > 0:
            budget = context.get('budget', 500)
            if cost > budget * 0.5:
                # Large cost - needs ROI justification
                if context.get('estimated_roi', 0) <= 0:
                    return False, f"Cost ${cost} exceeds 50% of budget without ROI"

        # Trading protection
        if 'trading' in action.lower():
            allowed, reason = check_trading_allowed(context.get('amount', 0))
            if not allowed:
                return False, reason

        return True, "Approved by unified decision system"

    def notify_master(self, message: str, priority: str = 'normal'):
        """Send notification to Yair Siegel."""
        if HAS_UNIFIED_AI:
            send_master_notification(message, priority)

        self._log(f"NOTIFICATION [{priority}]: {message}")

    # ========================================================================
    # COORDINATION ACTIONS
    # ========================================================================

    def coordinate_scaling(self) -> Dict:
        """
        Coordinate scaling decisions across all components.

        Ensures hardware brain, scaling engine, and unified system
        are aligned on infrastructure decisions.
        """
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'actions': [],
        }

        # Get current state
        state = self.gather_mega_state()

        # Check if scaling needed
        if state.scaling_progress_pct < 100:
            self._log(f"Scaling needed: {state.scaling_progress_pct:.1f}% of target")

            # Get decision from unified AI
            approved, reason = self.make_unified_decision(
                "scale_infrastructure",
                {
                    'current_vcpus': state.total_vcpus,
                    'target_vcpus': state.target_vcpus,
                    'cost_usd': 112,  # Cost of s-8vcpu-16gb-amd
                    'budget': 500,
                    'estimated_roi': 0.1,  # Infrastructure enables trading
                }
            )

            if approved:
                scaler = self._get_scaler()
                if scaler:
                    scale_results = scaler.scale_to_target()
                    result['actions'].extend(scale_results)

                    # Notify if significant change
                    if any(r.get('success') for r in scale_results):
                        self.notify_master(
                            f"Scaled infrastructure: now at {state.total_vcpus} vCPU",
                            'normal'
                        )
            else:
                result['actions'].append({'action': 'scale_blocked', 'reason': reason})

        return result

    def coordinate_health(self) -> Dict:
        """
        Coordinate health checks across all components.
        """
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'health': {},
        }

        state = self.gather_mega_state()

        result['health'] = {
            'hardware': state.hardware_health_score,
            'system': state.system_health_score,
            'nodes': f"{state.healthy_nodes}/{state.total_nodes}",
            'scaling': f"{state.scaling_progress_pct:.1f}%",
        }

        # Alert on critical issues
        if state.hardware_health_score < 50:
            self.notify_master(
                f"CRITICAL: Hardware health at {state.hardware_health_score}%",
                'critical'
            )

        if state.healthy_nodes < 2:
            self.notify_master(
                f"WARNING: Only {state.healthy_nodes} healthy nodes",
                'high'
            )

        return result

    def coordinate_healing(self) -> Dict:
        """
        Coordinate self-healing across all components.
        """
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'healing_actions': [],
        }

        healer = self._get_healer()
        if healer:
            process_results = healer.check_and_heal_processes()
            result['healing_actions'] = process_results.get('actions_taken', [])

        return result

    # ========================================================================
    # MAIN LOOP
    # ========================================================================

    def run_coordination_loop(self, interval_sec: int = 60):
        """
        Run the main coordination loop.

        Continuously coordinates all components to ensure
        optimal system operation.
        """
        self._log("=" * 60)
        self._log(f"MEGA COORDINATOR - Serving {self.master}")
        self._log("=" * 60)

        if HAS_UNIFIED_AI:
            self._log("Unified AI: CONNECTED")
            self._log(f"Priorities: {get_priorities()}")
        else:
            self._log("Unified AI: STANDALONE MODE")

        iteration = 0

        while not self._shutdown.is_set():
            iteration += 1

            try:
                self._log(f"[Iteration {iteration}] Coordinating systems...")

                # Gather state
                state = self.gather_mega_state()

                # Log summary
                self._log(f"  Hardware: {state.total_vcpus} vCPU, {state.total_ram_gb}GB RAM")
                self._log(f"  Scaling: {state.scaling_progress_pct:.1f}% of target")
                self._log(f"  Health: HW {state.hardware_health_score:.0f}%, System {state.system_health_score:.0f}%")

                # Coordinate scaling (every 5 iterations)
                if iteration % 5 == 0:
                    self._log("  Coordinating scaling...")
                    scale_result = self.coordinate_scaling()
                    if scale_result.get('actions'):
                        self._log(f"  Scaling actions: {len(scale_result['actions'])}")

                # Coordinate health (every iteration)
                health_result = self.coordinate_health()

                # Coordinate healing (every 2 iterations)
                if iteration % 2 == 0:
                    heal_result = self.coordinate_healing()
                    if heal_result.get('healing_actions'):
                        self._log(f"  Healing actions: {heal_result['healing_actions']}")

                # Update unified AI state
                if HAS_UNIFIED_AI:
                    update_system_state({
                        'total_vcpus': state.total_vcpus,
                        'total_ram_gb': state.total_ram_gb,
                        'healthy_nodes': state.healthy_nodes,
                        'scaling_progress': state.scaling_progress_pct,
                        'hardware_health': state.hardware_health_score,
                    })

            except Exception as e:
                self._log(f"Coordination error: {e}", level='error')

            self._shutdown.wait(timeout=interval_sec)

        self._log("MegaCoordinator shutting down")

    def status(self) -> Dict:
        """Get current mega system status."""
        state = self.gather_mega_state()
        return {
            'mega_state': state.to_dict(),
            'unified_ai': HAS_UNIFIED_AI,
            'master': self.master,
            'uptime_hours': (datetime.utcnow() - self.start_time).total_seconds() / 3600,
        }


# ============================================================================
# SYSTEMD SERVICE INTEGRATION
# ============================================================================

def create_mega_service():
    """Create systemd service file for mega coordinator."""
    service_content = """[Unit]
Description=Hands-Off Mega Coordinator - Unified System Integration
Documentation=https://github.com/yaya1738/hands-off-engine
After=network.target
Wants=master-controller.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/hands-off-engine
Environment=PYTHONPATH=/root/hands-off-engine
EnvironmentFile=-/root/hands-off-engine/.env

ExecStart=/usr/bin/python3 /root/hands-off-engine/autonomous/mega_integration.py run

Restart=always
RestartSec=30
StartLimitIntervalSec=0

StandardOutput=append:/var/log/hands-off/mega_coordinator.log
StandardError=append:/var/log/hands-off/mega_coordinator.log

TimeoutStopSec=60
KillMode=mixed

[Install]
WantedBy=multi-user.target
"""

    service_path = BASE_DIR / 'scripts' / 'systemd' / 'mega-coordinator.service'
    service_path.parent.mkdir(parents=True, exist_ok=True)
    service_path.write_text(service_content)

    print(f"Created: {service_path}")
    print("To install: sudo cp {service_path} /etc/systemd/system/")
    print("To start: sudo systemctl enable --now mega-coordinator.service")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Mega Integration Coordinator')
    parser.add_argument('command', nargs='?', default='status',
                       choices=['run', 'status', 'create-service', 'coordinate'],
                       help='Command to execute')
    parser.add_argument('--interval', type=int, default=60,
                       help='Coordination interval in seconds')

    args = parser.parse_args()

    coordinator = MegaCoordinator()

    if args.command == 'run':
        coordinator.run_coordination_loop(args.interval)

    elif args.command == 'status':
        status = coordinator.status()
        print(json.dumps(status, indent=2))

    elif args.command == 'create-service':
        create_mega_service()

    elif args.command == 'coordinate':
        # One-time coordination
        print("Gathering state...")
        state = coordinator.gather_mega_state()
        print(json.dumps(state.to_dict(), indent=2))

        print("\nCoordinating scaling...")
        scale = coordinator.coordinate_scaling()
        print(json.dumps(scale, indent=2))

        print("\nCoordinating health...")
        health = coordinator.coordinate_health()
        print(json.dumps(health, indent=2))


if __name__ == '__main__':
    main()
