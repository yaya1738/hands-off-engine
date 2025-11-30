#!/usr/bin/env python3
"""
AGGRESSIVE SCALING ENGINE - Exponential Hardware Growth

Manages exponential hardware growth with:
- 6x initial target multiplier
- 1.1x daily compound growth
- Never-stop expansion algorithm
- Multi-node parallel provisioning

RULES:
- NEVER turn off any droplet
- NEVER downgrade
- ALWAYS add capacity
- Respect account tier limits (request increase when blocked)

Standard: Yair Siegel Master Level Operations - Infinite Scale
"""

import json
import os
import time
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import urllib.request
import urllib.error

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Load DO token
DO_TOKEN = os.environ.get('DO_API_TOKEN', '')
if not DO_TOKEN:
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith('DO_API_TOKEN='):
                DO_TOKEN = line.split('=', 1)[1].strip()


@dataclass
class ScalingConfig:
    """Scaling configuration."""
    # Initial baseline (what we started with)
    baseline_vcpus: int = 4
    baseline_ram_gb: float = 8.0

    # Current target multiplier (6x baseline)
    target_multiplier: float = 6.0

    # Daily compound growth rate (1.1x = 10% daily)
    daily_growth_rate: float = 1.1

    # Maximum resources (account limits or budget)
    max_vcpus: int = 500
    max_ram_gb: float = 1000.0
    max_monthly_cost: float = 5000.0

    # Provisioning
    preferred_size: str = 's-8vcpu-16gb-amd'
    preferred_region: str = 'nyc1'
    max_parallel_provisions: int = 3

    # Timing
    check_interval_sec: int = 300
    provision_cooldown_sec: int = 600


@dataclass
class ScalingState:
    """Current scaling state."""
    # Tracking
    start_date: str
    current_date: str
    days_running: int

    # Resources
    current_vcpus: int
    current_ram_gb: float
    current_nodes: int
    current_monthly_cost: float

    # Targets (exponentially growing)
    target_vcpus: int
    target_ram_gb: float
    target_multiplier: float

    # Progress
    vcpu_pct: float
    ram_pct: float
    overall_pct: float

    # Actions
    nodes_to_add: int
    last_provision: Optional[str]
    provisions_today: int
    blocked_by_tier: bool
    tier_increase_requested: bool

    def to_dict(self) -> Dict:
        return asdict(self)


