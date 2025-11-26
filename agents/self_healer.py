"""
Self-Healing Agent for Hands-Off Engine

Autonomous self-repair capabilities:
- Auto-restart failed processes
- Repair corrupted state files
- Clear stale locks
- Reset rate limit counters
- Retry failed operations
"""

import json
import os
import signal
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audit.audit_logger import AuditLogger
from agents.alerts import get_alert_system, AlertLevel
from agents.backup import BackupSystem


class SelfHealer:
    """Autonomous self-healing agent"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize self-healer
        
        Args:
            config_path: Path to healing_rules.json config file
        """
        repo_root = Path(__file__).parent.parent
        
        # Load configuration
        if config_path is None:
            config_path = repo_root / "config" / "healing_rules.json"
        
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.state_dir = repo_root / "state"
        self.audit_logger = AuditLogger(component="self_healer")
        self.alerts = get_alert_system()
        self.backup_system = BackupSystem()
        
        # Track healing attempts
        self.healing_attempts: Dict[str, List[datetime]] = {}
        
        # State file
        self.state_file = self.state_dir / "self_healing_state.json"
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load self-healing state"""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except:
                return self._default_state()
        return self._default_state()
    
    def _default_state(self) -> Dict[str, Any]:
        """Return default state"""
        return {
            "total_fixes": 0,
            "last_check": None,
            "issues_detected": [],
            "auto_fixed": []
        }
    
    def _save_state(self):
        """Save self-healing state"""
        try:
            # Atomic write
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            temp_file.replace(self.state_file)
        except Exception as e:
            print(f"Failed to save state: {e}", file=sys.stderr)
    
    def auto_heal(self, issue: Dict[str, Any]) -> bool:
        """
        Attempt to automatically heal an issue
        
        Args:
            issue: Issue to heal (must have 'type' and 'details' keys)
            
        Returns:
            True if healing was successful
        """
        issue_type = issue.get("type")
        details = issue.get("details", {})
        
        # Check if healing is enabled
        if not self.config.get("auto_healing_enabled", True):
            return False
        
        # Find matching rule
        rule = self._find_matching_rule(issue_type)
        if not rule or not rule.get("enabled", True):
            return False
        
        # Check cooldown
        if not self._check_cooldown(issue_type, rule):
            return False
        
        # Attempt healing based on issue type
        success = False
        action = rule.get("action")
        
        try:
            if action == "restart":
                success = self._restart_process(details.get("process_name"))
            elif action == "restore_from_backup":
                success = self._restore_from_backup(details.get("file_name"))
            elif action == "clear_lock":
                success = self._clear_lock(details.get("lock_file"))
            elif action == "reset_counter":
                success = self._reset_counter(details.get("counter_name"))
            elif action == "retry":
                success = self._retry_operation(details.get("operation"))
            elif action == "cleanup_temp":
                success = self._cleanup_temp_files()
            
            # Record attempt
            self._record_healing_attempt(issue_type, success)
            
            # Update state
            if success:
                self.state["total_fixes"] += 1
                self.state["auto_fixed"].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "issue_type": issue_type,
                    "action": action,
                    "details": details
                })
                
                # Keep only last 100 fixes
                self.state["auto_fixed"] = self.state["auto_fixed"][-100:]
            
            self._save_state()
            
            # Send alert
            self.alerts.alert_self_healing_action(
                action,
                str(details),
                success
            )
            
            # Log audit event
            self.audit_logger.log(
                event_type="self_healing",
                event_data={
                    "issue_type": issue_type,
                    "action": action,
                    "success": success,
                    "details": details
                }
            )
            
            return success
            
        except Exception as e:
            self.audit_logger.log(
                event_type=AuditLogger.EVENT_ERROR,
                event_data={
                    "error": "healing_failed",
                    "issue_type": issue_type,
                    "exception": str(e)
                }
            )
            return False
    
    def _find_matching_rule(self, issue_type: str) -> Optional[Dict[str, Any]]:
        """Find healing rule matching issue type"""
        for rule in self.config.get("rules", []):
            if rule.get("condition") == issue_type:
                return rule
        return None
    
    def _check_cooldown(self, issue_type: str, rule: Dict[str, Any]) -> bool:
        """Check if cooldown period has elapsed"""
        cooldown = rule.get("cooldown_seconds", 0)
        if cooldown == 0:
            return True
        
        attempts = self.healing_attempts.get(issue_type, [])
        if not attempts:
            return True
        
        last_attempt = attempts[-1]
        elapsed = (datetime.now(timezone.utc) - last_attempt).total_seconds()
        
        return elapsed >= cooldown
    
    def _record_healing_attempt(self, issue_type: str, success: bool):
        """Record healing attempt"""
        if issue_type not in self.healing_attempts:
            self.healing_attempts[issue_type] = []
        
        self.healing_attempts[issue_type].append(datetime.now(timezone.utc))
        
        # Keep only recent attempts
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        self.healing_attempts[issue_type] = [
            t for t in self.healing_attempts[issue_type] if t > cutoff
        ]
    
    def _restart_process(self, process_name: str) -> bool:
        """Restart a failed process"""
        if not process_name:
            return False
        
        try:
            # Check if process-specific restart script exists
            repo_root = Path(__file__).parent.parent
            restart_script = repo_root / "termux-hands-off" / "agent" / f"ensure_{process_name}.sh"
            
            if restart_script.exists():
                subprocess.run([str(restart_script)], check=True)
                return True
            
            # Generic restart for common processes
            if process_name == "crond":
                subprocess.run(["crond", "-n", "-P"], check=False)
                return True
            
            return False
            
        except Exception as e:
            self.audit_logger.log(
                event_type=AuditLogger.EVENT_ERROR,
                event_data={"error": "restart_failed", "process": process_name, "exception": str(e)}
            )
            return False
    
    def _restore_from_backup(self, file_name: str) -> bool:
        """Restore corrupted file from backup"""
        if not file_name:
            return False
        
        return self.backup_system.restore_from_backup(file_name)
    
    def _clear_lock(self, lock_file: str) -> bool:
        """Clear a stale lock file"""
        if not lock_file:
            return False
        
        try:
            lock_path = Path(lock_file)
            
            # Check if lock is stale
            if lock_path.exists():
                mod_time = datetime.fromtimestamp(lock_path.stat().st_mtime, tz=timezone.utc)
                age_minutes = (datetime.now(timezone.utc) - mod_time).total_seconds() / 60
                
                threshold = self.config.get("stale_lock_age_minutes", 30)
                
                if age_minutes > threshold:
                    lock_path.unlink()
                    return True
            
            return False
            
        except Exception as e:
            self.audit_logger.log(
                event_type=AuditLogger.EVENT_ERROR,
                event_data={"error": "clear_lock_failed", "lock_file": lock_file, "exception": str(e)}
            )
            return False
    
    def _reset_counter(self, counter_name: str) -> bool:
        """Reset a rate limit counter"""
        if not counter_name:
            return False
        
        try:
            # Reset counter in state file
            counter_file = self.state_dir / f"{counter_name}_counter.json"
            if counter_file.exists():
                with open(counter_file, 'w') as f:
                    json.dump({"count": 0, "reset_at": datetime.now(timezone.utc).isoformat()}, f)
                return True
            
            return False
            
        except Exception as e:
            self.audit_logger.log(
                event_type=AuditLogger.EVENT_ERROR,
                event_data={"error": "reset_counter_failed", "counter": counter_name, "exception": str(e)}
            )
            return False
    
    def _retry_operation(self, operation: Dict[str, Any]) -> bool:
        """Retry a failed operation"""
        if not operation:
            return False
        
        # This would be implemented based on specific operation types
        # For now, just log the intent
        self.audit_logger.log(
            event_type="operation_retry",
            event_data={"operation": operation}
        )
        
        return False
    
    def _cleanup_temp_files(self) -> bool:
        """Clean up temporary files to free disk space"""
        try:
            cleaned_bytes = 0
            
            # Clean /tmp
            tmp_dir = Path("/tmp")
            if tmp_dir.exists():
                for item in tmp_dir.glob("hands-off-*"):
                    try:
                        if item.is_file():
                            cleaned_bytes += item.stat().st_size
                            item.unlink()
                        elif item.is_dir():
                            import shutil
                            cleaned_bytes += sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                            shutil.rmtree(item)
                    except:
                        continue
            
            # Clean old log files (keep last 30 days)
            logs_dir = Path(__file__).parent.parent / "logs"
            if logs_dir.exists():
                cutoff = datetime.now(timezone.utc) - timedelta(days=30)
                for log_file in logs_dir.glob("*.log*"):
                    try:
                        mod_time = datetime.fromtimestamp(log_file.stat().st_mtime, tz=timezone.utc)
                        if mod_time < cutoff:
                            cleaned_bytes += log_file.stat().st_size
                            log_file.unlink()
                    except:
                        continue
            
            self.audit_logger.log(
                event_type="cleanup_temp",
                event_data={"cleaned_bytes": cleaned_bytes, "cleaned_mb": cleaned_bytes / (1024**2)}
            )
            
            return True
            
        except Exception as e:
            self.audit_logger.log(
                event_type=AuditLogger.EVENT_ERROR,
                event_data={"error": "cleanup_failed", "exception": str(e)}
            )
            return False
    
    def should_escalate(self, issue_type: str) -> bool:
        """Check if issue should be escalated to human"""
        attempts = self.healing_attempts.get(issue_type, [])
        
        # Check recent attempts (last hour)
        recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_attempts = [t for t in attempts if t > recent_cutoff]
        
        escalation_config = self.config.get("escalation", {})
        max_failures = escalation_config.get("escalate_after_failures", 3)
        
        return len(recent_attempts) >= max_failures


if __name__ == "__main__":
    # Simple test
    healer = SelfHealer()
    
    # Test healing a mock issue
    test_issue = {
        "type": "state_file_corrupted",
        "details": {"file_name": "test.json"}
    }
    
    print(f"Testing self-healing for: {test_issue}")
    success = healer.auto_heal(test_issue)
    print(f"Healing result: {success}")
    
    print(f"\nTotal fixes: {healer.state['total_fixes']}")
