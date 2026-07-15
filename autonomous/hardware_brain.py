#!/usr/bin/env python3
"""
HARDWARE BRAIN - Autonomous Self-Managing Infrastructure

The central nervous system for all infrastructure operations.
Self-adapting, self-healing, self-evolving.

CORE PRINCIPLES:
1. NEVER turn off, restart, or downgrade any droplet
2. ALWAYS maintain redundancy across multiple nodes
3. PROTECT against CLI session termination
4. DISTRIBUTE work across all available compute
5. EVOLVE and improve algorithms over time
6. SELF-HEAL from any failure state

Standard: Yair Siegel Master Level Operations - Full Autonomy
"""

import json
import os
import sys
import time
import socket
import hashlib
import threading
import subprocess
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import urllib.request
import urllib.error

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
LOG_DIR = Path(__file__).resolve().parent.parent / 'logs'

STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Load DO token
DO_TOKEN = os.environ.get('DO_API_TOKEN', '')
if not DO_TOKEN:
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith('DO_API_TOKEN='):
                DO_TOKEN = line.split('=', 1)[1].strip()


# ============================================================================
# DATA MODELS
# ============================================================================

class NodeRole(Enum):
    PRIMARY = "primary"       # Main coordination node
    COMPUTE = "compute"       # Compute worker
    BACKUP = "backup"         # Hot standby
    EVOLVING = "evolving"     # Currently being upgraded


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    DEAD = "dead"
    UNKNOWN = "unknown"


class AlgorithmPhase(Enum):
    MONITORING = "monitoring"
    ANALYZING = "analyzing"
    DECIDING = "deciding"
    EXECUTING = "executing"
    LEARNING = "learning"


@dataclass
class Node:
    """Represents a compute node in the cluster."""
    id: str
    name: str
    ip: str
    private_ip: str
    vcpus: int
    ram_gb: float
    disk_gb: int
    role: NodeRole
    status: HealthStatus
    last_heartbeat: datetime
    load_1m: float = 0.0
    load_5m: float = 0.0
    load_15m: float = 0.0
    memory_used_pct: float = 0.0
    disk_used_pct: float = 0.0
    active_tasks: int = 0
    errors_last_hour: int = 0
    uptime_hours: float = 0.0

    def to_dict(self) -> Dict:
        d = asdict(self)
        d['role'] = self.role.value
        d['status'] = self.status.value
        d['last_heartbeat'] = self.last_heartbeat.isoformat()
        return d


@dataclass
class ClusterState:
    """Current state of the entire cluster."""
    timestamp: datetime
    total_vcpus: int
    total_ram_gb: float
    total_disk_gb: int
    nodes: List[Node]
    healthy_nodes: int
    degraded_nodes: int
    dead_nodes: int
    primary_node: Optional[str]
    algorithm_phase: AlgorithmPhase
    evolution_generation: int
    last_evolution: Optional[datetime]
    pending_actions: List[Dict]
    completed_actions_24h: int
    errors_24h: int

    def to_dict(self) -> Dict:
        d = {
            'timestamp': self.timestamp.isoformat(),
            'total_vcpus': self.total_vcpus,
            'total_ram_gb': self.total_ram_gb,
            'total_disk_gb': self.total_disk_gb,
            'nodes': [n.to_dict() for n in self.nodes],
            'healthy_nodes': self.healthy_nodes,
            'degraded_nodes': self.degraded_nodes,
            'dead_nodes': self.dead_nodes,
            'primary_node': self.primary_node,
            'algorithm_phase': self.algorithm_phase.value,
            'evolution_generation': self.evolution_generation,
            'last_evolution': self.last_evolution.isoformat() if self.last_evolution else None,
            'pending_actions': self.pending_actions,
            'completed_actions_24h': self.completed_actions_24h,
            'errors_24h': self.errors_24h,
        }
        return d