class ScalingEngine:
    """
    Aggressive scaling engine with exponential growth.

    Growth formula: target = baseline * initial_multiplier * (daily_rate ^ days)

    Example with baseline=4vCPU, multiplier=6x, rate=1.1x:
    - Day 0: 4 * 6 * 1.0 = 24 vCPU target
    - Day 1: 4 * 6 * 1.1 = 26.4 vCPU target
    - Day 7: 4 * 6 * 1.95 = 47 vCPU target
    - Day 30: 4 * 6 * 17.4 = 418 vCPU target
    """

    API_BASE = "https://api.digitalocean.com/v2"

    # Available instance sizes (sorted by value)
    INSTANCE_SIZES = {
        's-2vcpu-4gb': {'vcpus': 2, 'ram_gb': 4, 'cost': 24},
        's-4vcpu-8gb': {'vcpus': 4, 'ram_gb': 8, 'cost': 48},
        's-8vcpu-16gb-amd': {'vcpus': 8, 'ram_gb': 16, 'cost': 112},
        # Larger sizes (may require tier increase)
        's-8vcpu-32gb-amd': {'vcpus': 8, 'ram_gb': 32, 'cost': 168},
        'c2-16vcpu-32gb': {'vcpus': 16, 'ram_gb': 32, 'cost': 224},
        'c2-32vcpu-64gb': {'vcpus': 32, 'ram_gb': 64, 'cost': 448},
    }

    def __init__(self, config: ScalingConfig = None):
        self.config = config or ScalingConfig()
        self.token = DO_TOKEN
        self.state_file = STATE_DIR / 'scaling_state.json'
        self.start_date = self._load_start_date()
        self.blocked_sizes: set = set()

    def _api_request(self, method: str, endpoint: str, data: dict = None) -> Tuple[bool, dict]:
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
            try:
                error_data = json.loads(error_body)
            except:
                error_data = {'message': error_body}
            return False, {'error': error_data, 'code': e.code}
        except Exception as e:
            return False, {'error': str(e)}

    def _load_start_date(self) -> datetime:
        """Load or initialize start date."""
        date_file = STATE_DIR / 'scaling_start_date.txt'
        if date_file.exists():
            return datetime.fromisoformat(date_file.read_text().strip())

        # First run - set start date to now
        start = datetime.utcnow()
        date_file.write_text(start.isoformat())
        return start

    def calculate_target(self) -> Tuple[int, float, float]:
        """
        Calculate current target based on exponential growth.

        Returns: (target_vcpus, target_ram_gb, current_multiplier)
        """
        days_running = (datetime.utcnow() - self.start_date).days

        # Exponential growth: base * initial_mult * (rate ^ days)
        current_multiplier = self.config.target_multiplier * (self.config.daily_growth_rate ** days_running)

        target_vcpus = int(self.config.baseline_vcpus * current_multiplier)
        target_ram_gb = self.config.baseline_ram_gb * current_multiplier

        # Clamp to max
        target_vcpus = min(target_vcpus, self.config.max_vcpus)
        target_ram_gb = min(target_ram_gb, self.config.max_ram_gb)

        return target_vcpus, target_ram_gb, current_multiplier

    def get_current_resources(self) -> Tuple[int, float, int, float, List[Dict]]:
        """
        Get current cluster resources.

        Returns: (vcpus, ram_gb, node_count, monthly_cost, nodes)
        """
        ok, data = self._api_request('GET', '/droplets?per_page=100')
        if not ok:
            return 0, 0.0, 0, 0.0, []

        vcpus = 0
        ram_gb = 0.0
        monthly_cost = 0.0
        nodes = []

        for d in data.get('droplets', []):
            # Only count hands-off nodes
            tags = [t.lower() for t in d.get('tags', [])]
            if 'hands-off-engine' in tags or d['name'].startswith('ho-') or d['name'] == 'pm-helper':
                vcpus += d['vcpus']
                ram_gb += d['memory'] / 1024
                monthly_cost += d.get('size', {}).get('price_monthly', 0)

                ip = None
                for net in d.get('networks', {}).get('v4', []):
                    if net['type'] == 'public':
                        ip = net['ip_address']

                nodes.append({
                    'id': d['id'],
                    'name': d['name'],
                    'vcpus': d['vcpus'],
                    'ram_gb': d['memory'] / 1024,
                    'size': d['size_slug'],
                    'status': d['status'],
                    'ip': ip,
                })

        return vcpus, ram_gb, len(nodes), monthly_cost, nodes

    def get_scaling_state(self) -> ScalingState:
        """Get complete scaling state."""
        target_vcpus, target_ram_gb, multiplier = self.calculate_target()
        current_vcpus, current_ram_gb, node_count, monthly_cost, nodes = self.get_current_resources()

        days_running = (datetime.utcnow() - self.start_date).days

        vcpu_pct = (current_vcpus / target_vcpus * 100) if target_vcpus > 0 else 0
        ram_pct = (current_ram_gb / target_ram_gb * 100) if target_ram_gb > 0 else 0
        overall_pct = (vcpu_pct + ram_pct) / 2

        # Calculate nodes needed
        vcpu_gap = max(0, target_vcpus - current_vcpus)
        size_spec = self.INSTANCE_SIZES.get(self.config.preferred_size, {'vcpus': 8})
        nodes_to_add = math.ceil(vcpu_gap / size_spec['vcpus'])

        # Check if blocked
        blocked = len(self.blocked_sizes) > 0
        tier_requested = (STATE_DIR / 'tier_increase_requested.txt').exists()

        # Load last provision time
        last_prov = None
        prov_file = STATE_DIR / 'last_provision.txt'
        if prov_file.exists():
            last_prov = prov_file.read_text().strip()

        # Count today's provisions
        prov_today = self._count_provisions_today()

        return ScalingState(
            start_date=self.start_date.isoformat(),
            current_date=datetime.utcnow().isoformat(),
            days_running=days_running,
            current_vcpus=current_vcpus,
            current_ram_gb=current_ram_gb,
            current_nodes=node_count,
            current_monthly_cost=monthly_cost,
            target_vcpus=target_vcpus,
            target_ram_gb=target_ram_gb,
            target_multiplier=multiplier,
            vcpu_pct=round(vcpu_pct, 1),
            ram_pct=round(ram_pct, 1),
            overall_pct=round(overall_pct, 1),
            nodes_to_add=nodes_to_add,
            last_provision=last_prov,
            provisions_today=prov_today,
            blocked_by_tier=blocked,
            tier_increase_requested=tier_requested,
        )

    def _count_provisions_today(self) -> int:
        """Count provisions made today."""
        log_file = STATE_DIR / 'provision_log.jsonl'
        if not log_file.exists():
            return 0

        today = datetime.utcnow().date()
        count = 0

        for line in log_file.read_text().splitlines():
            try:
                entry = json.loads(line)
                entry_date = datetime.fromisoformat(entry['timestamp']).date()
                if entry_date == today:
                    count += 1
            except:
                pass

        return count

    def provision_node(self, name: str = None, size: str = None) -> Dict:
        """
        Provision a new compute node.

        Returns: {success: bool, droplet_id: str, error: str}
        """
        size = size or self.config.preferred_size

        # Check if size is blocked
        if size in self.blocked_sizes:
            # Try a smaller size
            smaller_sizes = ['s-4vcpu-8gb', 's-2vcpu-4gb']
            for alt_size in smaller_sizes:
                if alt_size not in self.blocked_sizes:
                    size = alt_size
                    break
            else:
                return {'success': False, 'error': 'All sizes blocked by tier limit'}

        # Generate name
        if not name:
            timestamp = int(time.time())
            name = f"ho-scale-{timestamp}"

        # Get SSH keys
        ok, keys_data = self._api_request('GET', '/account/keys')
        ssh_keys = [k['id'] for k in keys_data.get('ssh_keys', [])] if ok else []

        droplet_data = {
            'name': name,
            'region': self.config.preferred_region,
            'size': size,
            'image': 'ubuntu-22-04-x64',
            'ssh_keys': ssh_keys,
            'backups': True,
            'monitoring': True,
            'tags': ['hands-off-engine', 'compute-node', 'auto-scaled'],
            'user_data': self._get_cloud_init_script(),
        }

        ok, result = self._api_request('POST', '/droplets', droplet_data)

        if ok:
            droplet = result.get('droplet', {})

            # Log provision
            self._log_provision(droplet)

            return {
                'success': True,
                'droplet_id': droplet.get('id'),
                'name': droplet.get('name'),
                'size': size,
            }

        # Check if blocked by tier
        error_msg = str(result.get('error', {}).get('message', ''))
        if 'restricted' in error_msg.lower() or 'tier' in error_msg.lower():
            self.blocked_sizes.add(size)
            self._request_tier_increase()
            return {
                'success': False,
                'error': f'Size {size} blocked by tier. Tier increase requested.',
                'blocked': True,
            }

        return {
            'success': False,
            'error': error_msg or 'Unknown error',
        }

    def _get_cloud_init_script(self) -> str:
        """Get cloud-init script for new nodes."""
        return '''#!/bin/bash
# Auto-provisioned compute node setup

# Add pm-helper SSH key
mkdir -p /root/.ssh
chmod 700 /root/.ssh
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKUOlcMgjyYnAknQhzB/hHMZewPEx7XPLAd/Q2vLt1JD handsoff-do138" >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

# Install basics
apt-get update -qq
apt-get install -y -qq python3 python3-pip git curl jq

# Clone repo
git clone https://github.com/yaya1738/hands-off-engine.git /root/hands-off-engine || true

# Signal ready
touch /root/.node-ready
'''

    def _log_provision(self, droplet: Dict):
        """Log a provision event."""
        log_file = STATE_DIR / 'provision_log.jsonl'
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'droplet_id': droplet.get('id'),
            'name': droplet.get('name'),
            'size': droplet.get('size_slug'),
        }
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        # Update last provision time
        (STATE_DIR / 'last_provision.txt').write_text(entry['timestamp'])

    def _request_tier_increase(self):
        """Mark that tier increase was requested."""
        flag_file = STATE_DIR / 'tier_increase_requested.txt'
        if not flag_file.exists():
            flag_file.write_text(f"Requested at {datetime.utcnow().isoformat()}\n")
            flag_file.write_text("Please open a DO support ticket to increase account tier.\n")
            print("WARNING: Account tier limit reached. Please request tier increase at:")
            print("  https://cloud.digitalocean.com/support")

    def scale_to_target(self) -> List[Dict]:
        """
        Scale cluster toward target, provisioning as many nodes as needed.

        Returns list of provision results.
        """
        state = self.get_scaling_state()

        if state.overall_pct >= 100:
            return [{'action': 'none', 'reason': 'Already at target'}]

        if state.nodes_to_add <= 0:
            return [{'action': 'none', 'reason': 'No nodes needed'}]

        # Limit parallel provisions
        to_provision = min(state.nodes_to_add, self.config.max_parallel_provisions)

        # Check cost limit
        size_cost = self.INSTANCE_SIZES.get(self.config.preferred_size, {}).get('cost', 112)
        projected_cost = state.current_monthly_cost + (to_provision * size_cost)

        if projected_cost > self.config.max_monthly_cost:
            to_provision = max(1, int((self.config.max_monthly_cost - state.current_monthly_cost) / size_cost))

        if to_provision <= 0:
            return [{'action': 'none', 'reason': 'Cost limit reached'}]

        # Provision nodes
        results = []
        for i in range(to_provision):
            result = self.provision_node()
            results.append(result)

            if not result.get('success'):
                if result.get('blocked'):
                    # Stop if tier blocked
                    break
                # Small delay before retry
                time.sleep(5)

        return results

    def run_scaling_loop(self):
        """
        Run continuous scaling loop.

        Checks and scales every interval until target is reached.
        """
        print("=" * 60)
        print("AGGRESSIVE SCALING ENGINE - Exponential Growth Mode")
        print("=" * 60)
        print(f"Baseline: {self.config.baseline_vcpus} vCPU, {self.config.baseline_ram_gb}GB RAM")
        print(f"Initial multiplier: {self.config.target_multiplier}x")
        print(f"Daily growth rate: {self.config.daily_growth_rate}x")
        print(f"Preferred size: {self.config.preferred_size}")
        print("-" * 60)

        while True:
            try:
                state = self.get_scaling_state()

                print(f"\n[{state.current_date}] Day {state.days_running}")
                print(f"  Current: {state.current_vcpus} vCPU, {state.current_ram_gb}GB RAM ({state.current_nodes} nodes)")
                print(f"  Target:  {state.target_vcpus} vCPU, {state.target_ram_gb}GB RAM (multiplier: {state.target_multiplier:.1f}x)")
                print(f"  Progress: {state.overall_pct:.1f}%")
                print(f"  Monthly cost: ${state.current_monthly_cost:.2f}")

                if state.blocked_by_tier:
                    print("  ⚠️  BLOCKED BY TIER - Request increase at DO support")

                if state.overall_pct < 100:
                    print(f"  → Need to add {state.nodes_to_add} nodes")

                    # Scale up
                    results = self.scale_to_target()
                    for r in results:
                        if r.get('success'):
                            print(f"  ✓ Provisioned: {r.get('name')} ({r.get('size')})")
                        elif r.get('action') == 'none':
                            print(f"  - {r.get('reason')}")
                        else:
                            print(f"  ✗ Failed: {r.get('error')}")
                else:
                    print("  ✓ At or above target")

                # Save state
                state_dict = state.to_dict()
                self.state_file.write_text(json.dumps(state_dict, indent=2))

            except Exception as e:
                print(f"  ERROR: {e}")

            time.sleep(self.config.check_interval_sec)

    def status(self) -> Dict:
        """Get current scaling status."""
        state = self.get_scaling_state()
        return {
            **state.to_dict(),
            'blocked_sizes': list(self.blocked_sizes),
            'available_sizes': list(self.INSTANCE_SIZES.keys()),
        }


def main():
    import sys

    engine = ScalingEngine()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == 'status':
            status = engine.status()
            print(json.dumps(status, indent=2))

        elif cmd == 'scale':
            print("Scaling to target...")
            results = engine.scale_to_target()
            print(json.dumps(results, indent=2))

        elif cmd == 'run':
            engine.run_scaling_loop()

        elif cmd == 'provision':
            name = sys.argv[2] if len(sys.argv) > 2 else None
            result = engine.provision_node(name)
            print(json.dumps(result, indent=2))

        else:
            print(f"Unknown command: {cmd}")
            print("Commands: status, scale, run, provision [name]")
    else:
        # Default: show status
        status = engine.status()
        print("=== Scaling Status ===")
        print(f"Day {status['days_running']} | Multiplier: {status['target_multiplier']:.1f}x")
        print(f"Current: {status['current_vcpus']} vCPU, {status['current_ram_gb']}GB RAM")
        print(f"Target:  {status['target_vcpus']} vCPU, {status['target_ram_gb']}GB RAM")
        print(f"Progress: {status['overall_pct']:.1f}%")
        print(f"Nodes to add: {status['nodes_to_add']}")


if __name__ == '__main__':
    main()
