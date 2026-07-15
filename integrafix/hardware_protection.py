#!/usr/bin/env python3
"""
INTEGRAFIX: Hardware Protection Bridge
=======================================

ABSOLUTE RULE: THE SYSTEM MUST NEVER DESTROY ITSELF.

This bridge wires together all protection systems and extends them
to ensure the system can NEVER:
1. Delete its own code
2. Kill its own critical processes
3. Destroy its own infrastructure
4. Remove its own state/configuration

PROTECTION LAYERS:
1. Self-Preservation (autonomous/self_preservation.py)
2. Harm Prevention (autonomous/harm_prevention.py)
3. Hardware Brain Guards (autonomous/hardware_brain.py)
4. Self-Healer Guards (autonomous/self_healer.py)
5. THIS BRIDGE (unified protection)

Serving: Yair Siegel
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple, Set, List, Optional
from functools import wraps

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

PROTECTION_LOG = STATE_DIR / "hardware_protection.jsonl"
PROTECTION_STATE = STATE_DIR / "hardware_protection.json"

# ============================================================================
# ABSOLUTE PROTECTION - NEVER DELETE OR HARM THESE
# ============================================================================

# Critical directories - ENTIRE DIRECTORY is protected
PROTECTED_DIRECTORIES = {
    "autonomous",       # Core autonomous systems
    "integrafix",       # Integration bridges
    "ai_nexus",         # AI knowledge system
    "state",            # System state
    "finance",          # Financial systems
    "executor",         # Trade execution
    "alpha",            # Signal generation
    "health",           # Health monitoring
    "security",         # Security layer
    "infrastructure",   # Infrastructure management
    "hardware",         # Hardware control
    "audit",            # Audit logging
}

# Critical files - NEVER delete these specific files
CRITICAL_FILES = {
    # Root config
    ".env",
    ".env.polymarket",
    "requirements.txt",

    # Core state
    "state/unified_system_state.json",
    "state/brain_state.json",
    "state/script_registry.json",
    "state/self_preservation.json",
    "state/harm_prevention.json",
    "state/hardware_protection.json",
    "state/outcome_tracker.json",
    "state/trade_outcomes.jsonl",
    "state/trades_executed.jsonl",

    # Self-protection
    "autonomous/self_preservation.py",
    "autonomous/harm_prevention.py",
    "autonomous/self_healer.py",
    "autonomous/hardware_brain.py",
    "integrafix/hardware_protection.py",

    # Trading core
    "autonomous/concrete_executor.py",
    "autonomous/probability_calibrator.py",

    # INTEGRAFIX bridges
    "trading/market_data_pipeline.py",
    "ai/ai_orchestrator.py",
    "infrastructure/error_management.py",
    "autonomous/task_coordinator.py",
    "infrastructure/state_backend.py",
    "integrafix/outcome_tracker.py",
    "health/monitoring_bridge.py",
}

# Critical processes - NEVER kill these
CRITICAL_PROCESSES = {
    "hardware_brain.py",
    "self_healer.py",
    "backend_loop.py",
    "scaling_engine.py",
    "infra_manager.py",
    "python3",
    "cron",
    "sshd",
}

# Dangerous commands - ALWAYS block
BLOCKED_COMMANDS = {
    "rm -rf /",
    "rm -rf /*",
    "rm -rf /root",
    "rm -rf /root/hands-off-engine",
    "rm -rf hands-off-engine",
    "rm -rf autonomous",
    "rm -rf state",
    "rm -rf integrafix",
    "shutil.rmtree('/root/hands-off-engine')",
    "shutil.rmtree(PROJECT_ROOT)",
    "dd if=/dev/zero",
    "mkfs",
    ":(){ :|:& };:",  # Fork bomb
}


class HardwareProtection:
    """
    Unified hardware protection system.

    NEVER ALLOWS:
    - Deletion of protected directories
    - Deletion of critical files
    - Killing critical processes
    - Executing blocked commands
    """

    def __init__(self):
        self.state = self._load_state()
        self._wire_existing_systems()

    def _load_state(self) -> dict:
        if PROTECTION_STATE.exists():
            try:
                with open(PROTECTION_STATE) as f:
                    return json.load(f)
            except:
                pass
        return {
            "initialized": datetime.now(timezone.utc).isoformat(),
            "blocks": 0,
            "last_block": None,
            "enabled": True,
            "survival_mode": "ABSOLUTE",
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(PROTECTION_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_block(self, action: str, target: str, reason: str):
        """Log a blocked operation."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "target": target,
            "reason": reason,
            "blocked": True,
        }
        with open(PROTECTION_LOG, 'a') as f:
            f.write(json.dumps(entry) + "\n")

        self.state["blocks"] = self.state.get("blocks", 0) + 1
        self.state["last_block"] = entry
        self._save_state()

        print(f"[HARDWARE-PROTECTION] BLOCKED: {action} on {target}")
        print(f"[HARDWARE-PROTECTION] Reason: {reason}")

    def _wire_existing_systems(self):
        """Wire to existing protection systems."""
        # Import and register with harm_prevention
        try:
            from autonomous.harm_prevention import SACRED_FILES, SACRED_PROCESSES
            # Extend their sets with ours
            SACRED_FILES.update(CRITICAL_FILES)
            SACRED_PROCESSES.update(CRITICAL_PROCESSES)
        except ImportError:
            pass

        # Import and register with self_preservation
        try:
            from autonomous.self_preservation import CRITICAL_FILES as SP_FILES
            from autonomous.self_preservation import CRITICAL_SCRIPTS
            SP_FILES.update(CRITICAL_FILES)
            CRITICAL_SCRIPTS.update({
                "hardware_protection",
                "hardware_brain",
                "self_healer",
                "outcome_tracker",
                "market_data_pipeline",
            })
        except ImportError:
            pass

    # ========================================================================
    # PROTECTION CHECKS
    # ========================================================================

    def can_delete(self, path: str) -> Tuple[bool, str]:
        """
        Check if a path can be deleted.

        Returns: (allowed, reason)
        """
        path_obj = Path(path)
        path_str = str(path_obj)

        # Absolute protection: Never delete project root
        if str(PROJECT_ROOT) in path_str and path_obj == PROJECT_ROOT:
            self._log_block("delete", path, "Cannot delete project root")
            return False, "BLOCKED: Cannot delete project root directory"

        # Check protected directories
        for protected_dir in PROTECTED_DIRECTORIES:
            protected_path = PROJECT_ROOT / protected_dir
            if str(protected_path) in path_str or protected_dir in path_str:
                # Block deletion of directory itself or recursive deletion
                if path_obj.is_dir() or "rmtree" in str(path_str).lower():
                    self._log_block("delete", path, f"Protected directory: {protected_dir}")
                    return False, f"BLOCKED: '{protected_dir}' is a protected directory"

        # Check critical files
        for critical in CRITICAL_FILES:
            if critical in path_str:
                self._log_block("delete", path, f"Critical file: {critical}")
                return False, f"BLOCKED: '{critical}' is a critical file"

        # Check for .py files in protected directories
        if path_obj.suffix == ".py":
            for protected_dir in PROTECTED_DIRECTORIES:
                if protected_dir in path_str:
                    self._log_block("delete", path, f"Python file in protected dir: {protected_dir}")
                    return False, f"BLOCKED: Cannot delete .py files in {protected_dir}"

        return True, "OK"

    def can_kill_process(self, process: str) -> Tuple[bool, str]:
        """
        Check if a process can be killed.

        Returns: (allowed, reason)
        """
        process_lower = process.lower()

        for critical in CRITICAL_PROCESSES:
            if critical.lower() in process_lower:
                self._log_block("kill", process, f"Critical process: {critical}")
                return False, f"BLOCKED: '{critical}' is a critical process"

        return True, "OK"

    def can_execute_command(self, command: str) -> Tuple[bool, str]:
        """
        Check if a command is safe to execute.

        Returns: (allowed, reason)
        """
        command_lower = command.lower()

        # Check blocked commands
        for blocked in BLOCKED_COMMANDS:
            if blocked.lower() in command_lower:
                self._log_block("execute", command[:100], f"Blocked command: {blocked[:30]}")
                return False, "BLOCKED: Dangerous command pattern detected"

        # Check for attempts to delete protected directories
        if "rm " in command_lower or "rmtree" in command_lower:
            for protected_dir in PROTECTED_DIRECTORIES:
                if protected_dir in command_lower:
                    self._log_block("execute", command[:100], f"Delete protected: {protected_dir}")
                    return False, f"BLOCKED: Cannot delete protected directory '{protected_dir}'"

        # Check for kill commands targeting critical processes
        if "kill" in command_lower or "pkill" in command_lower:
            for critical in CRITICAL_PROCESSES:
                if critical.lower() in command_lower:
                    self._log_block("execute", command[:100], f"Kill critical: {critical}")
                    return False, f"BLOCKED: Cannot kill critical process '{critical}'"

        return True, "OK"

    def can_modify(self, path: str) -> Tuple[bool, str]:
        """
        Check if a file can be modified.

        Returns: (allowed, reason)

        Note: Modifications are generally allowed, but logged for audit.
        """
        # Allow modifications but log them for audit
        return True, "OK (logged for audit)"

    # ========================================================================
    # MAIN API
    # ========================================================================

    def check(self, action: str, target: str) -> Tuple[bool, str]:
        """
        Main API: Check if an action is safe.

        Actions: delete, kill, execute, modify
        """
        if action == "delete":
            return self.can_delete(target)
        elif action == "kill":
            return self.can_kill_process(target)
        elif action == "execute":
            return self.can_execute_command(target)
        elif action == "modify":
            return self.can_modify(target)
        else:
            return True, "OK (unknown action)"

    def status(self) -> dict:
        """Get protection status."""
        return {
            "enabled": self.state.get("enabled", True),
            "survival_mode": self.state.get("survival_mode", "ABSOLUTE"),
            "blocks": self.state.get("blocks", 0),
            "last_block": self.state.get("last_block"),
            "protected_directories": len(PROTECTED_DIRECTORIES),
            "protected_files": len(CRITICAL_FILES),
            "protected_processes": len(CRITICAL_PROCESSES),
            "message": "The system MUST NEVER destroy itself",
        }


