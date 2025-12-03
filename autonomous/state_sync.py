#!/usr/bin/env python3
"""
STATE SYNCHRONIZATION - Multi-Node State Consistency

Ensures all nodes in the cluster have consistent state:
1. Primary node broadcasts state changes
2. Compute nodes receive and apply updates
3. Conflict resolution for split-brain scenarios
4. Automatic state recovery from peers

Standard: Yair Siegel Master Level Operations - Distributed Consensus
"""

import json
import os
import socket
import subprocess
import hashlib
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import urllib.request

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
SYNC_DIR = STATE_DIR / 'sync'
STATE_DIR.mkdir(parents=True, exist_ok=True)
SYNC_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class NodeInfo:
    """Information about a cluster node."""
    name: str
    ip: str
    private_ip: str
    is_primary: bool
    last_seen: datetime
    state_hash: str
    reachable: bool


class StateSync:
    """
    Distributed state synchronization system.

    Uses a simple leader-follower model:
    - Primary node is the source of truth
    - Compute nodes pull state from primary
    - If primary is unreachable, nodes operate independently
    """

    # Files to synchronize across nodes
    SYNC_FILES = [
        'brain_state.json',
        'scaling_state.json',
        'cluster_state.json',
        'evolution_generation.txt',
        'pending_actions.json',
    ]

    # Environment files to sync (sensitive - only via secure channel)
    ENV_FILES = [
        '.env',
        '.env.polymarket',
    ]

    def __init__(self):
        self.hostname = socket.gethostname()
        self.is_primary = self.hostname == 'pm-helper'
        self.nodes: Dict[str, NodeInfo] = {}
        self.state_version = 0
        self.last_sync = None

        self._log(f"StateSync initialized on {self.hostname} (primary: {self.is_primary})")

    def _log(self, message: str, data: Dict = None, level: str = 'info'):
        """Log a message."""
        timestamp = datetime.utcnow().isoformat()
        log_line = f"[{timestamp}] [SYNC] [{level.upper()}] {message}"
        if data:
            log_line += f" | {json.dumps(data)}"
        print(log_line)

    def discover_nodes(self) -> List[NodeInfo]:
        """
        Discover all nodes in the cluster.

        Uses DO API to find all hands-off droplets.
        """
        # Load DO token
        do_token = os.environ.get('DO_API_TOKEN', '')
        if not do_token:
            env_file = BASE_DIR / '.env'
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith('DO_API_TOKEN='):
                        do_token = line.split('=', 1)[1].strip()

        if not do_token:
            self._log("No DO token - cannot discover nodes", level='warning')
            return []

        try:
            url = "https://api.digitalocean.com/v2/droplets?per_page=100"
            req = urllib.request.Request(url, headers={
                'Authorization': f'Bearer {do_token}',
                'Content-Type': 'application/json'
            })

            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())

            nodes = []
            for d in data.get('droplets', []):
                tags = [t.lower() for t in d.get('tags', [])]
                if 'hands-off-engine' not in tags and not d['name'].startswith('ho-') and d['name'] != 'pm-helper':
                    continue

                public_ip = None
                private_ip = None
                for net in d.get('networks', {}).get('v4', []):
                    if net['type'] == 'public':
                        public_ip = net['ip_address']
                    elif net['type'] == 'private':
                        private_ip = net['ip_address']

                node = NodeInfo(
                    name=d['name'],
                    ip=public_ip or '',
                    private_ip=private_ip or '',
                    is_primary=d['name'] == 'pm-helper',
                    last_seen=datetime.utcnow(),
                    state_hash='',
                    reachable=d['status'] == 'active',
                )
                nodes.append(node)
                self.nodes[node.name] = node

            return nodes

        except Exception as e:
            self._log(f"Error discovering nodes: {e}", level='error')
            return []

    def calculate_state_hash(self) -> str:
        """Calculate hash of current state for comparison."""
        hasher = hashlib.sha256()

        for filename in self.SYNC_FILES:
            filepath = STATE_DIR / filename
            if filepath.exists():
                content = filepath.read_bytes()
                hasher.update(content)

        return hasher.hexdigest()[:16]

    def get_state_bundle(self) -> Dict:
        """
        Get current state as a bundle for syncing.

        Returns dict with file contents.
        """
        bundle = {
            'timestamp': datetime.utcnow().isoformat(),
            'source': self.hostname,
            'version': self.state_version,
            'hash': self.calculate_state_hash(),
            'files': {},
        }

        for filename in self.SYNC_FILES:
            filepath = STATE_DIR / filename
            if filepath.exists():
                bundle['files'][filename] = filepath.read_text()

        return bundle

    def apply_state_bundle(self, bundle: Dict) -> bool:
        """
        Apply a state bundle from another node.

        Only applies if version is newer.
        """
        remote_version = bundle.get('version', 0)

        if remote_version <= self.state_version:
            self._log(f"Ignoring older state (remote: {remote_version}, local: {self.state_version})")
            return False

        self._log(f"Applying state bundle from {bundle.get('source')}")

        for filename, content in bundle.get('files', {}).items():
            filepath = STATE_DIR / filename
            try:
                filepath.write_text(content)
            except Exception as e:
                self._log(f"Error writing {filename}: {e}", level='error')
                return False

        self.state_version = remote_version
        self.last_sync = datetime.utcnow()

        return True

    def push_to_node(self, node: NodeInfo) -> bool:
        """
        Push current state to a remote node via SSH.
        """
        if not node.ip or node.name == self.hostname:
            return False

        try:
            bundle = self.get_state_bundle()
            bundle_json = json.dumps(bundle)

            # Write to temp file and scp
            temp_file = SYNC_DIR / f"bundle_{node.name}.json"
            temp_file.write_text(bundle_json)

            result = subprocess.run([
                'scp', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10',
                str(temp_file),
                f'root@{node.ip}:/root/hands-off-engine/state/sync/incoming.json'
            ], capture_output=True, timeout=30)

            if result.returncode == 0:
                # Trigger apply on remote
                subprocess.run([
                    'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10',
                    f'root@{node.ip}',
                    'python3 /root/hands-off-engine/autonomous/state_sync.py apply'
                ], capture_output=True, timeout=30)
                return True

            return False

        except Exception as e:
            self._log(f"Error pushing to {node.name}: {e}", level='error')
            return False

    def pull_from_primary(self) -> bool:
        """
        Pull state from primary node.
        """
        if self.is_primary:
            return True  # We are primary

        # Find primary
        primary = None
        for node in self.nodes.values():
            if node.is_primary and node.reachable:
                primary = node
                break

        if not primary:
            self._log("No reachable primary node", level='warning')
            return False

        try:
            # Pull bundle from primary
            result = subprocess.run([
                'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10',
                f'root@{primary.ip}',
                'python3 /root/hands-off-engine/autonomous/state_sync.py bundle'
            ], capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return False

            bundle = json.loads(result.stdout)
            return self.apply_state_bundle(bundle)

        except Exception as e:
            self._log(f"Error pulling from primary: {e}", level='error')
            return False

    def apply_incoming_bundle(self) -> bool:
        """Apply an incoming bundle from sync/incoming.json."""
        incoming_file = SYNC_DIR / 'incoming.json'

        if not incoming_file.exists():
            return False

        try:
            bundle = json.loads(incoming_file.read_text())
            result = self.apply_state_bundle(bundle)

            # Archive the incoming file
            archive = SYNC_DIR / f"applied_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            incoming_file.rename(archive)

            return result

        except Exception as e:
            self._log(f"Error applying incoming bundle: {e}", level='error')
            return False

    def broadcast_state(self) -> Dict:
        """
        Broadcast current state to all nodes (primary only).
        """
        if not self.is_primary:
            return {'error': 'Not primary'}

        self.state_version += 1
        results = {}

        nodes = self.discover_nodes()
        for node in nodes:
            if node.name != self.hostname:
                success = self.push_to_node(node)
                results[node.name] = success

        return {
            'version': self.state_version,
            'results': results,
        }

    def sync(self) -> Dict:
        """
        Perform sync operation based on role.

        Primary: broadcast to all nodes
        Compute: pull from primary
        """
        if self.is_primary:
            return self.broadcast_state()
        else:
            success = self.pull_from_primary()
            return {
                'action': 'pull',
                'success': success,
                'version': self.state_version,
            }

    def run_sync_loop(self, interval_sec: int = 60):
        """
        Run continuous sync loop.
        """
        self._log(f"Starting sync loop (interval: {interval_sec}s, primary: {self.is_primary})")

        while True:
            try:
                # Discover nodes
                self.discover_nodes()

                # Sync
                result = self.sync()
                self._log(f"Sync completed", result)

            except Exception as e:
                self._log(f"Sync error: {e}", level='error')

            time.sleep(interval_sec)


def main():
    import sys

    sync = StateSync()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == 'bundle':
            # Output bundle as JSON (for piping)
            bundle = sync.get_state_bundle()
            print(json.dumps(bundle))

        elif cmd == 'apply':
            # Apply incoming bundle
            result = sync.apply_incoming_bundle()
            print(json.dumps({'applied': result}))

        elif cmd == 'sync':
            # One-time sync
            result = sync.sync()
            print(json.dumps(result, indent=2))

        elif cmd == 'run':
            # Continuous sync loop
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            sync.run_sync_loop(interval)

        elif cmd == 'nodes':
            # Show discovered nodes
            nodes = sync.discover_nodes()
            for n in nodes:
                print(f"  {n.name}: {n.ip} (primary: {n.is_primary}, reachable: {n.reachable})")

        else:
            print(f"Unknown command: {cmd}")
            print("Commands: bundle, apply, sync, run [interval], nodes")
    else:
        print("State Sync Status:")
        print(f"  Hostname: {sync.hostname}")
        print(f"  Is Primary: {sync.is_primary}")
        print(f"  State Hash: {sync.calculate_state_hash()}")
        print(f"  State Version: {sync.state_version}")


if __name__ == '__main__':
    main()
