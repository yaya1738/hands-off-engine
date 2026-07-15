#!/usr/bin/env python3
"""
Autonomous Infrastructure Manager - Real-time Distributed Compute

Manages distributed compute across multiple droplets autonomously.
NEVER turns off, restarts, or downgrades any droplet.

Standard: Yair Siegel Master Level Operations - Full Self-Control
"""

import json
import os
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Load DO token
DO_TOKEN = os.environ.get('DO_API_TOKEN', '')
if not DO_TOKEN:
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith('DO_API_TOKEN='):
                DO_TOKEN = line.split('=', 1)[1].strip()

STATE_FILE = Path(__file__).parent.parent / 'state' / 'infra_state.json'
CLUSTER_FILE = Path(__file__).parent.parent / 'state' / 'cluster_state.json'


class InfraManager:
    """
    Autonomous infrastructure manager.

    RULES:
    - NEVER power off any droplet
    - NEVER restart any droplet
    - NEVER downgrade any droplet
    - ONLY add new resources
    - ONLY scale UP
    """

    API_BASE = "https://api.digitalocean.com/v2"

    # CRITICAL: These droplets must NEVER be touched
    PROTECTED_DROPLETS = {
        'pm-helper': '524521199',
        'ho-compute-1': '533553630',
        'ho-compute-2': '533553637',
    }

    # Minimum cluster specs (5x original)
    MIN_CLUSTER_VCPU = 20
    MIN_CLUSTER_RAM_GB = 40

    def __init__(self):
        self.token = DO_TOKEN
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {
            'last_check': None,
            'cluster_healthy': True,
            'total_vcpu': 0,
            'total_ram_gb': 0,
            'droplets': {},
            'alerts': [],
        }

    def _save_state(self):
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2, default=str))

    def _api_request(self, method: str, endpoint: str, data: dict = None) -> Tuple[bool, dict]:
        """Make DO API request."""
        import urllib.request
        import urllib.error

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
        except Exception as e:
            return False, {'error': str(e)}

    def get_cluster_status(self) -> Dict:
        """Get current cluster status."""
        ok, data = self._api_request('GET', '/droplets?per_page=100')
        if not ok:
            return {'error': data.get('error', 'API failed')}

        droplets = data.get('droplets', [])
        cluster = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_vcpu': 0,
            'total_ram_gb': 0,
            'total_disk_gb': 0,
            'droplets': [],
            'healthy': True,
        }

        for d in droplets:
            # Only count hands-off-engine droplets
            if d['name'] in self.PROTECTED_DROPLETS or 'hands-off' in str(d.get('tags', [])):
                vcpu = d['vcpus']
                ram = d['memory'] / 1024
                disk = d['disk']

                ip = None
                for net in d.get('networks', {}).get('v4', []):
                    if net['type'] == 'public':
                        ip = net['ip_address']

                droplet_info = {
                    'id': d['id'],
                    'name': d['name'],
                    'vcpu': vcpu,
                    'ram_gb': ram,
                    'disk_gb': disk,
                    'status': d['status'],
                    'ip': ip,
                    'region': d.get('region', {}).get('slug', ''),
                    'size': d['size_slug'],
                }

                cluster['droplets'].append(droplet_info)
                cluster['total_vcpu'] += vcpu
                cluster['total_ram_gb'] += ram
                cluster['total_disk_gb'] += disk

                if d['status'] != 'active':
                    cluster['healthy'] = False

        # Check if we meet minimum specs
        if cluster['total_vcpu'] < self.MIN_CLUSTER_VCPU:
            cluster['healthy'] = False
            cluster['alert'] = f"Below minimum vCPU: {cluster['total_vcpu']}/{self.MIN_CLUSTER_VCPU}"

        if cluster['total_ram_gb'] < self.MIN_CLUSTER_RAM_GB:
            cluster['healthy'] = False
            cluster['alert'] = f"Below minimum RAM: {cluster['total_ram_gb']}/{self.MIN_CLUSTER_RAM_GB}"

        return cluster

    def auto_scale_up(self) -> Dict:
        """
        Automatically scale UP if cluster is below minimum.
        NEVER scales down. NEVER touches existing droplets.
        """
        cluster = self.get_cluster_status()
        if 'error' in cluster:
            return cluster

        result = {
            'action': 'none',
            'cluster': cluster,
        }

        # Check if we need more resources
        vcpu_needed = self.MIN_CLUSTER_VCPU - cluster['total_vcpu']
        ram_needed = self.MIN_CLUSTER_RAM_GB - cluster['total_ram_gb']

        if vcpu_needed > 0 or ram_needed > 0:
            result['action'] = 'scale_up_needed'
            result['vcpu_needed'] = max(0, vcpu_needed)
            result['ram_needed'] = max(0, ram_needed)
            result['recommendation'] = self._get_scale_recommendation(vcpu_needed, ram_needed)

        return result

    def _get_scale_recommendation(self, vcpu_needed: int, ram_needed: int) -> str:
        """Get recommendation for scaling up."""
        if vcpu_needed <= 0 and ram_needed <= 0:
            return "No scaling needed"

        # Recommend adding droplets
        if vcpu_needed >= 8 or ram_needed >= 16:
            return "Add s-8vcpu-16gb-amd droplet ($112/mo)"
        elif vcpu_needed >= 4 or ram_needed >= 8:
            return "Add s-4vcpu-8gb droplet ($48/mo)"
        else:
            return "Add s-2vcpu-4gb droplet ($24/mo)"

    def add_compute_node(self, name: str, size: str = 's-8vcpu-16gb-amd', region: str = 'nyc1') -> Dict:
        """
        Add a new compute node to the cluster.
        NEVER modifies or removes existing nodes.
        """
        # Get SSH keys
        ok, keys_data = self._api_request('GET', '/account/keys')
        ssh_keys = [k['id'] for k in keys_data.get('ssh_keys', [])] if ok else []

        from finance.autonomous_cost_gate import get_cost_gate

        gate = get_cost_gate()
        approved, reason = gate.pre_scale_cost_check(
            size=size,
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
            'name': name,
            'region': region,
            'size': size,
            'image': 'ubuntu-22-04-x64',
            'ssh_keys': ssh_keys,
            'backups': True,
            'monitoring': True,
            'tags': ['hands-off-engine', 'compute-node', 'auto-provisioned'],
        }

        ok, result = self._api_request('POST', '/droplets', droplet_data)
        if ok:
            droplet = result.get('droplet', {})
            self.PROTECTED_DROPLETS[name] = str(droplet.get('id'))
            return {
                'success': True,
                'droplet_id': droplet.get('id'),
                'name': name,
                'size': size,
            }

        return {'success': False, 'error': result.get('error', 'Creation failed')}

    def health_check(self) -> Dict:
        """
        Run health check on all cluster nodes.
        Does NOT modify any nodes.
        """
        cluster = self.get_cluster_status()

        health = {
            'timestamp': datetime.utcnow().isoformat(),
            'cluster_healthy': cluster.get('healthy', False),
            'total_vcpu': cluster.get('total_vcpu', 0),
            'total_ram_gb': cluster.get('total_ram_gb', 0),
            'nodes': [],
            'issues': [],
        }

        for d in cluster.get('droplets', []):
            node_health = {
                'name': d['name'],
                'status': d['status'],
                'healthy': d['status'] == 'active',
            }

            # Try to ping the node
            if d.get('ip'):
                try:
                    result = subprocess.run(
                        ['ping', '-c', '1', '-W', '2', d['ip']],
                        capture_output=True,
                        timeout=5
                    )
                    node_health['reachable'] = result.returncode == 0
                except:
                    node_health['reachable'] = False

            health['nodes'].append(node_health)

            if not node_health.get('healthy'):
                health['issues'].append(f"{d['name']} is not active (status: {d['status']})")
            elif not node_health.get('reachable'):
                health['issues'].append(f"{d['name']} is not reachable via ping")

        # Save state
        self.state['last_check'] = health['timestamp']
        self.state['cluster_healthy'] = health['cluster_healthy']
        self.state['total_vcpu'] = health['total_vcpu']
        self.state['total_ram_gb'] = health['total_ram_gb']
        self._save_state()

        return health

    def run_continuous_monitoring(self, interval_seconds: int = 300):
        """
        Run continuous monitoring loop.
        Checks health every interval, auto-scales UP if needed.
        NEVER turns off or restarts anything.
        """
        print(f"Starting continuous infrastructure monitoring (interval: {interval_seconds}s)")
        print("RULES: NEVER power off, restart, or downgrade. ONLY scale UP.")

        while True:
            try:
                health = self.health_check()
                print(f"\n[{health['timestamp']}] Cluster: {health['total_vcpu']} vCPU, {health['total_ram_gb']}GB RAM")

                if health['issues']:
                    print(f"  Issues: {health['issues']}")

                # Check if auto-scale needed
                scale = self.auto_scale_up()
                if scale.get('action') == 'scale_up_needed':
                    print(f"  ALERT: Need to scale up!")
                    print(f"    vCPU needed: {scale.get('vcpu_needed', 0)}")
                    print(f"    RAM needed: {scale.get('ram_needed', 0)}GB")
                    print(f"    Recommendation: {scale.get('recommendation', 'unknown')}")
                else:
                    print(f"  Status: Healthy - meets minimum requirements")

            except Exception as e:
                print(f"  Error during monitoring: {e}")

            time.sleep(interval_seconds)