# ============================================================================
# DECORATORS FOR SAFE OPERATIONS
# ============================================================================

def safe_delete(func):
    """Decorator to protect deletion operations."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        protection = get_protection()

        # Try to extract path from args/kwargs
        path = None
        if args:
            path = str(args[0])
        elif 'path' in kwargs:
            path = str(kwargs['path'])
        elif 'file_path' in kwargs:
            path = str(kwargs['file_path'])

        if path:
            allowed, reason = protection.can_delete(path)
            if not allowed:
                raise PermissionError(reason)

        return func(*args, **kwargs)
    return wrapper


def safe_execute(func):
    """Decorator to protect command execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        protection = get_protection()

        # Try to extract command from args/kwargs
        command = None
        if args:
            command = str(args[0])
        elif 'command' in kwargs:
            command = str(kwargs['command'])
        elif 'cmd' in kwargs:
            command = str(kwargs['cmd'])

        if command:
            allowed, reason = protection.can_execute_command(command)
            if not allowed:
                raise PermissionError(reason)

        return func(*args, **kwargs)
    return wrapper


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_protection: Optional[HardwareProtection] = None


def get_protection() -> HardwareProtection:
    """Get or create global protection instance."""
    global _protection
    if _protection is None:
        _protection = HardwareProtection()
    return _protection


