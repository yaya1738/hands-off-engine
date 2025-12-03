#!/usr/bin/env python3
"""
HARM PREVENTION - Protection Against Well-Intentioned Damage
=============================================================

The road to system failure is paved with good intentions.

This module protects against:
1. Auto-healing that makes things worse
2. Optimizations that break functionality
3. Updates that cause regressions
4. Cleanup that removes needed components
5. Configuration changes with unintended consequences

PHILOSOPHY:
- Every "helpful" change must prove it helps before full deployment
- Changes that hurt can be rolled back
- The system learns from past harmful help
- Rate limit automatic changes to prevent cascading failures
- Validate against known-good state before changing

Serving: Yair Siegel
"""

import json
import os
import hashlib
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
STATE_DIR.mkdir(parents=True, exist_ok=True)

MASTER = "Yair Siegel"
HARM_PREVENTION_FILE = STATE_DIR / 'harm_prevention.json'
CHANGE_LOG_FILE = STATE_DIR / 'change_log.jsonl'
ROLLBACK_DIR = BASE_DIR / 'rollbacks'
ROLLBACK_DIR.mkdir(parents=True, exist_ok=True)


class ChangeType(Enum):
    """Types of changes that could cause harm."""
    CONFIG_CHANGE = "config_change"
    FILE_MODIFICATION = "file_modification"
    PROCESS_ACTION = "process_action"
    RESOURCE_CLEANUP = "resource_cleanup"
    AUTO_HEAL = "auto_heal"
    OPTIMIZATION = "optimization"
    UPDATE = "update"
    SCALING = "scaling"


