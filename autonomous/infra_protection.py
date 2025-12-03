#!/usr/bin/env python3
"""
INFRASTRUCTURE PROTECTION - Never Destroy Without Explicit Approval
=====================================================================

RULE: Infrastructure is PRESERVED by default.
- We build UP, not tear DOWN
- Every droplet has value (CLI, compute, storage, etc.)
- Destruction requires explicit human approval
- "Not immediately critical" != "destroy it"

This module:
1. Tracks all infrastructure assets
2. Assigns protection levels
3. Blocks destruction unless criteria met
4. Requires approval for any destruction

PROTECTION LEVELS:
- CRITICAL: Never destroy (main nodes, databases, CLI hosts)
- PROTECTED: 72h idle + approval required
- STANDARD: 168h (7 days) idle + approval required
- TEMPORARY: 24h idle can be destroyed (test instances only)

Serving: Yair Siegel
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
STATE_DIR.mkdir(parents=True, exist_ok=True)

MASTER = "Yair Siegel"
REGISTRY_FILE = STATE_DIR / 'infra_registry.json'
PROTECTION_LOG = STATE_DIR / 'infra_protection_log.jsonl'


# Protection level definitions
PROTECTION_LEVELS = {
    "CRITICAL": {
        "min_idle_hours": float('inf'),  # Never auto-destroy
        "requires_approval": True,
        "approval_type": "explicit_human",
        "description": "Never auto-destroy. Human approval only."
    },
    "PROTECTED": {
        "min_idle_hours": 72,  # 3 days
        "requires_approval": True,
        "approval_type": "explicit",
        "description": "72h idle + explicit approval required"
    },
    "STANDARD": {
        "min_idle_hours": 168,  # 7 days
        "requires_approval": True,
        "approval_type": "review",
        "description": "7 days idle + review required"
    },
    "TEMPORARY": {
        "min_idle_hours": 24,  # 1 day
        "requires_approval": False,
        "approval_type": "auto",
        "description": "Test instances, 24h idle can be recycled"
    }
}

# Auto-assign protection based on naming/purpose
PROTECTION_RULES = [
    # CRITICAL - Never destroy
    {"pattern": "ho-main", "level": "CRITICAL", "reason": "Main coordination node"},
    {"pattern": "ho-cli", "level": "CRITICAL", "reason": "CLI host - human interface"},
    {"pattern": "ho-primary", "level": "CRITICAL", "reason": "Primary infrastructure"},
    {"pattern": "pm-helper", "level": "CRITICAL", "reason": "Primary Polymarket helper - NEVER destroy"},
    {"pattern": "database", "level": "CRITICAL", "reason": "Data storage"},
    {"pattern": "db-", "level": "CRITICAL", "reason": "Database node"},
    {"pattern": "master", "level": "CRITICAL", "reason": "Master node"},

    # PROTECTED - Important but not critical
    {"pattern": "ho-compute", "level": "PROTECTED", "reason": "Compute node"},
    {"pattern": "ho-scale", "level": "PROTECTED", "reason": "Scaling node"},
    {"pattern": "ho-worker", "level": "PROTECTED", "reason": "Worker node"},
    {"pattern": "backup", "level": "PROTECTED", "reason": "Backup infrastructure"},

    # STANDARD - Regular infrastructure
    {"pattern": "ho-", "level": "STANDARD", "reason": "Hands-off infrastructure"},

    # TEMPORARY - Test instances only
    {"pattern": "test-", "level": "TEMPORARY", "reason": "Test instance"},
    {"pattern": "temp-", "level": "TEMPORARY", "reason": "Temporary instance"},
    {"pattern": "dev-", "level": "TEMPORARY", "reason": "Development instance"},
]


@dataclass
class InfraAsset:
    """Infrastructure asset record."""
    id: str
    name: str
    type: str  # droplet, volume, etc.
    protection_level: str
    protection_reason: str
    created: str
    last_active: str
    idle_hours: float
    destruction_blocked: bool
    block_reason: str


class InfraProtection:
    """
    Infrastructure Protection System.

    Blocks destruction of valuable infrastructure.
    """

    def __init__(self):
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict:
        """Load infrastructure registry."""
        if REGISTRY_FILE.exists():
            try:
                with open(REGISTRY_FILE) as f:
                    return json.load(f)
            except:
                pass
        return {
            "assets": {},
            "destruction_requests": [],
            "approved_destructions": [],
            "last_scan": None
        }

    def _save_registry(self):
        """Save infrastructure registry."""
        self.registry["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(REGISTRY_FILE, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def _log_protection_event(self, event_type: str, asset_id: str, details: Dict):
        """Log protection events."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "asset_id": asset_id,
            "details": details,
            "master": MASTER
        }
        with open(PROTECTION_LOG, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def assign_protection_level(self, name: str) -> Tuple[str, str]:
        """
        Assign protection level based on naming patterns.

        Returns: (level, reason)
        """
        name_lower = name.lower()

        for rule in PROTECTION_RULES:
            if rule["pattern"] in name_lower:
                return rule["level"], rule["reason"]

        # Default: STANDARD protection for anything hands-off related
        if "ho-" in name_lower or "hands" in name_lower:
            return "STANDARD", "Hands-off infrastructure (default protection)"

        # Unknown: Protect it anyway
        return "PROTECTED", "Unknown infrastructure - protected by default"

    def scan_infrastructure(self) -> List[InfraAsset]:
        """
        Scan all infrastructure and update registry.
        """
        assets = []

        try:
            # Get all droplets
            result = subprocess.run(
                ["doctl", "compute", "droplet", "list", "--format",
                 "ID,Name,Status,Created", "--no-header"],
                capture_output=True, text=True, timeout=30
            )

            now = datetime.now(timezone.utc)

            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 4:
                        droplet_id = parts[0]
                        name = parts[1]
                        status = parts[2]
                        created = parts[3] if len(parts) > 3 else now.isoformat()

                        # Assign protection
                        level, reason = self.assign_protection_level(name)

                        # Calculate idle time (estimate - in production use monitoring)
                        # For now, assume active unless powered off
                        idle_hours = 0 if status == "active" else 24

                        # Check destruction rules
                        destruction_blocked, block_reason = self._check_destruction_rules(
                            level, idle_hours
                        )

                        asset = InfraAsset(
                            id=droplet_id,
                            name=name,
                            type="droplet",
                            protection_level=level,
                            protection_reason=reason,
                            created=created,
                            last_active=now.isoformat() if status == "active" else "unknown",
                            idle_hours=idle_hours,
                            destruction_blocked=destruction_blocked,
                            block_reason=block_reason
                        )

                        assets.append(asset)

                        # Update registry
                        self.registry["assets"][droplet_id] = asdict(asset)

        except Exception as e:
            print(f"[INFRA PROTECTION] Scan error: {e}")

        self.registry["last_scan"] = datetime.now(timezone.utc).isoformat()
        self._save_registry()

        return assets

    def _check_destruction_rules(self, level: str, idle_hours: float) -> Tuple[bool, str]:
        """
        Check if destruction is allowed.

        Returns: (blocked, reason)
        """
        rules = PROTECTION_LEVELS.get(level, PROTECTION_LEVELS["STANDARD"])

        # Check idle time
        if idle_hours < rules["min_idle_hours"]:
            return True, f"Not idle long enough ({idle_hours:.0f}h < {rules['min_idle_hours']}h required)"

        # Check approval requirement
        if rules["requires_approval"]:
            return True, f"Requires {rules['approval_type']} approval"

        return False, "Destruction allowed by rules"

    def can_destroy(self, asset_id: str) -> Tuple[bool, str]:
        """
        Check if an asset can be destroyed.

        This is the MAIN GATE for all destruction operations.
        """
        # First, scan to ensure registry is current
        if asset_id not in self.registry.get("assets", {}):
            self.scan_infrastructure()

        asset = self.registry.get("assets", {}).get(asset_id)

        if not asset:
            # Unknown asset - BLOCK by default
            self._log_protection_event("destruction_blocked", asset_id, {
                "reason": "Unknown asset - blocked by default"
            })
            return False, "Unknown asset - destruction blocked by default"

        # Check if explicitly approved
        if asset_id in self.registry.get("approved_destructions", []):
            self._log_protection_event("destruction_approved", asset_id, {
                "reason": "Previously approved"
            })
            return True, "Destruction previously approved"

        # Check destruction rules
        blocked = asset.get("destruction_blocked", True)
        reason = asset.get("block_reason", "Blocked by protection policy")

        self._log_protection_event(
            "destruction_blocked" if blocked else "destruction_allowed",
            asset_id,
            {"level": asset.get("protection_level"), "reason": reason}
        )

        return not blocked, reason

    def request_destruction(self, asset_id: str, requestor: str, reason: str) -> Dict:
        """
        Request destruction of an asset.

        Creates a request that must be approved.
        """
        # Check current status
        can, block_reason = self.can_destroy(asset_id)

        request = {
            "asset_id": asset_id,
            "requestor": requestor,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "auto_approved": can,
            "block_reason": block_reason if not can else None,
            "status": "approved" if can else "pending_approval"
        }

        self.registry.setdefault("destruction_requests", []).append(request)
        self._save_registry()

        self._log_protection_event("destruction_requested", asset_id, request)

        return request

    def approve_destruction(self, asset_id: str, approver: str = MASTER) -> Dict:
        """
        Approve destruction of an asset.

        Only the master can approve critical destructions.
        """
        self.registry.setdefault("approved_destructions", []).append(asset_id)
        self._save_registry()

        self._log_protection_event("destruction_approved", asset_id, {
            "approver": approver,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return {"approved": True, "asset_id": asset_id, "approver": approver}

    def get_protection_report(self) -> Dict:
        """
        Get protection status report.
        """
        assets = self.scan_infrastructure()

        by_level = {}
        for asset in assets:
            level = asset.protection_level
            by_level.setdefault(level, []).append(asset.name)

        blocked_count = sum(1 for a in assets if a.destruction_blocked)

        return {
            "master": MASTER,
            "total_assets": len(assets),
            "protected_assets": blocked_count,
            "by_protection_level": {k: len(v) for k, v in by_level.items()},
            "assets_by_level": {k: v for k, v in by_level.items()},
            "pending_requests": len([r for r in self.registry.get("destruction_requests", [])
                                     if r.get("status") == "pending_approval"]),
            "policy": "PRESERVE by default. Build UP, never tear DOWN."
        }


# Global instance
_protection: Optional[InfraProtection] = None


def get_infra_protection() -> InfraProtection:
    """Get or create global protection instance."""
    global _protection
    if _protection is None:
        _protection = InfraProtection()
    return _protection


def block_destruction(asset_id: str) -> Tuple[bool, str]:
    """
    Main API: Check if destruction should be blocked.

    Call this BEFORE any destroy operation.
    """
    protection = get_infra_protection()
    can_destroy, reason = protection.can_destroy(asset_id)
    return not can_destroy, reason


# CLI
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Infrastructure Protection")
    parser.add_argument("command", choices=["scan", "report", "check", "approve"])
    parser.add_argument("--asset", help="Asset ID to check/approve")

    args = parser.parse_args()
    protection = get_infra_protection()

    if args.command == "scan":
        assets = protection.scan_infrastructure()
        print(f"\n{'='*60}")
        print(f"INFRASTRUCTURE SCAN - {len(assets)} assets found")
        print(f"{'='*60}")
        for asset in assets:
            status = "🔒" if asset.destruction_blocked else "⚠️"
            print(f"{status} {asset.name}")
            print(f"   Level: {asset.protection_level}")
            print(f"   Reason: {asset.protection_reason}")
            print(f"   Block: {asset.block_reason}")
        print(f"{'='*60}")

    elif args.command == "report":
        report = protection.get_protection_report()
        print(f"\n{'='*60}")
        print(f"INFRASTRUCTURE PROTECTION REPORT")
        print(f"{'='*60}")
        print(f"Total assets: {report['total_assets']}")
        print(f"Protected: {report['protected_assets']}")
        print(f"Pending destruction requests: {report['pending_requests']}")
        print(f"\nBy protection level:")
        for level, count in report['by_protection_level'].items():
            print(f"  {level}: {count}")
            for name in report['assets_by_level'].get(level, [])[:5]:
                print(f"    - {name}")
        print(f"\nPolicy: {report['policy']}")
        print(f"{'='*60}")

    elif args.command == "check":
        if not args.asset:
            print("Error: --asset required")
            return
        can, reason = protection.can_destroy(args.asset)
        if can:
            print(f"⚠️  Destruction ALLOWED: {reason}")
        else:
            print(f"🔒 Destruction BLOCKED: {reason}")

    elif args.command == "approve":
        if not args.asset:
            print("Error: --asset required")
            return
        result = protection.approve_destruction(args.asset)
        print(f"Approved: {result}")


if __name__ == "__main__":
    main()