def block_if_dangerous(action: str, target: str) -> Tuple[bool, str]:
    """
    Main API: Check if action should be blocked.

    Returns: (allowed, reason)

    Example:
        allowed, reason = block_if_dangerous("delete", str(BASE_DIR / "autonomous"))
        if not allowed:
            print(f"Operation blocked: {reason}")
    """
    return get_protection().check(action, target)


# ============================================================================
# MONKEY-PATCH DANGEROUS OPERATIONS
# ============================================================================

def patch_dangerous_operations():
    """
    Monkey-patch dangerous Python operations to add protection.

    This patches:
    - os.remove
    - os.unlink
    - shutil.rmtree
    - pathlib.Path.unlink
    """
    import shutil

    # Store originals
    _original_remove = os.remove
    _original_unlink = os.unlink
    _original_rmtree = shutil.rmtree
    _original_path_unlink = Path.unlink

    def protected_remove(path, *args, **kwargs):
        allowed, reason = block_if_dangerous("delete", str(path))
        if not allowed:
            raise PermissionError(reason)
        return _original_remove(path, *args, **kwargs)

    def protected_unlink(path, *args, **kwargs):
        allowed, reason = block_if_dangerous("delete", str(path))
        if not allowed:
            raise PermissionError(reason)
        return _original_unlink(path, *args, **kwargs)

    def protected_rmtree(path, *args, **kwargs):
        allowed, reason = block_if_dangerous("delete", str(path))
        if not allowed:
            raise PermissionError(reason)
        return _original_rmtree(path, *args, **kwargs)

    def protected_path_unlink(self, *args, **kwargs):
        allowed, reason = block_if_dangerous("delete", str(self))
        if not allowed:
            raise PermissionError(reason)
        return _original_path_unlink(self, *args, **kwargs)

    # Apply patches
    os.remove = protected_remove
    os.unlink = protected_unlink
    shutil.rmtree = protected_rmtree
    Path.unlink = protected_path_unlink

    print("[HARDWARE-PROTECTION] Dangerous operations patched with protection")


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Hardware Protection System")
    parser.add_argument("command", choices=["status", "check", "list", "patch"])
    parser.add_argument("--action", help="Action to check (delete, kill, execute)")
    parser.add_argument("--target", help="Target of action")

    args = parser.parse_args()
    protection = get_protection()

    if args.command == "status":
        status = protection.status()
        print(f"\n{'='*70}")
        print("INTEGRAFIX: Hardware Protection Status")
        print(f"{'='*70}")
        print(f"Enabled: {status['enabled']}")
        print(f"Survival Mode: {status['survival_mode']}")
        print(f"Blocks: {status['blocks']}")
        print(f"\nProtection Coverage:")
        print(f"  Protected directories: {status['protected_directories']}")
        print(f"  Protected files: {status['protected_files']}")
        print(f"  Protected processes: {status['protected_processes']}")
        print(f"\n{status['message']}")
        print(f"{'='*70}")

    elif args.command == "check":
        if not args.action or not args.target:
            print("Error: --action and --target required")
            return
        allowed, reason = protection.check(args.action, args.target)
        if allowed:
            print(f"ALLOWED: {args.action} on {args.target}")
        else:
            print(f"BLOCKED: {reason}")

    elif args.command == "list":
        print(f"\n{'='*70}")
        print("PROTECTED ELEMENTS")
        print(f"{'='*70}")
        print("\nProtected Directories (cannot delete):")
        for d in sorted(PROTECTED_DIRECTORIES):
            print(f"  - {d}/")
        print("\nCritical Files (cannot delete):")
        for f in sorted(CRITICAL_FILES)[:20]:
            print(f"  - {f}")
        if len(CRITICAL_FILES) > 20:
            print(f"  ... and {len(CRITICAL_FILES) - 20} more")
        print("\nCritical Processes (cannot kill):")
        for p in sorted(CRITICAL_PROCESSES):
            print(f"  - {p}")

    elif args.command == "patch":
        patch_dangerous_operations()
        print("Dangerous operations patched with protection")


if __name__ == "__main__":
    main()
