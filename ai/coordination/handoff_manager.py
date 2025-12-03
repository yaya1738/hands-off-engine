#!/usr/bin/env python3
"""
Enhanced Handoff Management System
===================================

Provides improved handoff coordination with:
- State validation and tracking
- Timeout handling
- Priority management
- Retry mechanisms
- Health monitoring
- Dependency tracking
"""

import json
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set
import logging

# Setup paths
BASE_DIR = Path(__file__).parent.parent.parent
COORD_DIR = Path(__file__).parent
HANDOFF_FILE = COORD_DIR / "handoffs.json"
HANDOFF_LOG = COORD_DIR / "handoff_history.jsonl"
HANDOFF_METRICS = COORD_DIR / "handoff_metrics.json"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HandoffStatus(Enum):
    """Handoff status states"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class HandoffPriority(Enum):
    """Handoff priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HandoffTask:
    """Enhanced handoff task with validation"""
    type: str  # e.g., "code_review", "research", "implementation"
    description: str
    files: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    estimated_duration: Optional[int] = None  # minutes
    deliverables: List[str] = field(default_factory=list)
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate task structure"""
        if not self.type:
            return False, "Task type is required"
        if not self.description:
            return False, "Task description is required"
        return True, None


@dataclass
class Handoff:
    """Enhanced handoff with full state management"""
    id: str
    timestamp: str
    from_agent: str
    to_agent: str
    task: HandoffTask
    status: HandoffStatus = HandoffStatus.PENDING
    priority: HandoffPriority = HandoffPriority.NORMAL
    context: Dict = field(default_factory=dict)
    
    # Lifecycle timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    accepted_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    failed_at: Optional[str] = None
    
    # Metadata
    dependencies: List[str] = field(default_factory=list)  # IDs of prerequisite handoffs
    timeout_minutes: int = 60  # Default 1 hour timeout
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    notes: List[Dict] = field(default_factory=list)
    
    def is_expired(self) -> bool:
        """Check if handoff has exceeded timeout"""
        if self.status in [HandoffStatus.COMPLETED, HandoffStatus.FAILED, HandoffStatus.CANCELLED]:
            return False
        
        created = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        elapsed = (now - created).total_seconds() / 60
        return elapsed > self.timeout_minutes
    
    def can_accept(self, agent_capabilities: Set[str]) -> tuple[bool, Optional[str]]:
        """Check if agent has required capabilities"""
        required_caps = set(self.task.requirements)
        if not required_caps.issubset(agent_capabilities):
            missing = required_caps - agent_capabilities
            return False, f"Missing capabilities: {', '.join(missing)}"
        return True, None
    
    def add_note(self, message: str, author: str):
        """Add note to handoff"""
        self.notes.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "author": author,
            "message": message
        })


class HandoffManager:
    """
    Enhanced handoff management with validation, monitoring, and recovery
    
    Features:
    - State validation
    - Timeout detection
    - Dependency resolution
    - Retry logic
    - Health metrics
    - Agent capability matching
    """
    
    def __init__(self):
        self.handoff_file = HANDOFF_FILE
        self.handoff_log = HANDOFF_LOG
        self.metrics_file = HANDOFF_METRICS
        
        # Agent capabilities registry
        self.agent_capabilities = {
            "copilot": {"code_review", "pr_management", "documentation", "testing"},
            "claude-code": {"implementation", "system_admin", "debugging", "refactoring"},
            "chatgpt": {"research", "analysis", "writing", "planning"},
            "claude-web": {"research", "analysis", "planning", "documentation"}
        }
        
    def create_handoff(
        self,
        from_agent: str,
        to_agent: str,
        task: Dict,
        priority: str = "normal",
        context: Dict = None,
        dependencies: List[str] = None,
        timeout_minutes: int = 60
    ) -> Dict:
        """
        Create new handoff with validation
        
        Returns:
            Dict with success status and handoff details or error
        """
        # Validate agents
        if to_agent not in self.agent_capabilities:
            return {
                "success": False,
                "error": f"Unknown target agent: {to_agent}"
            }
        
        # Create task object
        task_obj = HandoffTask(**task)
        is_valid, error = task_obj.validate()
        if not is_valid:
            return {
                "success": False,
                "error": f"Invalid task: {error}"
            }
        
        # Check agent capabilities
        agent_caps = self.agent_capabilities.get(to_agent, set())
        can_accept, cap_error = Handoff(
            id="temp",
            timestamp=datetime.now(timezone.utc).isoformat(),
            from_agent=from_agent,
            to_agent=to_agent,
            task=task_obj
        ).can_accept(agent_caps)
        
        if not can_accept:
            return {
                "success": False,
                "error": f"Agent {to_agent} cannot accept: {cap_error}"
            }
        
        # Check dependencies
        if dependencies:
            dep_status = self._check_dependencies(dependencies)
            if not dep_status["all_completed"]:
                return {
                    "success": False,
                    "error": f"Unmet dependencies: {', '.join(dep_status['incomplete'])}"
                }
        
        # Create handoff
        handoff_id = f"handoff-{int(time.time())}-{from_agent}-{to_agent}"
        handoff = Handoff(
            id=handoff_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            from_agent=from_agent,
            to_agent=to_agent,
            task=task_obj,
            priority=HandoffPriority[priority.upper()],
            context=context or {},
            dependencies=dependencies or [],
            timeout_minutes=timeout_minutes
        )
        
        # Save handoff
        self._save_handoff(handoff)
        self._log_handoff_event(handoff, "created")
        
        logger.info(f"Created handoff {handoff_id}: {task_obj.description}")
        
        return {
            "success": True,
            "handoff_id": handoff_id,
            "status": handoff.status.value,
            "to_agent": to_agent,
            "priority": handoff.priority.value
        }
    
    def accept_handoff(self, handoff_id: str, agent: str) -> Dict:
        """Accept a handoff"""
        handoff = self._get_handoff(handoff_id)
        if not handoff:
            return {"success": False, "error": "Handoff not found"}
        
        if handoff.to_agent != agent:
            return {"success": False, "error": "Not the target agent"}
        
        if handoff.status != HandoffStatus.PENDING:
            return {"success": False, "error": f"Handoff is {handoff.status.value}, cannot accept"}
        
        handoff.status = HandoffStatus.ACCEPTED
        handoff.accepted_at = datetime.now(timezone.utc).isoformat()
        handoff.add_note(f"Accepted by {agent}", agent)
        
        self._update_handoff(handoff)
        self._log_handoff_event(handoff, "accepted")
        
        logger.info(f"Handoff {handoff_id} accepted by {agent}")
        
        return {"success": True, "status": handoff.status.value}
    
    def start_handoff(self, handoff_id: str, agent: str) -> Dict:
        """Start working on handoff"""
        handoff = self._get_handoff(handoff_id)
        if not handoff:
            return {"success": False, "error": "Handoff not found"}
        
        if handoff.to_agent != agent:
            return {"success": False, "error": "Not the target agent"}
        
        if handoff.status != HandoffStatus.ACCEPTED:
            return {"success": False, "error": f"Handoff must be accepted first"}
        
        handoff.status = HandoffStatus.IN_PROGRESS
        handoff.started_at = datetime.now(timezone.utc).isoformat()
        handoff.add_note(f"Work started by {agent}", agent)
        
        self._update_handoff(handoff)
        self._log_handoff_event(handoff, "started")
        
        logger.info(f"Handoff {handoff_id} started by {agent}")
        
        return {"success": True, "status": handoff.status.value}
    
    def complete_handoff(self, handoff_id: str, agent: str, result: Dict = None) -> Dict:
        """Complete a handoff"""
        handoff = self._get_handoff(handoff_id)
        if not handoff:
            return {"success": False, "error": "Handoff not found"}
        
        if handoff.to_agent != agent:
            return {"success": False, "error": "Not the target agent"}
        
        handoff.status = HandoffStatus.COMPLETED
        handoff.completed_at = datetime.now(timezone.utc).isoformat()
        if result:
            handoff.context["result"] = result
        handoff.add_note(f"Completed by {agent}", agent)
        
        self._update_handoff(handoff)
        self._log_handoff_event(handoff, "completed", result)
        
        logger.info(f"Handoff {handoff_id} completed by {agent}")
        
        return {"success": True, "status": handoff.status.value}
    
    def fail_handoff(self, handoff_id: str, agent: str, error: str, retry: bool = True) -> Dict:
        """Mark handoff as failed"""
        handoff = self._get_handoff(handoff_id)
        if not handoff:
            return {"success": False, "error": "Handoff not found"}
        
        handoff.error_message = error
        handoff.failed_at = datetime.now(timezone.utc).isoformat()
        handoff.add_note(f"Failed: {error}", agent)
        
        # Check if should retry
        if retry and handoff.retry_count < handoff.max_retries:
            handoff.retry_count += 1
            handoff.status = HandoffStatus.PENDING
            handoff.add_note(f"Retry attempt {handoff.retry_count}/{handoff.max_retries}", "system")
            logger.warning(f"Handoff {handoff_id} failed, retrying ({handoff.retry_count}/{handoff.max_retries})")
        else:
            handoff.status = HandoffStatus.FAILED
            logger.error(f"Handoff {handoff_id} failed permanently: {error}")
        
        self._update_handoff(handoff)
        self._log_handoff_event(handoff, "failed", {"error": error, "retry": retry})
        
        return {"success": True, "status": handoff.status.value, "retry_count": handoff.retry_count}
    
    def cancel_handoff(self, handoff_id: str, agent: str, reason: str) -> Dict:
        """Cancel a handoff"""
        handoff = self._get_handoff(handoff_id)
        if not handoff:
            return {"success": False, "error": "Handoff not found"}
        
        if agent not in [handoff.from_agent, handoff.to_agent]:
            return {"success": False, "error": "Not authorized to cancel"}
        
        handoff.status = HandoffStatus.CANCELLED
        handoff.add_note(f"Cancelled by {agent}: {reason}", agent)
        
        self._update_handoff(handoff)
        self._log_handoff_event(handoff, "cancelled", {"reason": reason})
        
        logger.info(f"Handoff {handoff_id} cancelled by {agent}: {reason}")
        
        return {"success": True, "status": handoff.status.value}
    
    def get_pending_handoffs(self, agent: str = None) -> List[Dict]:
        """Get all pending handoffs, optionally filtered by agent"""
        handoffs_data = self._load_handoffs()
        pending = []
        
        for handoff_data in handoffs_data.get("active", []):
            handoff = self._deserialize_handoff(handoff_data)
            if handoff.status == HandoffStatus.PENDING:
                if agent is None or handoff.to_agent == agent:
                    pending.append(self._handoff_to_dict(handoff))
        
        # Sort by priority: critical > high > normal > low
        priority_order = {"critical": 4, "high": 3, "normal": 2, "low": 1}
        return sorted(pending, key=lambda x: priority_order.get(x["priority"], 0), reverse=True)
    
    def check_timeouts(self) -> List[Dict]:
        """Check for expired handoffs and mark as timeout"""
        handoffs_data = self._load_handoffs()
        timed_out = []
        
        for handoff_data in handoffs_data.get("active", []):
            handoff = self._deserialize_handoff(handoff_data)
            
            if handoff.is_expired() and handoff.status not in [
                HandoffStatus.COMPLETED,
                HandoffStatus.FAILED,
                HandoffStatus.CANCELLED,
                HandoffStatus.TIMEOUT
            ]:
                handoff.status = HandoffStatus.TIMEOUT
                handoff.add_note(f"Timed out after {handoff.timeout_minutes} minutes", "system")
                self._update_handoff(handoff)
                self._log_handoff_event(handoff, "timeout")
                timed_out.append(self._handoff_to_dict(handoff))
                logger.warning(f"Handoff {handoff.id} timed out")
        
        return timed_out
    
    def get_metrics(self) -> Dict:
        """Calculate handoff health metrics"""
        handoffs_data = self._load_handoffs()
        
        total = 0
        by_status = {status.value: 0 for status in HandoffStatus}
        by_agent = {}
        by_priority = {priority.value: 0 for priority in HandoffPriority}
        total_duration = 0
        completed_count = 0
        
        for handoff_data in handoffs_data.get("active", []) + handoffs_data.get("completed", []):
            handoff = self._deserialize_handoff(handoff_data)
            total += 1
            by_status[handoff.status.value] += 1
            by_priority[handoff.priority.value] += 1
            
            # Track by agent
            agent = handoff.to_agent
            if agent not in by_agent:
                by_agent[agent] = {"total": 0, "completed": 0, "failed": 0, "pending": 0}
            by_agent[agent]["total"] += 1
            
            if handoff.status == HandoffStatus.COMPLETED:
                by_agent[agent]["completed"] += 1
                if handoff.created_at and handoff.completed_at:
                    created = datetime.fromisoformat(handoff.created_at.replace('Z', '+00:00'))
                    completed = datetime.fromisoformat(handoff.completed_at.replace('Z', '+00:00'))
                    duration = (completed - created).total_seconds() / 60
                    total_duration += duration
                    completed_count += 1
            elif handoff.status == HandoffStatus.FAILED:
                by_agent[agent]["failed"] += 1
            elif handoff.status == HandoffStatus.PENDING:
                by_agent[agent]["pending"] += 1
        
        avg_duration = total_duration / completed_count if completed_count > 0 else 0
        completion_rate = by_status["completed"] / total if total > 0 else 0
        
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_handoffs": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_agent": by_agent,
            "completion_rate": round(completion_rate, 2),
            "average_duration_minutes": round(avg_duration, 2)
        }
        
        # Save metrics
        with open(self.metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        return metrics
    
    def _check_dependencies(self, dep_ids: List[str]) -> Dict:
        """Check if all dependency handoffs are completed"""
        handoffs_data = self._load_handoffs()
        completed_ids = {h["id"] for h in handoffs_data.get("completed", [])}
        
        incomplete = [dep_id for dep_id in dep_ids if dep_id not in completed_ids]
        
        return {
            "all_completed": len(incomplete) == 0,
            "incomplete": incomplete
        }
    
    def _get_handoff(self, handoff_id: str) -> Optional[Handoff]:
        """Get handoff by ID"""
        handoffs_data = self._load_handoffs()
        
        for handoff_data in handoffs_data.get("active", []):
            if handoff_data["id"] == handoff_id:
                return self._deserialize_handoff(handoff_data)
        
        for handoff_data in handoffs_data.get("completed", []):
            if handoff_data["id"] == handoff_id:
                return self._deserialize_handoff(handoff_data)
        
        return None
    
    def _save_handoff(self, handoff: Handoff):
        """Save new handoff"""
        handoffs_data = self._load_handoffs()
        
        if "active" not in handoffs_data:
            handoffs_data["active"] = []
        
        handoffs_data["active"].append(self._handoff_to_dict(handoff))
        
        with open(self.handoff_file, 'w') as f:
            json.dump(handoffs_data, f, indent=2)
    
    def _update_handoff(self, handoff: Handoff):
        """Update existing handoff"""
        handoffs_data = self._load_handoffs()
        
        # Find and update in active
        for i, h in enumerate(handoffs_data.get("active", [])):
            if h["id"] == handoff.id:
                # Move to completed if done
                if handoff.status in [HandoffStatus.COMPLETED, HandoffStatus.FAILED, HandoffStatus.CANCELLED]:
                    handoffs_data["active"].pop(i)
                    if "completed" not in handoffs_data:
                        handoffs_data["completed"] = []
                    handoffs_data["completed"].append(self._handoff_to_dict(handoff))
                else:
                    handoffs_data["active"][i] = self._handoff_to_dict(handoff)
                break
        
        with open(self.handoff_file, 'w') as f:
            json.dump(handoffs_data, f, indent=2)
    
    def _load_handoffs(self) -> Dict:
        """Load handoffs from file"""
        if self.handoff_file.exists():
            with open(self.handoff_file) as f:
                return json.load(f)
        return {"active": [], "completed": [], "protocol_version": "2.0"}
    
    def _log_handoff_event(self, handoff: Handoff, event: str, data: Dict = None):
        """Log handoff event to history"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "handoff_id": handoff.id,
            "event": event,
            "from_agent": handoff.from_agent,
            "to_agent": handoff.to_agent,
            "status": handoff.status.value,
            "priority": handoff.priority.value
        }
        
        if data:
            log_entry["data"] = data
        
        with open(self.handoff_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _handoff_to_dict(self, handoff: Handoff) -> Dict:
        """Convert handoff to dictionary"""
        d = {
            "id": handoff.id,
            "timestamp": handoff.timestamp,
            "from_agent": handoff.from_agent,
            "to_agent": handoff.to_agent,
            "task": asdict(handoff.task),
            "status": handoff.status.value,
            "priority": handoff.priority.value,
            "context": handoff.context,
            "created_at": handoff.created_at,
            "accepted_at": handoff.accepted_at,
            "started_at": handoff.started_at,
            "completed_at": handoff.completed_at,
            "failed_at": handoff.failed_at,
            "dependencies": handoff.dependencies,
            "timeout_minutes": handoff.timeout_minutes,
            "retry_count": handoff.retry_count,
            "max_retries": handoff.max_retries,
            "error_message": handoff.error_message,
            "notes": handoff.notes
        }
        return d
    
    def _deserialize_handoff(self, data: Dict) -> Handoff:
        """Convert dictionary to handoff"""
        task_data = data.get("task", {})
        task = HandoffTask(**task_data)
        
        return Handoff(
            id=data["id"],
            timestamp=data["timestamp"],
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            task=task,
            status=HandoffStatus(data["status"]),
            priority=HandoffPriority(data.get("priority", "normal")),
            context=data.get("context", {}),
            created_at=data.get("created_at", data["timestamp"]),
            accepted_at=data.get("accepted_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            failed_at=data.get("failed_at"),
            dependencies=data.get("dependencies", []),
            timeout_minutes=data.get("timeout_minutes", 60),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            error_message=data.get("error_message"),
            notes=data.get("notes", [])
        )


# CLI interface
if __name__ == "__main__":
    import sys
    
    manager = HandoffManager()
    
    if len(sys.argv) < 2:
        print("Usage: python handoff_manager.py <command> [args]")
        print("\nCommands:")
        print("  pending [agent]     - List pending handoffs")
        print("  metrics             - Show handoff metrics")
        print("  check-timeouts      - Check for expired handoffs")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "pending":
        agent = sys.argv[2] if len(sys.argv) > 2 else None
        handoffs = manager.get_pending_handoffs(agent)
        print(json.dumps(handoffs, indent=2))
    
    elif command == "metrics":
        metrics = manager.get_metrics()
        print(json.dumps(metrics, indent=2))
    
    elif command == "check-timeouts":
        timed_out = manager.check_timeouts()
        if timed_out:
            print(f"Found {len(timed_out)} timed out handoffs:")
            print(json.dumps(timed_out, indent=2))
        else:
            print("No timed out handoffs")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