def main():
    """Main entry point."""
    import sys

    manager = InfraManager()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == 'status':
            cluster = manager.get_cluster_status()
            print(json.dumps(cluster, indent=2))

        elif cmd == 'health':
            health = manager.health_check()
            print(json.dumps(health, indent=2))

        elif cmd == 'scale':
            scale = manager.auto_scale_up()
            print(json.dumps(scale, indent=2))

        elif cmd == 'add':
            if len(sys.argv) < 3:
                print("Usage: infra_manager.py add <name> [size]")
                sys.exit(1)
            name = sys.argv[2]
            size = sys.argv[3] if len(sys.argv) > 3 else 's-8vcpu-16gb-amd'
            result = manager.add_compute_node(name, size)
            print(json.dumps(result, indent=2))

        elif cmd == 'monitor':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300
            manager.run_continuous_monitoring(interval)

        else:
            print(f"Unknown command: {cmd}")
            print("Commands: status, health, scale, add <name> [size], monitor [interval]")

    else:
        # Default: show status
        cluster = manager.get_cluster_status()
        print("=== Cluster Status ===")
        print(f"Total: {cluster['total_vcpu']} vCPU, {cluster['total_ram_gb']}GB RAM")
        print(f"Healthy: {cluster['healthy']}")
        print("\nDroplets:")
        for d in cluster.get('droplets', []):
            print(f"  {d['name']}: {d['vcpu']} vCPU, {d['ram_gb']}GB - {d['status']} - {d.get('ip', 'no IP')}")


if __name__ == '__main__':
    main()
