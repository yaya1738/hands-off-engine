#!/usr/bin/env python3
"""
FULL ACTIVATION - Use Everything We Have
==========================================

RESOURCES AVAILABLE:
- 4 Droplets (56GB RAM, 28 vCPUs)
- 27 Autonomous Modules
- 45 Scripts
- 4 Protection Layers
- 14 Cron Jobs Running

ZERO CAPITAL = PREPARATION MODE
- Gather maximum intelligence
- Pre-compute all trading signals
- Prepare instant execution
- Generate income opportunities
- Optimize all systems

When capital arrives, everything executes INSTANTLY.

Serving: Yair Siegel
"""

import json
import subprocess
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple
import concurrent.futures
import time

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
STATE_DIR.mkdir(parents=True, exist_ok=True)

MASTER = "Yair Siegel"
ACTIVATION_FILE = STATE_DIR / 'full_activation.json'


class FullActivation:
    """
    Activate and coordinate all system resources.
    """

    def __init__(self):
        self.state = self._load_state()
        self.results = {}

    def _load_state(self) -> Dict:
        """Load activation state."""
        if ACTIVATION_FILE.exists():
            try:
                with open(ACTIVATION_FILE) as f:
                    return json.load(f)
            except:
                pass
        return {
            "master": MASTER,
            "last_activation": None,
            "modules_active": 0,
            "nodes_coordinated": 0
        }

    def _save_state(self):
        """Save activation state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(ACTIVATION_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _run_module(self, module_name: str, args: List[str] = None) -> Tuple[bool, str]:
        """Run an autonomous module."""
        module_path = BASE_DIR / 'autonomous' / f'{module_name}.py'
        if not module_path.exists():
            return False, f"Module not found: {module_name}"

        try:
            cmd = ['python3', str(module_path)]
            if args:
                cmd.extend(args)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(BASE_DIR),
                env={**os.environ, "PYTHONPATH": str(BASE_DIR)}
            )

            if result.returncode == 0:
                return True, result.stdout[:500]
            else:
                return False, result.stderr[:500]

        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)

    # ========================================================================
    # ACTIVATION MODES
    # ========================================================================

    def activate_intelligence_gathering(self) -> Dict:
        """
        Activate all intelligence gathering capabilities.

        Uses all nodes to scan markets, gather data, analyze opportunities.
        """
        print("\n" + "="*60)
        print("ACTIVATING INTELLIGENCE GATHERING")
        print("="*60)

        results = {}

        # 1. Web agent - fetch market data
        print("\n[1] Web Agent - Market Data...")
        success, output = self._run_module('web_agent', ['fetch'])
        results['web_agent'] = {'success': success, 'output': output[:100]}
        print(f"    {'✓' if success else '✗'} Web Agent")

        # 2. Dense AI - market analysis
        print("\n[2] Dense AI - Market Analysis...")
        success, output = self._run_module('dense_ai', ['market', '--no-ai'])
        results['dense_ai'] = {'success': success, 'output': output[:100]}
        print(f"    {'✓' if success else '✗'} Dense AI")

        # 3. System topology - current state
        print("\n[3] System Topology - State Recording...")
        success, output = self._run_module('system_topology', ['record'])
        results['system_topology'] = {'success': success, 'output': output[:100]}
        print(f"    {'✓' if success else '✗'} System Topology")

        # 4. Threat analysis - security scan
        print("\n[4] Threat Analysis - Security Scan...")
        success, output = self._run_module('threat_analysis', ['scan'])
        results['threat_analysis'] = {'success': success, 'output': output[:100]}
        print(f"    {'✓' if success else '✗'} Threat Analysis")

        return results

    def activate_preparation_mode(self) -> Dict:
        """
        Prepare everything for instant execution when capital arrives.
        """
        print("\n" + "="*60)
        print("ACTIVATING PREPARATION MODE")
        print("="*60)

        results = {}

        # 1. Pre-compute trading signals
        print("\n[1] Pre-computing Trading Signals...")
        try:
            result = subprocess.run(
                ['python3', 'scripts/run_pipeline.py', '--dry-run', '--bankroll', '100'],
                capture_output=True, text=True, timeout=180,
                cwd=str(BASE_DIR),
                env={**os.environ, "PYTHONPATH": str(BASE_DIR)}
            )
            results['pipeline'] = {
                'success': result.returncode == 0,
                'output': result.stdout[:200]
            }
            print(f"    {'✓' if result.returncode == 0 else '✗'} Pipeline Dry Run")
        except Exception as e:
            results['pipeline'] = {'success': False, 'output': str(e)}
            print(f"    ✗ Pipeline: {e}")

        # 2. Optimize Claude
        print("\n[2] Optimizing Claude Integration...")
        success, output = self._run_module('claude_optimizer', ['optimize'])
        results['claude_optimizer'] = {'success': success, 'output': output[:100]}
        print(f"    {'✓' if success else '✗'} Claude Optimizer")

        # 3. Update singularity trigger
        print("\n[3] Updating Singularity Trigger...")
        success, output = self._run_module('singularity_trigger', ['check'])
        results['singularity_trigger'] = {'success': success, 'output': output[:100]}
        print(f"    {'✓' if success else '✗'} Singularity Trigger")

        # 4. Backup critical files
        print("\n[4] Backing Up Critical Files...")
        try:
            result = subprocess.run(
                ['python3', 'scripts/backup_critical.py'],
                capture_output=True, text=True, timeout=60,
                cwd=str(BASE_DIR)
            )
            results['backup'] = {'success': result.returncode == 0, 'output': result.stdout[:100]}
            print(f"    {'✓' if result.returncode == 0 else '✗'} Backup")
        except Exception as e:
            results['backup'] = {'success': False, 'output': str(e)}

        return results

    def activate_node_coordination(self) -> Dict:
        """
        Coordinate all 4 droplets to work together.
        """
        print("\n" + "="*60)
        print("ACTIVATING NODE COORDINATION")
        print("="*60)

        results = {}

        # Get node list
        try:
            result = subprocess.run(
                ['doctl', 'compute', 'droplet', 'list', '--format', 'Name,PublicIPv4', '--no-header'],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                nodes = []
                for line in result.stdout.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        nodes.append({'name': parts[0], 'ip': parts[1]})

                print(f"\n[1] Found {len(nodes)} nodes:")
                for node in nodes:
                    print(f"    - {node['name']}: {node['ip']}")

                results['nodes'] = nodes

                # Sync code to all nodes
                print("\n[2] Syncing code to all nodes...")
                for node in nodes:
                    if node['ip'] != '138.68.103.156':  # Skip primary
                        try:
                            sync_result = subprocess.run(
                                ['rsync', '-az', '--delete',
                                 f'{BASE_DIR}/', f"root@{node['ip']}:/root/hands-off-engine/"],
                                capture_output=True, text=True, timeout=120
                            )
                            status = '✓' if sync_result.returncode == 0 else '✗'
                            print(f"    {status} Synced to {node['name']}")
                        except:
                            print(f"    ✗ Failed to sync to {node['name']}")

                self.state["nodes_coordinated"] = len(nodes)

        except Exception as e:
            results['error'] = str(e)
            print(f"    ✗ Node coordination failed: {e}")

        return results

    def activate_protection_layers(self) -> Dict:
        """
        Ensure all protection layers are active and healthy.
        """
        print("\n" + "="*60)
        print("ACTIVATING PROTECTION LAYERS")
        print("="*60)

        results = {}
        layers = [
            ('self_preservation', ['status']),
            ('system_immunity', ['status']),
            ('harm_prevention', ['status']),
            ('claude_optimizer', ['status']),
        ]

        for layer, args in layers:
            print(f"\n[{layers.index((layer, args)) + 1}] {layer}...")
            success, output = self._run_module(layer, args)
            results[layer] = {'success': success, 'active': success}
            print(f"    {'✓ ACTIVE' if success else '✗ INACTIVE'}")

        return results

    def activate_income_generation(self) -> Dict:
        """
        Activate all income generation channels.
        """
        print("\n" + "="*60)
        print("ACTIVATING INCOME GENERATION")
        print("="*60)

        results = {}

        # 1. Check outreach materials
        print("\n[1] Checking Outreach Materials...")
        outreach_dir = BASE_DIR / 'outreach'
        if outreach_dir.exists():
            materials = list(outreach_dir.glob('*.md'))
            print(f"    ✓ {len(materials)} outreach materials ready")
            results['outreach'] = {'ready': True, 'count': len(materials)}
        else:
            print("    ✗ No outreach materials")
            results['outreach'] = {'ready': False}

        # 2. Check landing pages
        print("\n[2] Checking Landing Pages...")
        try:
            # Main landing page
            result = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://138.68.103.156:8080'],
                capture_output=True, text=True, timeout=10
            )
            main_up = result.stdout == '200'
            print(f"    {'✓' if main_up else '✗'} Main landing page (8080)")

            # Consulting page
            result = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://138.68.103.156:8081'],
                capture_output=True, text=True, timeout=10
            )
            consulting_up = result.stdout == '200'
            print(f"    {'✓' if consulting_up else '✗'} Consulting page (8081)")

            results['landing_pages'] = {
                'main': main_up,
                'consulting': consulting_up
            }
        except Exception as e:
            results['landing_pages'] = {'error': str(e)}

        # 3. Check GitHub funding
        print("\n[3] Checking GitHub Funding...")
        funding_file = BASE_DIR / '.github' / 'FUNDING.yml'
        if funding_file.exists():
            print("    ✓ GitHub sponsors enabled")
            results['github_funding'] = True
        else:
            print("    ✗ GitHub funding not set up")
            results['github_funding'] = False

        return results

    def full_activation(self) -> Dict:
        """
        Run full activation of all systems.
        """
        print("\n" + "="*60)
        print("FULL SYSTEM ACTIVATION")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("="*60)

        all_results = {}

        # 1. Protection layers first
        all_results['protection'] = self.activate_protection_layers()

        # 2. Intelligence gathering
        all_results['intelligence'] = self.activate_intelligence_gathering()

        # 3. Preparation mode
        all_results['preparation'] = self.activate_preparation_mode()

        # 4. Node coordination
        all_results['nodes'] = self.activate_node_coordination()

        # 5. Income generation
        all_results['income'] = self.activate_income_generation()

        # Summary
        print("\n" + "="*60)
        print("ACTIVATION SUMMARY")
        print("="*60)

        total_success = 0
        total_items = 0

        for category, results in all_results.items():
            if isinstance(results, dict):
                successes = sum(1 for v in results.values()
                               if isinstance(v, dict) and v.get('success', False))
                items = len([v for v in results.values() if isinstance(v, dict)])
                if items > 0:
                    total_success += successes
                    total_items += items
                    print(f"  {category}: {successes}/{items} active")

        print(f"\nTotal: {total_success}/{total_items} components active")
        print(f"Activation rate: {(total_success/total_items*100) if total_items > 0 else 0:.0f}%")

        # Save state
        self.state["last_activation"] = datetime.now(timezone.utc).isoformat()
        self.state["modules_active"] = total_success
        self.state["results"] = all_results
        self._save_state()

        return all_results

    def get_status(self) -> Dict:
        """Get current activation status."""
        return {
            "master": MASTER,
            "last_activation": self.state.get("last_activation"),
            "modules_active": self.state.get("modules_active", 0),
            "nodes_coordinated": self.state.get("nodes_coordinated", 0),
            "ready_for_capital": self.state.get("modules_active", 0) > 10
        }


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Full System Activation")
    parser.add_argument("command", choices=[
        "status", "full", "intelligence", "preparation",
        "nodes", "protection", "income"
    ])

    args = parser.parse_args()
    activation = FullActivation()

    if args.command == "status":
        status = activation.get_status()
        print(f"\n{'='*60}")
        print("ACTIVATION STATUS")
        print(f"{'='*60}")
        print(f"Master: {status['master']}")
        print(f"Last activation: {status['last_activation']}")
        print(f"Modules active: {status['modules_active']}")
        print(f"Nodes coordinated: {status['nodes_coordinated']}")
        print(f"Ready for capital: {'YES' if status['ready_for_capital'] else 'NO'}")

    elif args.command == "full":
        activation.full_activation()

    elif args.command == "intelligence":
        activation.activate_intelligence_gathering()

    elif args.command == "preparation":
        activation.activate_preparation_mode()

    elif args.command == "nodes":
        activation.activate_node_coordination()

    elif args.command == "protection":
        activation.activate_protection_layers()

    elif args.command == "income":
        activation.activate_income_generation()


if __name__ == "__main__":
    main()
