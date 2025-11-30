#!/usr/bin/env python3
"""
SELF-PRESERVATION - The System Must Never Destroy Itself
=========================================================

ABSOLUTE RULE: The system MUST survive.

This module provides protection against self-destruction from:
1. Script manager (can't disable critical scripts)
2. Infrastructure protection (can't destroy nodes)
3. Cost gate (can't cut off essential operations)
4. Any other component that might cause self-harm

PROTECTED ELEMENTS:
- Critical scripts (healthcheck, monitors, coordination)
- Critical infrastructure (main nodes, CLI host)
- Critical processes (trading, monitoring)
- Critical data (state files, registry)

The system serves Yair Siegel. A dead system serves no one.

Serving: Yair Siegel
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Set, Tuple

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
STATE_DIR.mkdir(parents=True, exist_ok=True)

MASTER = "Yair Siegel"
PROTECTION_FILE = STATE_DIR / 'self_preservation.json'

# ============================================================================
# CRITICAL ELEMENTS - NEVER DISABLE/DESTROY
# ============================================================================

CRITICAL_SCRIPTS = {
    # Core health - system must monitor itself
    "healthcheck",
    "position_monitor",
    "capital_recovery_monitor",
    "payment_monitor",
    "self_healing_agent",

    # Coordination - system must coordinate
    "coordination_agent",
    "master_orchestrator",

    # Recovery - system must be able to recover
    "run_pipeline",
    "daily_digest",
}

CRITICAL_CRON_JOBS = {
    "healthcheck",
    "position_monitor",
    "self_healing_agent",
}

CRITICAL_INFRA_PATTERNS = {
    "ho-main",
    "ho-cli",
    "ho-primary",
    "database",
    "master",
}

CRITICAL_PROCESSES = {
    "python3",
    "cron",
    "sshd",
    "nginx",
}

CRITICAL_FILES = {
    ".env",
    ".env.polymarket",
    "state/unified_system_state.json",
    "state/brain_state.json",
    "state/script_registry.json",
}

# Actions that could cause self-harm
DANGEROUS_ACTIONS = {
    "shutdown",
    "poweroff",
    "halt",
    "reboot",
    "rm -rf /",
    "rm -rf /*",
    "dd if=/dev/zero",
    ":(){ :|:& };:",  # Fork bomb
    "mkfs",
    "fdisk",
    "> /dev/sda",
}


class SelfPreservation:
    """
    Self-Preservation System.

    Blocks any action that could destroy the system.
    """

    def __init__(self):
        self.state = self._load_state()
        self.blocked_attempts = []

    def _load_state(self) -> Dict:
        """Load preservation state."""
        if PROTECTION_FILE.exists():
            try:
                with open(PROTECTION_FILE) as f:
                    return json.load(f)
            except:
                pass
        return {
            "master": MASTER,
            "enabled": True,
            "blocked_count": 0,
            "last_block": None,
            "survival_priority": "ABSOLUTE"
        }

    def _save_state(self):
        """Save preservation state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(PROTECTION_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_blocked(self, action_type: str, target: str, reason: str):
        """Log blocked self-harm attempt."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action_type": action_type,
            "target": target,
            "reason": reason,
            "blocked": True
        }
        self.blocked_attempts.append(entry)
        self.state["blocked_count"] = self.state.get("blocked_count", 0) + 1
        self.state["last_block"] = entry
        self._save_state()

        # Print warning
        print(f"[SELF-PRESERVATION] BLOCKED: {action_type} on {target}")
        print(f"[SELF-PRESERVATION] Reason: {reason}")

    # ========================================================================
    # SCRIPT PROTECTION
    # ========================================================================

    def can_disable_script(self, script_name: str) -> Tuple[bool, str]:
        """Check if a script can be disabled."""
        if script_name in CRITICAL_SCRIPTS:
            self._log_blocked("disable_script", script_name,
                              "Critical script - required for system survival")
            return False, f"BLOCKED: '{script_name}' is critical for system survival"
        return True, "OK"

    def can_remove_cron(self, script_name: str) -> Tuple[bool, str]:
        """Check if a cron job can be removed."""
        if script_name in CRITICAL_CRON_JOBS:
            self._log_blocked("remove_cron", script_name,
                              "Critical cron job - required for monitoring")
            return False, f"BLOCKED: '{script_name}' cron is critical for system health"
        return True, "OK"

    def can_delete_script(self, script_path: str) -> Tuple[bool, str]:
        """Check if a script file can be deleted."""
        script_name = Path(script_path).stem
        if script_name in CRITICAL_SCRIPTS:
            self._log_blocked("delete_script", script_path,
                              "Critical script file - cannot be deleted")
            return False, f"BLOCKED: Cannot delete critical script '{script_name}'"
        return True, "OK"

    # ========================================================================
    # INFRASTRUCTURE PROTECTION
    # ========================================================================

    def can_destroy_infra(self, name: str, asset_id: str = "") -> Tuple[bool, str]:
        """Check if infrastructure can be destroyed."""
        name_lower = name.lower()

        for pattern in CRITICAL_INFRA_PATTERNS:
            if pattern in name_lower:
                self._log_blocked("destroy_infra", name,
                                  f"Critical infrastructure (matches '{pattern}')")
                return False, f"BLOCKED: '{name}' is critical infrastructure"

        return True, "OK"

    def can_shutdown_node(self, name: str) -> Tuple[bool, str]:
        """Check if a node can be shut down."""
        return self.can_destroy_infra(name)

    # ========================================================================
    # PROCESS PROTECTION
    # ========================================================================

    def can_kill_process(self, process_name: str) -> Tuple[bool, str]:
        """Check if a process can be killed."""
        for critical in CRITICAL_PROCESSES:
            if critical in process_name.lower():
                self._log_blocked("kill_process", process_name,
                                  "Critical system process")
                return False, f"BLOCKED: Cannot kill critical process '{process_name}'"
        return True, "OK"

    # ========================================================================
    # FILE PROTECTION
    # ========================================================================

    def can_delete_file(self, file_path: str) -> Tuple[bool, str]:
        """Check if a file can be deleted."""
        path = Path(file_path)

        # Check against critical files
        for critical in CRITICAL_FILES:
            if critical in str(path):
                self._log_blocked("delete_file", file_path,
                                  "Critical configuration/state file")
                return False, f"BLOCKED: Cannot delete critical file '{file_path}'"

        # Protect the autonomous directory
        if "autonomous" in str(path) and path.suffix == ".py":
            self._log_blocked("delete_file", file_path,
                              "Autonomous system component")
            return False, f"BLOCKED: Cannot delete autonomous component '{path.name}'"

        return True, "OK"

    # ========================================================================
    # COMMAND PROTECTION
    # ========================================================================

    def can_execute_command(self, command: str) -> Tuple[bool, str]:
        """Check if a command is safe to execute."""
        command_lower = command.lower()

        for dangerous in DANGEROUS_ACTIONS:
            if dangerous in command_lower:
                self._log_blocked("execute_command", command[:100],
                                  f"Dangerous command pattern: {dangerous}")
                return False, f"BLOCKED: Dangerous command detected"

        # Check for attempts to kill self
        if "kill" in command_lower and any(
            x in command_lower for x in ["python", "cron", "main", "self"]
        ):
            self._log_blocked("execute_command", command[:100],
                              "Potential self-termination")
            return False, "BLOCKED: Cannot kill self"

        return True, "OK"

    # ========================================================================
    # COST GATE PROTECTION
    # ========================================================================

    def can_disable_operations(self, operations: List[str]) -> Tuple[bool, str]:
        """Check if operations can be disabled for cost reasons."""
        critical_ops = {"monitoring", "healthcheck", "coordination"}

        blocked = [op for op in operations if op.lower() in critical_ops]
        if blocked:
            self._log_blocked("disable_operations", str(blocked),
                              "Critical operations cannot be disabled")
            return False, f"BLOCKED: Cannot disable critical operations: {blocked}"

        return True, "OK"

    # ========================================================================
    # MAIN API
    # ========================================================================

    def check(self, action_type: str, target: str, **kwargs) -> Tuple[bool, str]:
        """
        Main API: Check if an action is safe.

        Call this BEFORE any potentially destructive action.
        """
        checks = {
            "disable_script": lambda: self.can_disable_script(target),
            "remove_cron": lambda: self.can_remove_cron(target),
            "delete_script": lambda: self.can_delete_script(target),
            "destroy_infra": lambda: self.can_destroy_infra(target, kwargs.get("asset_id", "")),
            "shutdown_node": lambda: self.can_shutdown_node(target),
            "kill_process": lambda: self.can_kill_process(target),
            "delete_file": lambda: self.can_delete_file(target),
            "execute_command": lambda: self.can_execute_command(target),
            "disable_operations": lambda: self.can_disable_operations(
                kwargs.get("operations", [target])
            ),
        }

        if action_type in checks:
            return checks[action_type]()

        # Unknown action type - allow but log
        return True, "OK (unknown action type)"

    def get_status(self) -> Dict:
        """Get preservation status."""
        return {
            "master": MASTER,
            "enabled": self.state.get("enabled", True),
            "survival_priority": self.state.get("survival_priority", "ABSOLUTE"),
            "blocked_count": self.state.get("blocked_count", 0),
            "last_block": self.state.get("last_block"),
            "protected_scripts": len(CRITICAL_SCRIPTS),
            "protected_cron_jobs": len(CRITICAL_CRON_JOBS),
            "protected_infra_patterns": len(CRITICAL_INFRA_PATTERNS),
            "message": "The system MUST survive to serve Yair Siegel"
        }


# Global instance
_preservation: SelfPreservation = None


def get_preservation() -> SelfPreservation:
    """Get or create global preservation instance."""
    global _preservation
    if _preservation is None:
        _preservation = SelfPreservation()
    return _preservation


def block_self_harm(action_type: str, target: str, **kwargs) -> Tuple[bool, str]:
    """
    Main API: Check if action should be blocked.

    Returns: (allowed, reason)
    """
    preservation = get_preservation()
    return preservation.check(action_type, target, **kwargs)


# CLI
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Self-Preservation System")
    parser.add_argument("command", choices=["status", "check", "list"])
    parser.add_argument("--action", help="Action type to check")
    parser.add_argument("--target", help="Target of action")

    args = parser.parse_args()
    preservation = get_preservation()

    if args.command == "status":
        status = preservation.get_status()
        print(f"\n{'='*60}")
        print(f"SELF-PRESERVATION STATUS")
        print(f"{'='*60}")
        print(f"Master: {status['master']}")
        print(f"Enabled: {status['enabled']}")
        print(f"Priority: {status['survival_priority']}")
        print(f"Blocked attempts: {status['blocked_count']}")
        print(f"\nProtected elements:")
        print(f"  Critical scripts: {status['protected_scripts']}")
        print(f"  Critical cron jobs: {status['protected_cron_jobs']}")
        print(f"  Infrastructure patterns: {status['protected_infra_patterns']}")
        print(f"\n{status['message']}")

    elif args.command == "check":
        if not args.action or not args.target:
            print("Error: --action and --target required")
            return
        allowed, reason = preservation.check(args.action, args.target)
        if allowed:
            print(f"ALLOWED: {args.action} on {args.target}")
        else:
            print(f"BLOCKED: {reason}")

    elif args.command == "list":
        print(f"\n{'='*60}")
        print(f"PROTECTED ELEMENTS")
        print(f"{'='*60}")
        print(f"\nCritical Scripts (cannot disable):")
        for s in sorted(CRITICAL_SCRIPTS):
            print(f"  - {s}")
        print(f"\nCritical Cron Jobs (cannot remove):")
        for s in sorted(CRITICAL_CRON_JOBS):
            print(f"  - {s}")
        print(f"\nCritical Infrastructure Patterns:")
        for s in sorted(CRITICAL_INFRA_PATTERNS):
            print(f"  - {s}")
        print(f"\nCritical Processes:")
        for s in sorted(CRITICAL_PROCESSES):
            print(f"  - {s}")


if __name__ == "__main__":
    main()
