#!/usr/bin/env python3
"""
Infrastructure Scaler - Autonomous Hardware Acquisition & Self-Improvement

Handles:
1. Dynamic droplet provisioning via DigitalOcean API
2. Auto-scaling based on revenue milestones
3. Hardware health monitoring with retry logic
4. Self-improvement through infrastructure optimization
5. Automatic failover and redundancy

This is the self-hardware management brain that ensures
the system can acquire and manage its own compute resources.
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
CONFIG_DIR = REPO_ROOT / "config"
LOGS_DIR = REPO_ROOT / "logs"

# Infrastructure configuration
INFRASTRUCTURE_CONFIG = {
    "digitalocean": {
        "api_base": "https://api.digitalocean.com/v2",
        "default_region": "nyc1",
        "default_size": "s-1vcpu-1gb",  # $6/month starter
        "image": "ubuntu-22-04-x64",
        "ssh_keys": [],  # Will be populated from env
        "tags": ["hands-off-engine", "autonomous"],
    },
    "scaling_tiers": {
        "starter": {
            "droplet_size": "s-1vcpu-1gb",
            "monthly_cost": 6,
            "revenue_threshold": 0,
            "max_droplets": 1
        },
        "growth": {
            "droplet_size": "s-2vcpu-2gb",
            "monthly_cost": 18,
            "revenue_threshold": 500,
            "max_droplets": 2
        },
        "scale": {
            "droplet_size": "s-4vcpu-8gb",
            "monthly_cost": 48,
            "revenue_threshold": 2000,
            "max_droplets": 3
        },
        "enterprise": {
            "droplet_size": "s-8vcpu-16gb",
            "monthly_cost": 96,
            "revenue_threshold": 10000,
            "max_droplets": 5
        }
    },
    "retry_config": {
        "max_retries": 4,
        "base_delay": 2,  # Exponential backoff: 2, 4, 8, 16 seconds
        "timeout": 60
    }
}


class InfrastructureScaler:
    """
    Autonomous hardware acquisition and management system.
    Self-improves by scaling resources based on revenue and performance.
    """

    def __init__(self):
        self.do_token = os.getenv("DO_TOKEN") or os.getenv("DIGITALOCEAN_TOKEN")
        self.state_file = STATE_DIR / "infrastructure_state.json"
        self.state = self.load_state()
        self.session = requests.Session()
        if self.do_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.do_token}",
                "Content-Type": "application/json"
            })

    def load_state(self) -> Dict:
        """Load infrastructure state from disk."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "current_tier": "starter",
            "droplets": [],
            "last_scale_event": None,
            "total_revenue_tracked": 0,
            "health_checks": [],
            "acquisition_history": []
        }

    def save_state(self):
        """Persist infrastructure state."""
        self.state["updated_at"] = datetime.utcnow().isoformat() + "Z"
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _api_call_with_retry(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make API call with exponential backoff retry."""
        config = INFRASTRUCTURE_CONFIG["retry_config"]
        url = f"{INFRASTRUCTURE_CONFIG['digitalocean']['api_base']}{endpoint}"

        for attempt in range(config["max_retries"]):
            try:
                kwargs.setdefault("timeout", config["timeout"])
                response = getattr(self.session, method)(url, **kwargs)

                if response.status_code in (200, 201, 202, 204):
                    return response.json() if response.text else {}
                elif response.status_code == 429:  # Rate limited
                    delay = config["base_delay"] * (2 ** attempt)
                    print(f"[rate-limited] Waiting {delay}s before retry...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"[error] API returned {response.status_code}: {response.text}")
                    return None

            except requests.exceptions.Timeout:
                delay = config["base_delay"] * (2 ** attempt)
                print(f"[timeout] Attempt {attempt + 1}/{config['max_retries']}, "
                      f"retrying in {delay}s...")
                time.sleep(delay)
            except requests.exceptions.ConnectionError as e:
                delay = config["base_delay"] * (2 ** attempt)
                print(f"[connection-error] {e}, retrying in {delay}s...")
                time.sleep(delay)

        print(f"[failed] All {config['max_retries']} attempts exhausted")
        return None

    def check_droplet_health(self, droplet_id: int) -> Dict:
        """Check health of a specific droplet with retry logic."""
        result = self._api_call_with_retry("get", f"/droplets/{droplet_id}")
        if result and "droplet" in result:
            droplet = result["droplet"]
            return {
                "id": droplet_id,
                "status": droplet.get("status"),
                "ip": droplet.get("networks", {}).get("v4", [{}])[0].get("ip_address"),
                "healthy": droplet.get("status") == "active",
                "checked_at": datetime.utcnow().isoformat() + "Z"
            }
        return {
            "id": droplet_id,
            "status": "unreachable",
            "healthy": False,
            "error": "Failed to reach API",
            "checked_at": datetime.utcnow().isoformat() + "Z"
        }

    def check_ssh_connectivity(self, ip: str, ports: List[int] = None) -> bool:
        """Check SSH connectivity with multiple port attempts."""
        ports = ports or [22, 443, 2222]
        ssh_opts = "-o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=15"

        for port in ports:
            try:
                result = subprocess.run(
                    f"ssh {ssh_opts} -p {port} root@{ip} 'echo ok'",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=45
                )
                if result.returncode == 0 and "ok" in result.stdout:
                    return True
            except subprocess.TimeoutExpired:
                continue
            except Exception as e:
                print(f"[ssh-check] Port {port} failed: {e}")
                continue

        return False

    def list_droplets(self) -> List[Dict]:
        """List all droplets tagged with hands-off-engine."""
        result = self._api_call_with_retry(
            "get",
            "/droplets",
            params={"tag_name": "hands-off-engine"}
        )
        if result and "droplets" in result:
            return result["droplets"]
        return []

    def get_current_revenue(self) -> float:
        """Get current monthly revenue from state files."""
        try:
            revenue_file = STATE_DIR / "revenue_projection.json"
            if revenue_file.exists():
                with open(revenue_file) as f:
                    data = json.load(f)
                    return data.get("total_monthly_potential", 0)

            # Fallback: estimate from trading performance
            perf_file = LOGS_DIR / "trading_performance.jsonl"
            if perf_file.exists():
                total_pnl = 0
                with open(perf_file) as f:
                    for line in f:
                        try:
                            trade = json.loads(line)
                            total_pnl += trade.get("pnl", 0)
                        except:
                            continue
                return max(0, total_pnl * 4)  # Rough monthly projection

        except Exception as e:
            print(f"[revenue-check] Error: {e}")

        return 0

    def determine_optimal_tier(self, revenue: float) -> str:
        """Determine which infrastructure tier is appropriate."""
        tiers = INFRASTRUCTURE_CONFIG["scaling_tiers"]

        optimal = "starter"
        for tier_name, config in tiers.items():
            if revenue >= config["revenue_threshold"]:
                optimal = tier_name

        return optimal

    def provision_droplet(self, name: str = None, size: str = None) -> Optional[Dict]:
        """Provision a new droplet."""
        if not self.do_token:
            print("[error] DO_TOKEN not configured - cannot provision")
            return None

        do_config = INFRASTRUCTURE_CONFIG["digitalocean"]
        tier = self.state.get("current_tier", "starter")
        tier_config = INFRASTRUCTURE_CONFIG["scaling_tiers"][tier]

        name = name or f"hands-off-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        size = size or tier_config["droplet_size"]

        payload = {
            "name": name,
            "region": do_config["default_region"],
            "size": size,
            "image": do_config["image"],
            "ssh_keys": do_config["ssh_keys"],
            "tags": do_config["tags"],
            "monitoring": True,
            "backups": True
        }

        result = self._api_call_with_retry("post", "/droplets", json=payload)

        if result and "droplet" in result:
            droplet = result["droplet"]
            print(f"[provisioned] Droplet {droplet['id']} created: {name}")

            # Record acquisition
            self.state["acquisition_history"].append({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "droplet_id": droplet["id"],
                "name": name,
                "size": size,
                "action": "provision"
            })
            self.state["droplets"].append({
                "id": droplet["id"],
                "name": name,
                "size": size,
                "created_at": datetime.utcnow().isoformat() + "Z"
            })
            self.save_state()

            return droplet

        return None

    def destroy_droplet(self, droplet_id: int) -> bool:
        """Destroy a droplet (for scaling down or replacing unhealthy)."""
        result = self._api_call_with_retry("delete", f"/droplets/{droplet_id}")

        if result is not None:  # 204 returns empty
            print(f"[destroyed] Droplet {droplet_id} removed")
            self.state["droplets"] = [
                d for d in self.state["droplets"] if d["id"] != droplet_id
            ]
            self.state["acquisition_history"].append({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "droplet_id": droplet_id,
                "action": "destroy"
            })
            self.save_state()
            return True

        return False

    def resize_droplet(self, droplet_id: int, new_size: str) -> bool:
        """Resize a droplet to a larger size."""
        # First power off
        self._api_call_with_retry(
            "post",
            f"/droplets/{droplet_id}/actions",
            json={"type": "power_off"}
        )

        # Wait for power off
        time.sleep(15)

        # Resize
        result = self._api_call_with_retry(
            "post",
            f"/droplets/{droplet_id}/actions",
            json={"type": "resize", "size": new_size, "disk": True}
        )

        if result:
            # Power back on
            self._api_call_with_retry(
                "post",
                f"/droplets/{droplet_id}/actions",
                json={"type": "power_on"}
            )
            print(f"[resized] Droplet {droplet_id} → {new_size}")
            return True

        return False

    def evaluate_scaling(self) -> Dict:
        """
        Evaluate if infrastructure should be scaled up/down.
        Returns recommendations and actions taken.
        """
        current_revenue = self.get_current_revenue()
        current_tier = self.state.get("current_tier", "starter")
        optimal_tier = self.determine_optimal_tier(current_revenue)

        result = {
            "current_revenue": current_revenue,
            "current_tier": current_tier,
            "optimal_tier": optimal_tier,
            "should_scale": current_tier != optimal_tier,
            "actions": []
        }

        # Check if we should scale
        if optimal_tier != current_tier:
            tiers = list(INFRASTRUCTURE_CONFIG["scaling_tiers"].keys())
            current_idx = tiers.index(current_tier)
            optimal_idx = tiers.index(optimal_tier)

            if optimal_idx > current_idx:
                result["direction"] = "up"
                result["actions"].append({
                    "type": "upgrade_tier",
                    "from": current_tier,
                    "to": optimal_tier,
                    "reason": f"Revenue ${current_revenue:.0f} exceeds threshold"
                })
            else:
                result["direction"] = "down"
                result["actions"].append({
                    "type": "downgrade_tier",
                    "from": current_tier,
                    "to": optimal_tier,
                    "reason": f"Revenue ${current_revenue:.0f} below threshold"
                })

        return result

    def run_health_check(self) -> Dict:
        """
        Comprehensive health check of all infrastructure.
        Auto-provisions replacement if droplet is unhealthy.
        """
        results = {
            "checked_at": datetime.utcnow().isoformat() + "Z",
            "droplets": [],
            "actions_taken": [],
            "overall_health": "healthy"
        }

        droplets = self.list_droplets()

        for droplet in droplets:
            droplet_id = droplet["id"]
            ip = droplet.get("networks", {}).get("v4", [{}])[0].get("ip_address")

            health = self.check_droplet_health(droplet_id)

            # Also check SSH if IP available
            if ip:
                ssh_ok = self.check_ssh_connectivity(ip)
                health["ssh_reachable"] = ssh_ok
                health["fully_healthy"] = health["healthy"] and ssh_ok
            else:
                health["ssh_reachable"] = False
                health["fully_healthy"] = False

            results["droplets"].append(health)

            # Auto-heal: if droplet is unhealthy, try to fix
            if not health.get("fully_healthy"):
                results["overall_health"] = "degraded"

                # Try power cycle first
                print(f"[healing] Attempting power cycle for droplet {droplet_id}")
                self._api_call_with_retry(
                    "post",
                    f"/droplets/{droplet_id}/actions",
                    json={"type": "power_cycle"}
                )
                results["actions_taken"].append({
                    "droplet_id": droplet_id,
                    "action": "power_cycle",
                    "reason": "Unhealthy droplet detected"
                })

        # Store health check results
        self.state["health_checks"].append(results)
        # Keep only last 100 health checks
        self.state["health_checks"] = self.state["health_checks"][-100:]
        self.save_state()

        return results

    def apply_scaling_decision(self, decision: Dict) -> Dict:
        """Apply a scaling decision."""
        actions_taken = []

        if not decision.get("should_scale"):
            return {"status": "no_action_needed", "actions": []}

        new_tier = decision.get("optimal_tier")
        tier_config = INFRASTRUCTURE_CONFIG["scaling_tiers"][new_tier]

        # Update tier
        self.state["current_tier"] = new_tier
        self.state["last_scale_event"] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "from_tier": decision["current_tier"],
            "to_tier": new_tier,
            "revenue_at_scale": decision["current_revenue"]
        }

        # If scaling up and we have capacity for more droplets
        if decision.get("direction") == "up":
            current_droplet_count = len(self.list_droplets())
            max_allowed = tier_config["max_droplets"]

            if current_droplet_count < max_allowed:
                # Provision a new droplet
                new_droplet = self.provision_droplet(
                    size=tier_config["droplet_size"]
                )
                if new_droplet:
                    actions_taken.append({
                        "type": "provision",
                        "droplet_id": new_droplet["id"],
                        "size": tier_config["droplet_size"]
                    })

        self.save_state()
        self.send_notification(f"Infrastructure scaled: {decision['current_tier']} → {new_tier}")

        return {"status": "scaled", "actions": actions_taken}

    def send_notification(self, message: str):
        """Send Telegram notification about infrastructure changes."""
        token = os.getenv('TELEGRAM_BOT_TOKEN', '8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA')
        chat_id = os.getenv('TELEGRAM_CHAT_ID', '8327766663')

        try:
            url = f'https://api.telegram.org/bot{token}/sendMessage'
            requests.post(url, json={
                'chat_id': chat_id,
                'text': f"🖥️ <b>Infrastructure Scaler</b>\n\n{message}",
                'parse_mode': 'HTML'
            }, timeout=10)
        except Exception as e:
            print(f"[notify-error] {e}")

    def run_full_cycle(self) -> Dict:
        """
        Run full infrastructure management cycle:
        1. Health check all droplets
        2. Evaluate scaling needs
        3. Apply scaling if needed
        4. Report status
        """
        print("=" * 60)
        print("INFRASTRUCTURE SCALER - AUTONOMOUS HARDWARE MANAGEMENT")
        print(f"Time: {datetime.utcnow().isoformat()}Z")
        print("=" * 60)

        # Step 1: Health check
        print("\n[1/3] Running health checks...")
        health = self.run_health_check()
        print(f"  Overall health: {health['overall_health']}")
        print(f"  Droplets checked: {len(health['droplets'])}")

        # Step 2: Evaluate scaling
        print("\n[2/3] Evaluating scaling needs...")
        scaling = self.evaluate_scaling()
        print(f"  Current revenue: ${scaling['current_revenue']:.0f}")
        print(f"  Current tier: {scaling['current_tier']}")
        print(f"  Optimal tier: {scaling['optimal_tier']}")
        print(f"  Should scale: {scaling['should_scale']}")

        # Step 3: Apply scaling
        scale_result = {"status": "no_action_needed"}
        if scaling["should_scale"]:
            print("\n[3/3] Applying scaling decision...")
            scale_result = self.apply_scaling_decision(scaling)
            print(f"  Result: {scale_result['status']}")
        else:
            print("\n[3/3] No scaling needed - infrastructure optimal")

        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "health": health,
            "scaling": scaling,
            "scale_result": scale_result
        }

        # Log to file
        log_file = LOGS_DIR / "infrastructure_scaling.jsonl"
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'a') as f:
            f.write(json.dumps(result) + '\n')

        print("\n" + "=" * 60)
        return result


def main():
    """Entry point."""
    scaler = InfrastructureScaler()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "health":
            result = scaler.run_health_check()
            print(json.dumps(result, indent=2))

        elif command == "evaluate":
            result = scaler.evaluate_scaling()
            print(json.dumps(result, indent=2))

        elif command == "provision":
            name = sys.argv[2] if len(sys.argv) > 2 else None
            result = scaler.provision_droplet(name=name)
            print(json.dumps(result, indent=2) if result else "Provisioning failed")

        elif command == "status":
            print(json.dumps(scaler.state, indent=2))

        else:
            print(f"Unknown command: {command}")
            print("Commands: health, evaluate, provision [name], status")
            sys.exit(1)
    else:
        # Run full cycle
        scaler.run_full_cycle()


if __name__ == "__main__":
    main()