@dataclass
class BrainConfig:
    """Configuration for the hardware brain."""
    # Timing
    heartbeat_interval_sec: int = 30
    health_check_interval_sec: int = 60
    evolution_check_interval_sec: int = 300
    state_sync_interval_sec: int = 10

    # Thresholds
    min_healthy_nodes: int = 2
    max_node_load: float = 0.8
    max_memory_pct: float = 85.0
    max_disk_pct: float = 90.0

    # Protection
    cli_protection_enabled: bool = True
    auto_recovery_enabled: bool = True
    evolution_enabled: bool = True

    # Cluster minimums (5x original)
    min_cluster_vcpus: int = 20
    min_cluster_ram_gb: float = 40.0


# ============================================================================
# HARDWARE BRAIN - THE CENTRAL NERVOUS SYSTEM
# ============================================================================

class HardwareBrain:
    """
    The autonomous brain that manages all infrastructure.

    Multi-chain algorithm structure:
    1. PERCEPTION CHAIN: Monitor all nodes, gather telemetry
    2. ANALYSIS CHAIN: Detect patterns, anomalies, opportunities
    3. DECISION CHAIN: Determine optimal actions
    4. EXECUTION CHAIN: Safely execute changes
    5. LEARNING CHAIN: Improve from outcomes
    """

    API_BASE = "https://api.digitalocean.com/v2"

    # Protected nodes that MUST NEVER be turned off
    PROTECTED_NODES = {
        'pm-helper': {'id': '524521199', 'role': 'primary'},
        'ho-compute-1': {'id': '533553630', 'role': 'compute'},
        'ho-compute-2': {'id': '533553637', 'role': 'compute'},
    }

    def __init__(self, config: BrainConfig = None):
        self.config = config or BrainConfig()
        self.token = DO_TOKEN
        self.hostname = socket.gethostname()
        self.start_time = datetime.utcnow()

        # State
        self.cluster_state: Optional[ClusterState] = None
        self.evolution_generation = self._load_evolution_generation()
        self.algorithm_phase = AlgorithmPhase.MONITORING

        # Threading
        self._shutdown = threading.Event()
        self._threads: List[threading.Thread] = []

        # CLI Protection
        self._setup_cli_protection()

        # Learning data
        self.action_history: List[Dict] = []
        self.error_history: List[Dict] = []

        self._log("Brain initializing", {
            'hostname': self.hostname,
            'evolution_generation': self.evolution_generation,
            'config': asdict(self.config),
        })

    # ========================================================================
    # CLI PROTECTION - Prevent session termination from killing infrastructure
    # ========================================================================

    def _setup_cli_protection(self):
        """Set up protection against CLI session termination."""
        if not self.config.cli_protection_enabled:
            return

        # Ignore hangup signal (SIGHUP) - prevents SSH disconnect from killing us
        signal.signal(signal.SIGHUP, signal.SIG_IGN)

        # Handle termination gracefully
        signal.signal(signal.SIGTERM, self._graceful_shutdown)
        signal.signal(signal.SIGINT, self._graceful_shutdown)

        # Detach from controlling terminal if possible
        try:
            os.setsid()
        except:
            pass  # May already be session leader

        self._log("CLI protection enabled - immune to SIGHUP")

    def _graceful_shutdown(self, signum, frame):
        """Handle shutdown gracefully - save state but DON'T touch infrastructure."""
        self._log(f"Graceful shutdown initiated (signal {signum})")
        self._shutdown.set()
        self._save_state()
        # DO NOT touch any droplets - just exit cleanly
        sys.exit(0)

    # ========================================================================
    # PERCEPTION CHAIN - Monitor everything
    # ========================================================================

    def _api_request(self, method: str, endpoint: str, data: dict = None) -> Tuple[bool, Any]:
        """Make DO API request."""
        url = f"{self.API_BASE}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

        try:
            body = json.dumps(data).encode() if data else None
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return True, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            return False, {'error': error_body, 'code': e.code}
        except Exception as e:
            return False, {'error': str(e)}

    def perceive_cluster(self) -> ClusterState:
        """
        PERCEPTION CHAIN: Gather complete cluster telemetry.
        """
        self.algorithm_phase = AlgorithmPhase.MONITORING

        # Get all droplets
        ok, data = self._api_request('GET', '/droplets?per_page=100')
        if not ok:
            self._log("Failed to get droplets", data, level='error')
            return self.cluster_state  # Return last known state

        nodes = []
        total_vcpus = 0
        total_ram = 0.0
        total_disk = 0
        healthy = 0
        degraded = 0
        dead = 0

        for d in data.get('droplets', []):
            # Only track hands-off nodes
            if d['name'] not in self.PROTECTED_NODES and 'hands-off' not in str(d.get('tags', [])):
                continue

            # Get IPs
            public_ip = None
            private_ip = None
            for net in d.get('networks', {}).get('v4', []):
                if net['type'] == 'public':
                    public_ip = net['ip_address']
                elif net['type'] == 'private':
                    private_ip = net['ip_address']

            # Determine role
            node_info = self.PROTECTED_NODES.get(d['name'], {})
            role = NodeRole.PRIMARY if node_info.get('role') == 'primary' else NodeRole.COMPUTE

            # Determine health
            status = HealthStatus.HEALTHY if d['status'] == 'active' else HealthStatus.DEAD

            # Check if node is reachable (ping)
            if status == HealthStatus.HEALTHY and public_ip:
                reachable = self._ping_node(public_ip)
                if not reachable:
                    status = HealthStatus.DEGRADED

            node = Node(
                id=str(d['id']),
                name=d['name'],
                ip=public_ip or '',
                private_ip=private_ip or '',
                vcpus=d['vcpus'],
                ram_gb=d['memory'] / 1024,
                disk_gb=d['disk'],
                role=role,
                status=status,
                last_heartbeat=datetime.utcnow(),
            )

            nodes.append(node)
            total_vcpus += node.vcpus
            total_ram += node.ram_gb
            total_disk += node.disk_gb

            if status == HealthStatus.HEALTHY:
                healthy += 1
            elif status == HealthStatus.DEGRADED:
                degraded += 1
            else:
                dead += 1

        # Find primary
        primary = None
        for n in nodes:
            if n.role == NodeRole.PRIMARY and n.status == HealthStatus.HEALTHY:
                primary = n.name
                break

        state = ClusterState(
            timestamp=datetime.utcnow(),
            total_vcpus=total_vcpus,
            total_ram_gb=total_ram,
            total_disk_gb=total_disk,
            nodes=nodes,
            healthy_nodes=healthy,
            degraded_nodes=degraded,
            dead_nodes=dead,
            primary_node=primary,
            algorithm_phase=self.algorithm_phase,
            evolution_generation=self.evolution_generation,
            last_evolution=self._load_last_evolution(),
            pending_actions=self._load_pending_actions(),
            completed_actions_24h=self._count_recent_actions(24),
            errors_24h=self._count_recent_errors(24),
        )

        self.cluster_state = state
        self._save_state()

        return state

    def _ping_node(self, ip: str) -> bool:
        """Ping a node to check reachability."""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', ip],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    # ========================================================================
    # ANALYSIS CHAIN - Detect patterns and problems
    # ========================================================================

    def analyze_cluster(self) -> Dict[str, Any]:
        """
        ANALYSIS CHAIN: Analyze cluster state and detect issues.
        """
        self.algorithm_phase = AlgorithmPhase.ANALYZING

        if not self.cluster_state:
            return {'error': 'No cluster state available'}

        analysis = {
            'timestamp': datetime.utcnow().isoformat(),
            'issues': [],
            'warnings': [],
            'opportunities': [],
            'health_score': 100.0,
        }

        state = self.cluster_state

        # Check minimum resources
        if state.total_vcpus < self.config.min_cluster_vcpus:
            analysis['issues'].append({
                'type': 'insufficient_vcpus',
                'current': state.total_vcpus,
                'required': self.config.min_cluster_vcpus,
                'severity': 'critical',
            })
            analysis['health_score'] -= 30

        if state.total_ram_gb < self.config.min_cluster_ram_gb:
            analysis['issues'].append({
                'type': 'insufficient_ram',
                'current': state.total_ram_gb,
                'required': self.config.min_cluster_ram_gb,
                'severity': 'critical',
            })
            analysis['health_score'] -= 30

        # Check node health
        if state.healthy_nodes < self.config.min_healthy_nodes:
            analysis['issues'].append({
                'type': 'insufficient_healthy_nodes',
                'current': state.healthy_nodes,
                'required': self.config.min_healthy_nodes,
                'severity': 'critical',
            })
            analysis['health_score'] -= 40

        # Check for dead nodes
        if state.dead_nodes > 0:
            analysis['issues'].append({
                'type': 'dead_nodes',
                'count': state.dead_nodes,
                'nodes': [n.name for n in state.nodes if n.status == HealthStatus.DEAD],
                'severity': 'critical',
            })
            analysis['health_score'] -= 20 * state.dead_nodes

        # Check for degraded nodes
        if state.degraded_nodes > 0:
            analysis['warnings'].append({
                'type': 'degraded_nodes',
                'count': state.degraded_nodes,
                'nodes': [n.name for n in state.nodes if n.status == HealthStatus.DEGRADED],
            })
            analysis['health_score'] -= 10 * state.degraded_nodes

        # Check primary node
        if not state.primary_node:
            analysis['issues'].append({
                'type': 'no_primary_node',
                'severity': 'critical',
            })
            analysis['health_score'] -= 50

        # Detect opportunities
        if state.healthy_nodes >= 3 and state.total_vcpus >= 20:
            analysis['opportunities'].append({
                'type': 'ready_for_distributed_compute',
                'nodes': state.healthy_nodes,
            })

        # Clamp health score
        analysis['health_score'] = max(0, min(100, analysis['health_score']))

        return analysis

    # ========================================================================
    # DECISION CHAIN - Determine optimal actions
    # ========================================================================

    def decide_actions(self, analysis: Dict) -> List[Dict]:
        """
        DECISION CHAIN: Determine what actions to take based on analysis.

        CRITICAL RULES:
        - NEVER power off any droplet
        - NEVER restart any droplet
        - NEVER downgrade any droplet
        - Only ADD resources, RECOVER failed nodes, or IMPROVE efficiency
        """
        self.algorithm_phase = AlgorithmPhase.DECIDING

        actions = []

        # Handle critical issues
        for issue in analysis.get('issues', []):
            if issue['type'] == 'insufficient_vcpus' or issue['type'] == 'insufficient_ram':
                actions.append({
                    'action': 'add_compute_node',
                    'reason': f"Cluster below minimum: {issue['type']}",
                    'priority': 'high',
                    'params': {
                        'size': 's-8vcpu-16gb-amd',
                        'name': f"ho-compute-{len(self.cluster_state.nodes) + 1}",
                    }
                })

            elif issue['type'] == 'dead_nodes':
                # Don't try to restart - create replacement
                for node_name in issue.get('nodes', []):
                    actions.append({
                        'action': 'investigate_node',
                        'reason': f"Node {node_name} appears dead",
                        'priority': 'critical',
                        'params': {'node': node_name},
                    })

            elif issue['type'] == 'no_primary_node':
                # Elect new primary from healthy nodes
                actions.append({
                    'action': 'elect_primary',
                    'reason': 'No primary node available',
                    'priority': 'critical',
                })

        # Handle warnings
        for warning in analysis.get('warnings', []):
            if warning['type'] == 'degraded_nodes':
                for node_name in warning.get('nodes', []):
                    actions.append({
                        'action': 'diagnose_node',
                        'reason': f"Node {node_name} is degraded",
                        'priority': 'medium',
                        'params': {'node': node_name},
                    })

        return actions

    # ========================================================================
    # EXECUTION CHAIN - Safely execute actions
    # ========================================================================

    def execute_actions(self, actions: List[Dict]) -> List[Dict]:
        """
        EXECUTION CHAIN: Execute decided actions safely.

        SAFETY RULES:
        - Log everything
        - Validate before executing
        - Never execute destructive actions
        - Roll back on failure if possible
        """
        self.algorithm_phase = AlgorithmPhase.EXECUTING

        results = []

        for action in actions:
            action_type = action.get('action')
            params = action.get('params', {})

            self._log(f"Executing action: {action_type}", action)

            try:
                if action_type == 'add_compute_node':
                    result = self._execute_add_node(params)
                elif action_type == 'investigate_node':
                    result = self._execute_investigate_node(params)
                elif action_type == 'diagnose_node':
                    result = self._execute_diagnose_node(params)
                elif action_type == 'elect_primary':
                    result = self._execute_elect_primary()
                else:
                    result = {'success': False, 'error': f'Unknown action: {action_type}'}

                results.append({
                    'action': action,
                    'result': result,
                    'timestamp': datetime.utcnow().isoformat(),
                })

                # Record for learning
                self.action_history.append({
                    'action': action,
                    'result': result,
                    'timestamp': datetime.utcnow().isoformat(),
                })

            except Exception as e:
                error_result = {'success': False, 'error': str(e)}
                results.append({
                    'action': action,
                    'result': error_result,
                    'timestamp': datetime.utcnow().isoformat(),
                })
                self.error_history.append({
                    'action': action,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat(),
                })

        return results

    def _execute_add_node(self, params: Dict) -> Dict:
        """Add a new compute node."""
        # Get SSH keys
        ok, keys_data = self._api_request('GET', '/account/keys')
        ssh_keys = [k['id'] for k in keys_data.get('ssh_keys', [])] if ok else []

        from finance.autonomous_cost_gate import get_cost_gate

        gate = get_cost_gate()
        approved, reason = gate.pre_scale_cost_check(
            size=params.get('size', 's-8vcpu-16gb-amd'),
            hours=24
        )

        if not approved:
            return {
                'success': False,
                'blocked': True,
                'blocked_by_cost_gate': True,
                'reason': reason,
            }

        droplet_data = {
            'name': params.get('name', f'ho-compute-{int(time.time())}'),
            'region': 'nyc1',
            'size': params.get('size', 's-8vcpu-16gb-amd'),
            'image': 'ubuntu-22-04-x64',
            'ssh_keys': ssh_keys,
            'backups': True,
            'monitoring': True,
            'tags': ['hands-off-engine', 'compute-node', 'auto-provisioned'],
        }

        ok, result = self._api_request('POST', '/droplets', droplet_data)

        if ok:
            droplet = result.get('droplet', {})
            return {
                'success': True,
                'droplet_id': droplet.get('id'),
                'name': droplet.get('name'),
            }

        return {'success': False, 'error': result.get('error', 'Unknown error')}

    def _execute_investigate_node(self, params: Dict) -> Dict:
        """Investigate a potentially dead node."""
        node_name = params.get('node')

        # Find the node
        node = None
        for n in self.cluster_state.nodes:
            if n.name == node_name:
                node = n
                break

        if not node:
            return {'success': False, 'error': f'Node {node_name} not found'}

        # Try to ping it
        reachable = self._ping_node(node.ip) if node.ip else False

        # Check DO status
        ok, data = self._api_request('GET', f'/droplets/{node.id}')
        do_status = data.get('droplet', {}).get('status', 'unknown') if ok else 'api_error'

        return {
            'success': True,
            'node': node_name,
            'reachable': reachable,
            'do_status': do_status,
            'recommendation': 'wait_and_monitor' if do_status == 'active' else 'escalate',
        }

    def _execute_diagnose_node(self, params: Dict) -> Dict:
        """Diagnose a degraded node."""
        node_name = params.get('node')

        # Similar to investigate but more detailed
        return self._execute_investigate_node(params)

    def _execute_elect_primary(self) -> Dict:
        """Elect a new primary node from healthy nodes."""
        if not self.cluster_state:
            return {'success': False, 'error': 'No cluster state'}

        # Find best candidate
        candidates = [n for n in self.cluster_state.nodes
                     if n.status == HealthStatus.HEALTHY]

        if not candidates:
            return {'success': False, 'error': 'No healthy nodes available'}

        # Prefer pm-helper, then largest node
        candidates.sort(key=lambda n: (n.name == 'pm-helper', n.vcpus), reverse=True)
        new_primary = candidates[0]

        # Update role
        new_primary.role = NodeRole.PRIMARY

        return {
            'success': True,
            'new_primary': new_primary.name,
        }

    # ========================================================================
    # LEARNING CHAIN - Improve over time
    # ========================================================================

    def learn_from_outcomes(self):
        """
        LEARNING CHAIN: Analyze past actions and improve decision making.
        """
        self.algorithm_phase = AlgorithmPhase.LEARNING

        # Analyze action success rates
        if len(self.action_history) < 10:
            return  # Not enough data

        success_rate = sum(1 for a in self.action_history if a['result'].get('success', False)) / len(self.action_history)

        # Adjust thresholds based on outcomes
        if success_rate < 0.7:
            # Be more conservative
            self.config.health_check_interval_sec = min(120, self.config.health_check_interval_sec + 10)
        elif success_rate > 0.9:
            # Can be more aggressive
            self.config.health_check_interval_sec = max(30, self.config.health_check_interval_sec - 5)

        # Increment evolution generation
        self.evolution_generation += 1
        self._save_evolution_generation()

        self._log("Learning complete", {
            'success_rate': success_rate,
            'new_generation': self.evolution_generation,
        })

    # ========================================================================
    # MAIN LOOP - The beating heart
    # ========================================================================

    def run_forever(self):
        """
        Run the brain indefinitely.

        Multi-chain algorithm loop:
        1. Perceive -> 2. Analyze -> 3. Decide -> 4. Execute -> 5. Learn
        """
        self._log("Brain starting main loop")

        iteration = 0
        last_perception = datetime.min
        last_analysis = datetime.min
        last_evolution = datetime.min

        while not self._shutdown.is_set():
            try:
                now = datetime.utcnow()
                iteration += 1

                # PERCEPTION: Gather telemetry
                if (now - last_perception).seconds >= self.config.health_check_interval_sec:
                    self._log(f"[Iteration {iteration}] PERCEPTION CHAIN")
                    self.perceive_cluster()
                    last_perception = now

                # ANALYSIS: Detect issues
                if self.cluster_state and (now - last_analysis).seconds >= self.config.health_check_interval_sec:
                    self._log(f"[Iteration {iteration}] ANALYSIS CHAIN")
                    analysis = self.analyze_cluster()

                    # Log health
                    self._log(f"Cluster health: {analysis.get('health_score', 0)}%", {
                        'issues': len(analysis.get('issues', [])),
                        'warnings': len(analysis.get('warnings', [])),
                    })

                    # DECISION: Determine actions
                    if analysis.get('issues') or analysis.get('warnings'):
                        self._log(f"[Iteration {iteration}] DECISION CHAIN")
                        actions = self.decide_actions(analysis)

                        if actions:
                            # EXECUTION: Execute actions
                            self._log(f"[Iteration {iteration}] EXECUTION CHAIN - {len(actions)} actions")
                            results = self.execute_actions(actions)

                            for r in results:
                                success = r['result'].get('success', False)
                                self._log(f"Action result: {r['action']['action']} -> {'SUCCESS' if success else 'FAILED'}")

                    last_analysis = now

                # LEARNING: Evolve over time
                if self.config.evolution_enabled and (now - last_evolution).seconds >= self.config.evolution_check_interval_sec:
                    self._log(f"[Iteration {iteration}] LEARNING CHAIN")
                    self.learn_from_outcomes()
                    last_evolution = now

                # Sleep before next iteration
                time.sleep(self.config.state_sync_interval_sec)

            except Exception as e:
                self._log(f"Error in main loop: {e}", level='error')
                self.error_history.append({
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat(),
                })
                time.sleep(30)  # Back off on errors

    # ========================================================================
    # PERSISTENCE
    # ========================================================================

    def _save_state(self):
        """Save current state to disk."""
        if self.cluster_state:
            state_file = STATE_DIR / 'brain_state.json'
            state_file.write_text(json.dumps(self.cluster_state.to_dict(), indent=2))

    def _load_evolution_generation(self) -> int:
        """Load evolution generation from disk."""
        gen_file = STATE_DIR / 'evolution_generation.txt'
        if gen_file.exists():
            return int(gen_file.read_text().strip())
        return 1

    def _save_evolution_generation(self):
        """Save evolution generation to disk."""
        gen_file = STATE_DIR / 'evolution_generation.txt'
        gen_file.write_text(str(self.evolution_generation))

    def _load_last_evolution(self) -> Optional[datetime]:
        """Load last evolution timestamp."""
        evo_file = STATE_DIR / 'last_evolution.txt'
        if evo_file.exists():
            return datetime.fromisoformat(evo_file.read_text().strip())
        return None

    def _load_pending_actions(self) -> List[Dict]:
        """Load pending actions."""
        actions_file = STATE_DIR / 'pending_actions.json'
        if actions_file.exists():
            return json.loads(actions_file.read_text())
        return []

    def _count_recent_actions(self, hours: int) -> int:
        """Count actions in the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return sum(1 for a in self.action_history
                  if datetime.fromisoformat(a['timestamp']) > cutoff)

    def _count_recent_errors(self, hours: int) -> int:
        """Count errors in the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return sum(1 for e in self.error_history
                  if datetime.fromisoformat(e['timestamp']) > cutoff)

    def _log(self, message: str, data: Dict = None, level: str = 'info'):
        """Log a message."""
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"
        if data:
            log_entry += f" | {json.dumps(data)}"

        print(log_entry)

        # Also write to log file
        log_file = LOG_DIR / 'brain.log'
        with open(log_file, 'a') as f:
            f.write(log_entry + '\n')


