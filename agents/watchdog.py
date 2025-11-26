"""
Watchdog for Hands-Off Engine

Monitors agent heartbeats and restarts dead agents:
- Monitor agent heartbeats
- Restart dead agents
- Log all interventions
- Escalate if self-healing fails
"""

import json
import time
import signal
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audit.audit_logger import AuditLogger
from agents.alerts import get_alert_system, AlertLevel
from agents.health_monitor import HealthMonitor, HealthStatus
from agents.self_healer import SelfHealer


class Watchdog:
    """Monitors and restarts agents"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize watchdog
        
        Args:
            config_path: Path to health_thresholds.json config file
        """
        repo_root = Path(__file__).parent.parent
        
        # Load configuration
        if config_path is None:
            config_path = repo_root / "config" / "health_thresholds.json"
        
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.state_dir = repo_root / "state"
        self.audit_logger = AuditLogger(component="watchdog")
        self.alerts = get_alert_system()
        self.health_monitor = HealthMonitor(config_path)
        self.self_healer = SelfHealer()
        
        # Track agent heartbeats
        self.heartbeats: Dict[str, datetime] = {}
        
        # Track restart attempts
        self.restart_attempts: Dict[str, List[datetime]] = {}
        
        # Watchdog state
        self.state_file = self.state_dir / "watchdog_state.json"
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load watchdog state"""
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
            "total_interventions": 0,
            "last_check": None,
            "agents": {},
            "interventions": []
        }
    
    def _save_state(self):
        """Save watchdog state atomically"""
        try:
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            temp_file.replace(self.state_file)
        except Exception as e:
            print(f"Failed to save state: {e}", file=sys.stderr)
    
    def register_heartbeat(self, agent_name: str):
        """Register heartbeat from agent"""
        self.heartbeats[agent_name] = datetime.now(timezone.utc)
        
        # Update state
        if agent_name not in self.state["agents"]:
            self.state["agents"][agent_name] = {
                "first_seen": datetime.now(timezone.utc).isoformat(),
                "last_heartbeat": None,
                "restart_count": 0
            }
        
        self.state["agents"][agent_name]["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
        self._save_state()
    
    def check_heartbeats(self) -> List[str]:
        """
        Check for missing heartbeats
        
        Returns:
            List of agent names with missing heartbeats
        """
        timeout_seconds = self.config.get("heartbeat_timeout_seconds", 600)
        timeout = timedelta(seconds=timeout_seconds)
        now = datetime.now(timezone.utc)
        
        dead_agents = []
        
        for agent_name, last_heartbeat in self.heartbeats.items():
            if now - last_heartbeat > timeout:
                dead_agents.append(agent_name)
        
        return dead_agents
    
    def run_watch_cycle(self) -> Dict[str, Any]:
        """
        Run one watch cycle
        
        Returns:
            Cycle results
        """
        cycle_start = datetime.now(timezone.utc)
        
        results = {
            "timestamp": cycle_start.isoformat(),
            "health_check": None,
            "dead_agents": [],
            "restart_attempts": [],
            "healing_actions": [],
            "escalations": []
        }
        
        # Run health check
        health_results = self.health_monitor.run_health_check()
        results["health_check"] = health_results
        
        # Check for dead agents
        dead_agents = self.check_heartbeats()
        results["dead_agents"] = dead_agents
        
        # Attempt to restart dead agents
        for agent_name in dead_agents:
            restart_success = self._restart_agent(agent_name)
            results["restart_attempts"].append({
                "agent": agent_name,
                "success": restart_success
            })
        
        # Check for issues requiring healing
        if health_results["overall_status"] in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
            healing_actions = self._heal_health_issues(health_results)
            results["healing_actions"] = healing_actions
        
        # Check for escalations
        escalations = self._check_escalations(health_results, dead_agents)
        results["escalations"] = escalations
        
        # Update state
        self.state["last_check"] = cycle_start.isoformat()
        self._save_state()
        
        # Log cycle
        self.audit_logger.log(
            event_type="watchdog_cycle",
            event_data=results
        )
        
        return results
    
    def _restart_agent(self, agent_name: str) -> bool:
        """
        Attempt to restart an agent
        
        Returns:
            True if restart was successful
        """
        # Check restart attempts
        max_attempts = self.config.get("max_process_restart_attempts", 3)
        cooldown = self.config.get("restart_cooldown_seconds", 60)
        
        if agent_name not in self.restart_attempts:
            self.restart_attempts[agent_name] = []
        
        # Check cooldown
        if self.restart_attempts[agent_name]:
            last_attempt = self.restart_attempts[agent_name][-1]
            elapsed = (datetime.now(timezone.utc) - last_attempt).total_seconds()
            if elapsed < cooldown:
                return False
        
        # Check max attempts
        recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_attempts = [t for t in self.restart_attempts[agent_name] if t > recent_cutoff]
        
        if len(recent_attempts) >= max_attempts:
            self._escalate(f"Max restart attempts reached for agent: {agent_name}")
            return False
        
        # Record attempt
        self.restart_attempts[agent_name].append(datetime.now(timezone.utc))
        
        # Attempt restart using self-healer
        success = self.self_healer.auto_heal({
            "type": "process_not_running",
            "details": {"process_name": agent_name}
        })
        
        # Update state
        if agent_name in self.state["agents"]:
            self.state["agents"][agent_name]["restart_count"] += 1
        
        self.state["total_interventions"] += 1
        self.state["interventions"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "agent_restart",
            "agent": agent_name,
            "success": success
        })
        
        # Keep only last 100 interventions
        self.state["interventions"] = self.state["interventions"][-100:]
        
        self._save_state()
        
        # Send alert
        self.alerts.alert_self_healing_action(
            "restart_agent",
            agent_name,
            success
        )
        
        return success
    
    def _heal_health_issues(self, health_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Attempt to heal health check issues
        
        Returns:
            List of healing actions taken
        """
        healing_actions = []
        
        checks = health_results.get("checks", {})
        
        # Handle state file integrity issues
        if "state_file_integrity" in checks:
            file_results = checks["state_file_integrity"].get("files", {})
            for filename, file_result in file_results.items():
                if not file_result.get("valid_json", True):
                    # Corrupted JSON file - restore from backup
                    success = self.self_healer.auto_heal({
                        "type": "state_file_corrupted",
                        "details": {"file_name": filename}
                    })
                    healing_actions.append({
                        "issue": "corrupted_state_file",
                        "target": filename,
                        "action": "restore_from_backup",
                        "success": success
                    })
        
        # Handle disk usage issues
        if "disk_usage" in checks and checks["disk_usage"]["status"] == HealthStatus.CRITICAL:
            success = self.self_healer.auto_heal({
                "type": "disk_usage_high",
                "details": {}
            })
            healing_actions.append({
                "issue": "disk_usage_high",
                "action": "cleanup_temp",
                "success": success
            })
        
        # Handle process status issues
        if "process_status" in checks:
            processes = checks["process_status"].get("processes", {})
            for process_name, process_result in processes.items():
                if not process_result.get("running", False):
                    success = self.self_healer.auto_heal({
                        "type": "process_not_running",
                        "details": {"process_name": process_name}
                    })
                    healing_actions.append({
                        "issue": "process_not_running",
                        "target": process_name,
                        "action": "restart",
                        "success": success
                    })
        
        return healing_actions
    
    def _check_escalations(
        self,
        health_results: Dict[str, Any],
        dead_agents: List[str]
    ) -> List[str]:
        """
        Check if any issues require escalation
        
        Returns:
            List of escalation messages
        """
        escalations = []
        
        # Escalate if overall health is critical
        if health_results["overall_status"] == HealthStatus.CRITICAL:
            # Check if we've already tried to heal
            checks = health_results.get("checks", {})
            for check_name, check_result in checks.items():
                if check_result.get("status") == HealthStatus.CRITICAL:
                    if self.self_healer.should_escalate(check_name):
                        msg = f"Critical health check failed after multiple healing attempts: {check_name}"
                        escalations.append(msg)
                        self._escalate(msg)
        
        # Escalate if agents keep dying
        for agent_name in dead_agents:
            if self.self_healer.should_escalate(f"agent_{agent_name}"):
                msg = f"Agent keeps dying after multiple restart attempts: {agent_name}"
                escalations.append(msg)
                self._escalate(msg)
        
        return escalations
    
    def _escalate(self, message: str):
        """Escalate issue to human"""
        self.alerts.send_alert(
            f"ESCALATION REQUIRED: {message}",
            level=AlertLevel.CRITICAL,
            context={"requires_human_intervention": True}
        )
        
        self.audit_logger.log(
            event_type="escalation",
            event_data={"message": message}
        )
    
    def run_forever(self, interval_seconds: int = 300):
        """
        Run watchdog loop forever
        
        Args:
            interval_seconds: Time between watch cycles (default 5 minutes)
        """
        self.alerts.send_alert(
            "Watchdog started",
            level=AlertLevel.INFO
        )
        
        try:
            while True:
                try:
                    results = self.run_watch_cycle()
                    
                    # Log summary
                    print(f"Watch cycle complete: {results['timestamp']}")
                    print(f"  Overall health: {results['health_check']['overall_status']}")
                    print(f"  Dead agents: {len(results['dead_agents'])}")
                    print(f"  Healing actions: {len(results['healing_actions'])}")
                    print(f"  Escalations: {len(results['escalations'])}")
                    
                except Exception as e:
                    self.audit_logger.log(
                        event_type=AuditLogger.EVENT_ERROR,
                        event_data={"error": "watch_cycle_failed", "exception": str(e)}
                    )
                    print(f"Watch cycle error: {e}", file=sys.stderr)
                
                # Wait for next cycle
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            self.alerts.send_alert(
                "Watchdog stopped",
                level=AlertLevel.WARNING
            )
            print("\nWatchdog stopped by user")


if __name__ == "__main__":
    # Run watchdog
    watchdog = Watchdog()
    
    # Run single cycle for testing
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        results = watchdog.run_watch_cycle()
        print(json.dumps(results, indent=2))
    else:
        # Run forever
        interval = int(sys.argv[1]) if len(sys.argv) > 1 else 300
        watchdog.run_forever(interval_seconds=interval)