class Outcome(Enum):
    """Outcome of a change."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"
    HARMFUL = "harmful"
    ROLLED_BACK = "rolled_back"


@dataclass
class ChangeRecord:
    """Record of a change and its effects."""
    change_id: str
    change_type: ChangeType
    description: str
    target: str
    timestamp: str
    intention: str  # What was the change trying to achieve?
    pre_state: Dict  # State before change
    post_state: Optional[Dict] = None  # State after change
    outcome: Outcome = Outcome.PENDING
    harm_detected: bool = False
    harm_description: str = ""
    rollback_available: bool = False
    rollback_path: str = ""
    validated: bool = False


# ============================================================================
# KNOWN HARMFUL PATTERNS - Learned from experience
# ============================================================================

KNOWN_HARMFUL_PATTERNS = {
    # Pattern: (description, harm_type, severity)
    "restart_loop": (
        "Restarting a service that keeps failing without fixing root cause",
        "infinite_loop",
        "high"
    ),
    "aggressive_cleanup": (
        "Removing 'unused' files that are actually needed",
        "data_loss",
        "critical"
    ),
    "memory_optimization": (
        "Killing processes to free memory without understanding dependencies",
        "service_disruption",
        "high"
    ),
    "auto_update": (
        "Updating dependencies without testing for breaking changes",
        "regression",
        "high"
    ),
    "auto_scale_down": (
        "Scaling down resources during perceived low usage",
        "capacity_loss",
        "medium"
    ),
    "config_reset": (
        "Resetting config to 'defaults' losing customizations",
        "config_loss",
        "high"
    ),
    "aggressive_caching": (
        "Caching data that should be fresh",
        "stale_data",
        "medium"
    ),
    "permission_fix": (
        "Changing permissions 'for security' breaking functionality",
        "access_loss",
        "high"
    ),
    "log_rotation": (
        "Rotating logs too aggressively losing debug info",
        "debug_loss",
        "low"
    ),
    "connection_cleanup": (
        "Closing 'idle' connections that are actually in use",
        "connection_loss",
        "medium"
    ),
    "code_deletion": (
        "Deleting source code files or directories",
        "self_destruction",
        "critical"
    ),
    "self_termination": (
        "Killing own critical processes",
        "self_destruction",
        "critical"
    ),
    "state_wipe": (
        "Deleting or clearing state files",
        "data_loss",
        "critical"
    ),
}

# Files that should NEVER be "optimized" or "cleaned"
SACRED_FILES = {
    ".env",
    ".env.polymarket",
    "state/unified_system_state.json",
    "state/brain_state.json",
    "state/script_registry.json",
    "state/self_preservation.json",
    "state/harm_prevention.json",
    "state/hardware_protection.json",
    "state/outcome_tracker.json",
    "autonomous/self_preservation.py",
    "autonomous/security_layer.py",
    "autonomous/harm_prevention.py",
    "autonomous/self_healer.py",
    "autonomous/hardware_brain.py",
    "autonomous/concrete_executor.py",
    "integrafix/hardware_protection.py",
    "integrafix/outcome_tracker.py",
    "trading/market_data_pipeline.py",
    "ai/ai_orchestrator.py",
}

# Processes that should never be "optimized" by killing
SACRED_PROCESSES = {
    "python3",
    "cron",
    "sshd",
    "nginx",
    "postgres",
    "redis",
    "hardware_brain.py",
    "self_healer.py",
    "backend_loop.py",
    "scaling_engine.py",
    "infra_manager.py",
}

# Config keys that should never be "reset" or "optimized"
SACRED_CONFIG_KEYS = {
    "master",
    "api_key",
    "private_key",
    "wallet_address",
    "enabled",
    "survival_priority",
}


class HarmPrevention:
    """
    Harm Prevention System.

    Validates, monitors, and can rollback "helpful" changes.
    """

    def __init__(self):
        self.state = self._load_state()
        self.change_history: List[ChangeRecord] = []
        self._lock = threading.Lock()

    def _load_state(self) -> Dict:
        """Load harm prevention state."""
        if HARM_PREVENTION_FILE.exists():
            try:
                with open(HARM_PREVENTION_FILE) as f:
                    return json.load(f)
            except:
                pass
        return {
            "master": MASTER,
            "enabled": True,
            "total_changes": 0,
            "harmful_changes": 0,
            "rollbacks": 0,
            "learned_patterns": [],
            "rate_limit": {
                "max_changes_per_hour": 10,
                "current_hour_changes": 0,
                "hour_start": datetime.now(timezone.utc).isoformat()
            }
        }

    def _save_state(self):
        """Save harm prevention state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(HARM_PREVENTION_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_change(self, record: ChangeRecord):
        """Log a change to the change log."""
        with open(CHANGE_LOG_FILE, 'a') as f:
            data = asdict(record)
            data['change_type'] = record.change_type.value
            data['outcome'] = record.outcome.value
            f.write(json.dumps(data) + "\n")

    def _generate_change_id(self) -> str:
        """Generate unique change ID."""
        return hashlib.sha256(
            f"{datetime.now(timezone.utc).isoformat()}-{os.urandom(8).hex()}".encode()
        ).hexdigest()[:16]

    # ========================================================================
    # RATE LIMITING
    # ========================================================================

    def _check_rate_limit(self) -> Tuple[bool, str]:
        """Check if we're within rate limits for changes."""
        with self._lock:
            now = datetime.now(timezone.utc)
            hour_start = datetime.fromisoformat(
                self.state["rate_limit"]["hour_start"].replace('Z', '+00:00')
            )

            # Reset if new hour
            if (now - hour_start).total_seconds() > 3600:
                self.state["rate_limit"]["current_hour_changes"] = 0
                self.state["rate_limit"]["hour_start"] = now.isoformat()
                self._save_state()

            current = self.state["rate_limit"]["current_hour_changes"]
            max_allowed = self.state["rate_limit"]["max_changes_per_hour"]

            if current >= max_allowed:
                return False, f"Rate limit exceeded: {current}/{max_allowed} changes this hour"

            return True, f"Within limits: {current}/{max_allowed}"

    def _increment_rate_limit(self):
        """Increment the rate limit counter."""
        with self._lock:
            self.state["rate_limit"]["current_hour_changes"] += 1
            self._save_state()

    # ========================================================================
    # PRE-CHANGE VALIDATION
    # ========================================================================

    def validate_change(
        self,
        change_type: ChangeType,
        target: str,
        intention: str,
        **kwargs
    ) -> Tuple[bool, str, Optional[ChangeRecord]]:
        """
        Validate a proposed change before execution.

        Returns: (allowed, reason, change_record)
        """
        # Rate limit check
        allowed, reason = self._check_rate_limit()
        if not allowed:
            return False, reason, None

        # Check against known harmful patterns
        harmful = self._check_harmful_patterns(change_type, target, intention)
        if harmful:
            pattern_name, harm_info = harmful
            return False, (
                f"BLOCKED: Matches known harmful pattern '{pattern_name}': "
                f"{harm_info[0]} (severity: {harm_info[2]})"
            ), None

        # Check sacred files
        if change_type in [ChangeType.FILE_MODIFICATION, ChangeType.RESOURCE_CLEANUP]:
            if self._is_sacred_file(target):
                return False, f"BLOCKED: '{target}' is a sacred file - cannot be modified by automation", None

        # Check sacred processes
        if change_type in [ChangeType.PROCESS_ACTION, ChangeType.OPTIMIZATION]:
            if self._is_sacred_process(target):
                return False, f"BLOCKED: '{target}' is a sacred process - cannot be killed/optimized", None

        # Check sacred config
        if change_type == ChangeType.CONFIG_CHANGE:
            config_key = kwargs.get("config_key", "")
            if config_key in SACRED_CONFIG_KEYS:
                return False, f"BLOCKED: '{config_key}' is a sacred config key - cannot be auto-modified", None

        # Capture pre-state for rollback
        pre_state = self._capture_state(change_type, target)

        # Create change record
        record = ChangeRecord(
            change_id=self._generate_change_id(),
            change_type=change_type,
            description=kwargs.get("description", f"{change_type.value} on {target}"),
            target=target,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intention=intention,
            pre_state=pre_state,
            validated=True
        )

        # Create rollback point
        rollback_path = self._create_rollback_point(record)
        if rollback_path:
            record.rollback_available = True
            record.rollback_path = rollback_path

        self._increment_rate_limit()
        self.state["total_changes"] = self.state.get("total_changes", 0) + 1
        self._save_state()

        return True, "Change validated and rollback point created", record

    def _check_harmful_patterns(
        self,
        change_type: ChangeType,
        target: str,
        intention: str
    ) -> Optional[Tuple[str, Tuple]]:
        """Check if change matches known harmful patterns."""
        intention_lower = intention.lower()
        target_lower = target.lower()

        # Check for restart loop pattern
        if change_type == ChangeType.AUTO_HEAL:
            if "restart" in intention_lower:
                # Check if this target has been restarted recently
                recent_restarts = self._count_recent_actions(target, "restart", hours=1)
                if recent_restarts >= 3:
                    return ("restart_loop", KNOWN_HARMFUL_PATTERNS["restart_loop"])

        # Check for aggressive cleanup
        if change_type == ChangeType.RESOURCE_CLEANUP:
            if any(word in intention_lower for word in ["unused", "old", "cleanup", "remove"]):
                return ("aggressive_cleanup", KNOWN_HARMFUL_PATTERNS["aggressive_cleanup"])

        # Check for memory optimization
        if change_type == ChangeType.OPTIMIZATION:
            if "memory" in intention_lower and "kill" in intention_lower:
                return ("memory_optimization", KNOWN_HARMFUL_PATTERNS["memory_optimization"])

        # Check for auto update
        if change_type == ChangeType.UPDATE:
            if "auto" in intention_lower or "automatic" in intention_lower:
                return ("auto_update", KNOWN_HARMFUL_PATTERNS["auto_update"])

        # Check for config reset
        if change_type == ChangeType.CONFIG_CHANGE:
            if any(word in intention_lower for word in ["reset", "default", "restore"]):
                return ("config_reset", KNOWN_HARMFUL_PATTERNS["config_reset"])

        # Check for learned patterns
        for pattern in self.state.get("learned_patterns", []):
            if pattern["target"] in target_lower or pattern["intention"] in intention_lower:
                return (pattern["name"], (pattern["description"], pattern["harm_type"], "learned"))

        return None

    def _is_sacred_file(self, target: str) -> bool:
        """Check if file is sacred."""
        for sacred in SACRED_FILES:
            if sacred in target:
                return True
        return False

    def _is_sacred_process(self, target: str) -> bool:
        """Check if process is sacred."""
        target_lower = target.lower()
        for sacred in SACRED_PROCESSES:
            if sacred in target_lower:
                return True
        return False

    def _capture_state(self, change_type: ChangeType, target: str) -> Dict:
        """Capture current state before change."""
        state = {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "target": target,
            "type": change_type.value
        }

        # Capture file state
        if change_type == ChangeType.FILE_MODIFICATION:
            path = Path(target) if target.startswith('/') else BASE_DIR / target
            if path.exists():
                state["file_exists"] = True
                state["file_size"] = path.stat().st_size
                state["file_mtime"] = path.stat().st_mtime
                if path.stat().st_size < 100000:  # Only hash small files
                    with open(path, 'rb') as f:
                        state["file_hash"] = hashlib.sha256(f.read()).hexdigest()

        # Capture process state
        elif change_type == ChangeType.PROCESS_ACTION:
            try:
                result = subprocess.run(
                    ["pgrep", "-f", target],
                    capture_output=True, text=True, timeout=5
                )
                state["process_pids"] = result.stdout.strip().split('\n') if result.stdout.strip() else []
            except:
                state["process_pids"] = []

        # Capture config state
        elif change_type == ChangeType.CONFIG_CHANGE:
            config_path = BASE_DIR / target if not target.startswith('/') else Path(target)
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        state["config_content"] = json.load(f)
                except:
                    pass

        return state

    def _create_rollback_point(self, record: ChangeRecord) -> Optional[str]:
        """Create a rollback point for the change."""
        rollback_dir = ROLLBACK_DIR / record.change_id
        rollback_dir.mkdir(exist_ok=True)

        try:
            # For file modifications, copy the file
            if record.change_type == ChangeType.FILE_MODIFICATION:
                path = Path(record.target) if record.target.startswith('/') else BASE_DIR / record.target
                if path.exists():
                    shutil.copy2(path, rollback_dir / path.name)

            # For config changes, save the config
            elif record.change_type == ChangeType.CONFIG_CHANGE:
                if record.pre_state.get("config_content"):
                    with open(rollback_dir / "config_backup.json", 'w') as f:
                        json.dump(record.pre_state["config_content"], f, indent=2)

            # Save the record itself
            with open(rollback_dir / "record.json", 'w') as f:
                data = asdict(record)
                data['change_type'] = record.change_type.value
                data['outcome'] = record.outcome.value
                json.dump(data, f, indent=2)

            return str(rollback_dir)

        except Exception as e:
            print(f"[HARM-PREVENTION] Failed to create rollback point: {e}")
            return None

    def _count_recent_actions(self, target: str, action: str, hours: int = 1) -> int:
        """Count recent similar actions on a target."""
        if not CHANGE_LOG_FILE.exists():
            return 0

        count = 0
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        try:
            with open(CHANGE_LOG_FILE) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entry_time = datetime.fromisoformat(
                            entry["timestamp"].replace('Z', '+00:00')
                        )
                        if entry_time > cutoff:
                            if target in entry.get("target", "") and action in entry.get("intention", "").lower():
                                count += 1
                    except:
                        continue
        except:
            pass

        return count

    # ========================================================================
    # POST-CHANGE MONITORING
    # ========================================================================

    def report_outcome(
        self,
        record: ChangeRecord,
        success: bool,
        post_state: Optional[Dict] = None,
        harm_description: str = ""
    ) -> Tuple[bool, str]:
        """
        Report the outcome of a change.

        If harmful, triggers learning and potential rollback.
        """
        record.post_state = post_state or {}

        if success:
            record.outcome = Outcome.SUCCESS
            self._log_change(record)
            return True, "Change completed successfully"

        # Change failed or caused harm
        record.outcome = Outcome.HARMFUL
        record.harm_detected = True
        record.harm_description = harm_description

        self.state["harmful_changes"] = self.state.get("harmful_changes", 0) + 1
        self._save_state()

        # Learn from this harmful change
        self._learn_from_harm(record)

        # Log the harmful change
        self._log_change(record)

        # Offer rollback
        if record.rollback_available:
            return False, f"HARMFUL CHANGE DETECTED: {harm_description}. Rollback available at {record.rollback_path}"

        return False, f"HARMFUL CHANGE DETECTED: {harm_description}. No rollback available."

    def _learn_from_harm(self, record: ChangeRecord):
        """Learn from a harmful change to prevent similar issues."""
        learned = {
            "name": f"learned_{record.change_id[:8]}",
            "target": record.target,
            "intention": record.intention,
            "description": record.harm_description,
            "harm_type": "learned_from_experience",
            "change_type": record.change_type.value,
            "learned_at": datetime.now(timezone.utc).isoformat()
        }

        if "learned_patterns" not in self.state:
            self.state["learned_patterns"] = []

        self.state["learned_patterns"].append(learned)
        self._save_state()

        print(f"[HARM-PREVENTION] Learned new harmful pattern: {learned['name']}")

    # ========================================================================
    # ROLLBACK
    # ========================================================================

    def rollback(self, change_id: str) -> Tuple[bool, str]:
        """Rollback a harmful change."""
        rollback_dir = ROLLBACK_DIR / change_id

        if not rollback_dir.exists():
            return False, f"No rollback point found for change {change_id}"

        record_file = rollback_dir / "record.json"
        if not record_file.exists():
            return False, "Rollback record not found"

        try:
            with open(record_file) as f:
                record_data = json.load(f)

            change_type = ChangeType(record_data["change_type"])
            target = record_data["target"]

            # Perform rollback based on type
            if change_type == ChangeType.FILE_MODIFICATION:
                # Find the backup file
                for backup_file in rollback_dir.glob("*"):
                    if backup_file.name not in ["record.json", "config_backup.json"]:
                        target_path = Path(target) if target.startswith('/') else BASE_DIR / target
                        shutil.copy2(backup_file, target_path)
                        break

            elif change_type == ChangeType.CONFIG_CHANGE:
                config_backup = rollback_dir / "config_backup.json"
                if config_backup.exists():
                    target_path = Path(target) if target.startswith('/') else BASE_DIR / target
                    shutil.copy2(config_backup, target_path)

            self.state["rollbacks"] = self.state.get("rollbacks", 0) + 1
            self._save_state()

            return True, f"Successfully rolled back change {change_id}"

        except Exception as e:
            return False, f"Rollback failed: {e}"

    # ========================================================================
    # CANARY TESTING
    # ========================================================================

    def canary_test(
        self,
        test_func: Callable,
        success_check: Callable[[], bool],
        timeout_seconds: int = 30
    ) -> Tuple[bool, str]:
        """
        Run a canary test before full deployment.

        test_func: Function to execute the change
        success_check: Function that returns True if system is healthy
        timeout_seconds: How long to wait before checking
        """
        # Check health before
        try:
            before_healthy = success_check()
            if not before_healthy:
                return False, "System unhealthy before canary test - aborting"
        except Exception as e:
            return False, f"Health check failed before test: {e}"

        # Execute the test
        try:
            test_func()
        except Exception as e:
            return False, f"Canary test execution failed: {e}"

        # Wait and check
        time.sleep(min(timeout_seconds, 60))  # Max 60 seconds

        try:
            after_healthy = success_check()
            if after_healthy:
                return True, "Canary test passed - system remains healthy"
            else:
                return False, "Canary test FAILED - system became unhealthy after change"
        except Exception as e:
            return False, f"Health check failed after test: {e}"

    # ========================================================================
    # STATUS
    # ========================================================================

    def get_status(self) -> Dict:
        """Get harm prevention status."""
        return {
            "master": MASTER,
            "enabled": self.state.get("enabled", True),
            "total_changes": self.state.get("total_changes", 0),
            "harmful_changes": self.state.get("harmful_changes", 0),
            "rollbacks": self.state.get("rollbacks", 0),
            "learned_patterns": len(self.state.get("learned_patterns", [])),
            "rate_limit": self.state.get("rate_limit", {}),
            "sacred_files": len(SACRED_FILES),
            "sacred_processes": len(SACRED_PROCESSES),
            "known_harmful_patterns": len(KNOWN_HARMFUL_PATTERNS),
            "message": "Protecting against well-intentioned harm"
        }


# ============================================================================
# DECORATORS FOR SAFE CHANGES
# ============================================================================

def safe_change(
    change_type: ChangeType,
    intention: str,
    target_param: str = "target"
):
    """
    Decorator to wrap functions that make changes.

    Validates the change before execution and monitors outcome.
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            prevention = get_harm_prevention()

            # Get target from kwargs or first arg
            target = kwargs.get(target_param, args[0] if args else "unknown")

            # Validate change
            allowed, reason, record = prevention.validate_change(
                change_type=change_type,
                target=str(target),
                intention=intention
            )

            if not allowed:
                print(f"[HARM-PREVENTION] {reason}")
                return None

            # Execute with monitoring
            try:
                result = func(*args, **kwargs)

                # Report success
                prevention.report_outcome(record, success=True)

                return result

            except Exception as e:
                # Report failure/harm
                prevention.report_outcome(
                    record,
                    success=False,
                    harm_description=str(e)
                )
                raise

        return wrapper
    return decorator


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_harm_prevention: HarmPrevention = None


def get_harm_prevention() -> HarmPrevention:
    """Get or create global harm prevention instance."""
    global _harm_prevention
    if _harm_prevention is None:
        _harm_prevention = HarmPrevention()
    return _harm_prevention


def validate_helpful_action(
    change_type: str,
    target: str,
    intention: str,
    **kwargs
) -> Tuple[bool, str]:
    """
    Main API: Validate a helpful action before execution.

    Returns: (allowed, reason)
    """
    prevention = get_harm_prevention()

    try:
        ct = ChangeType(change_type)
    except ValueError:
        ct = ChangeType.CONFIG_CHANGE  # Default

    allowed, reason, _ = prevention.validate_change(ct, target, intention, **kwargs)
    return allowed, reason


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Harm Prevention System")
    parser.add_argument("command", choices=["status", "patterns", "validate", "history", "rollback"])
    parser.add_argument("--type", help="Change type")
    parser.add_argument("--target", help="Target of change")
    parser.add_argument("--intention", help="Intention of change")
    parser.add_argument("--change-id", help="Change ID for rollback")

    args = parser.parse_args()
    prevention = get_harm_prevention()

    if args.command == "status":
        status = prevention.get_status()
        print(f"\n{'='*60}")
        print(f"HARM PREVENTION STATUS")
        print(f"{'='*60}")
        print(f"Master: {status['master']}")
        print(f"Enabled: {status['enabled']}")
        print(f"\nStatistics:")
        print(f"  Total changes monitored: {status['total_changes']}")
        print(f"  Harmful changes detected: {status['harmful_changes']}")
        print(f"  Rollbacks performed: {status['rollbacks']}")
        print(f"  Learned patterns: {status['learned_patterns']}")
        print(f"\nProtection:")
        print(f"  Sacred files: {status['sacred_files']}")
        print(f"  Sacred processes: {status['sacred_processes']}")
        print(f"  Known harmful patterns: {status['known_harmful_patterns']}")
        print(f"\nRate limit:")
        print(f"  Max per hour: {status['rate_limit'].get('max_changes_per_hour', 10)}")
        print(f"  This hour: {status['rate_limit'].get('current_hour_changes', 0)}")
        print(f"\n{status['message']}")

    elif args.command == "patterns":
        print(f"\n{'='*60}")
        print(f"KNOWN HARMFUL PATTERNS")
        print(f"{'='*60}")
        for name, (desc, harm_type, severity) in KNOWN_HARMFUL_PATTERNS.items():
            print(f"\n{name}:")
            print(f"  Description: {desc}")
            print(f"  Harm type: {harm_type}")
            print(f"  Severity: {severity}")

        learned = prevention.state.get("learned_patterns", [])
        if learned:
            print(f"\n{'='*60}")
            print(f"LEARNED PATTERNS ({len(learned)})")
            print(f"{'='*60}")
            for pattern in learned:
                print(f"\n{pattern['name']}:")
                print(f"  Target: {pattern['target']}")
                print(f"  Intention: {pattern['intention']}")
                print(f"  Description: {pattern['description']}")

    elif args.command == "validate":
        if not all([args.type, args.target, args.intention]):
            print("Error: --type, --target, and --intention required")
            return

        try:
            ct = ChangeType(args.type)
        except ValueError:
            print(f"Invalid change type. Valid types: {[t.value for t in ChangeType]}")
            return

        allowed, reason, record = prevention.validate_change(ct, args.target, args.intention)
        if allowed:
            print(f"ALLOWED: {reason}")
            if record:
                print(f"Change ID: {record.change_id}")
                print(f"Rollback available: {record.rollback_available}")
        else:
            print(f"BLOCKED: {reason}")

    elif args.command == "history":
        if not CHANGE_LOG_FILE.exists():
            print("No change history found")
            return

        print(f"\n{'='*60}")
        print(f"RECENT CHANGES")
        print(f"{'='*60}")

        with open(CHANGE_LOG_FILE) as f:
            lines = f.readlines()[-20:]  # Last 20

        for line in lines:
            try:
                entry = json.loads(line)
                outcome = entry.get("outcome", "unknown")
                emoji = "✓" if outcome == "success" else "✗" if outcome == "harmful" else "?"
                print(f"\n{emoji} {entry.get('change_id', 'unknown')[:8]}:")
                print(f"   Type: {entry.get('change_type')}")
                print(f"   Target: {entry.get('target')}")
                print(f"   Intention: {entry.get('intention')}")
                print(f"   Outcome: {outcome}")
                if entry.get("harm_description"):
                    print(f"   Harm: {entry.get('harm_description')}")
            except:
                continue

    elif args.command == "rollback":
        if not args.change_id:
            print("Error: --change-id required")
            return

        success, message = prevention.rollback(args.change_id)
        print(message)


if __name__ == "__main__":
    main()