# ============================================================================
# DISTRIBUTED EXECUTOR - Run tasks across all nodes
# ============================================================================

class DistributedExecutor:
    """
    Execute tasks across all available compute nodes.
    Distributes load and handles failures.
    """

    def __init__(self, brain: HardwareBrain):
        self.brain = brain

    def get_available_nodes(self) -> List[Node]:
        """Get all healthy nodes available for work."""
        if not self.brain.cluster_state:
            return []
        return [n for n in self.brain.cluster_state.nodes
                if n.status == HealthStatus.HEALTHY]

    def distribute_task(self, task: str, nodes: List[Node] = None) -> Dict:
        """
        Distribute a task across nodes.
        Returns results from all nodes.
        """
        if nodes is None:
            nodes = self.get_available_nodes()

        if not nodes:
            return {'error': 'No available nodes'}

        results = {}
        for node in nodes:
            try:
                # Execute via SSH
                result = subprocess.run(
                    ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10',
                     f'root@{node.ip}', task],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                results[node.name] = {
                    'success': result.returncode == 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                }
            except Exception as e:
                results[node.name] = {
                    'success': False,
                    'error': str(e),
                }

        return results

    def run_on_best_node(self, task: str) -> Dict:
        """Run a task on the best available node (lowest load)."""
        nodes = self.get_available_nodes()
        if not nodes:
            return {'error': 'No available nodes'}

        # Sort by load (lowest first)
        nodes.sort(key=lambda n: n.load_1m)
        best = nodes[0]

        try:
            result = subprocess.run(
                ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10',
                 f'root@{best.ip}', task],
                capture_output=True,
                text=True,
                timeout=300
            )
            return {
                'node': best.name,
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
            }
        except Exception as e:
            return {
                'node': best.name,
                'success': False,
                'error': str(e),
            }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the Hardware Brain."""
    import argparse

    parser = argparse.ArgumentParser(description='Autonomous Hardware Brain')
    parser.add_argument('command', nargs='?', default='run',
                       choices=['run', 'status', 'analyze', 'test'],
                       help='Command to execute')

    args = parser.parse_args()

    brain = HardwareBrain()

    if args.command == 'run':
        print("Starting Hardware Brain - Full Autonomous Mode")
        print("Press Ctrl+C to gracefully shutdown")
        print("-" * 50)
        brain.run_forever()

    elif args.command == 'status':
        state = brain.perceive_cluster()
        print(json.dumps(state.to_dict(), indent=2))

    elif args.command == 'analyze':
        brain.perceive_cluster()
        analysis = brain.analyze_cluster()
        print(json.dumps(analysis, indent=2))

    elif args.command == 'test':
        print("Testing brain components...")

        print("\n1. Perceiving cluster...")
        state = brain.perceive_cluster()
        print(f"   Found {len(state.nodes)} nodes, {state.total_vcpus} vCPUs, {state.total_ram_gb}GB RAM")

        print("\n2. Analyzing cluster...")
        analysis = brain.analyze_cluster()
        print(f"   Health score: {analysis['health_score']}%")
        print(f"   Issues: {len(analysis['issues'])}, Warnings: {len(analysis['warnings'])}")

        print("\n3. Deciding actions...")
        actions = brain.decide_actions(analysis)
        print(f"   Determined {len(actions)} actions")

        print("\n4. Brain test complete!")


if __name__ == '__main__':
    main()
