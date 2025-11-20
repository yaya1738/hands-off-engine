"""
AI Nexus - Multi-Brain Orchestration System

This module coordinates multiple AI agents (Copilot, ChatGPT, Claude, etc.) to work
together on complex tasks with full audit trail and cost tracking.
"""

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Import audit logger
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from audit import get_audit_logger
    audit = get_audit_logger(component="ai_nexus")
except ImportError:
    audit = None


class AIProvider(Enum):
    """Supported AI providers"""
    COPILOT = "copilot"
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AITask:
    """Represents a task to be executed by an AI agent"""
    task_id: str
    task_type: str  # plan, code, analyze, decide, etc.
    description: str
    priority: TaskPriority
    provider: Optional[AIProvider] = None  # Auto-select if None
    context: Dict[str, Any] = None
    max_cost: Optional[float] = None  # Cost limit in USD
    timeout: Optional[int] = None  # Timeout in seconds
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.context is None:
            self.context = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        d = asdict(self)
        d['priority'] = self.priority.value if self.priority else None
        d['provider'] = self.provider.value if self.provider else None
        return d


@dataclass
class AIResult:
    """Result from AI task execution"""
    task_id: str
    status: TaskStatus
    provider: AIProvider
    output: Any
    cost: float = 0.0  # Cost in USD
    tokens_used: int = 0
    execution_time: float = 0.0  # Time in seconds
    error: Optional[str] = None
    completed_at: str = None
    
    def __post_init__(self):
        if self.completed_at is None:
            self.completed_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        d = asdict(self)
        d['status'] = self.status.value if self.status else None
        d['provider'] = self.provider.value if self.provider else None
        return d


class AINexus:
    """
    Central AI orchestration system that:
    - Routes tasks to appropriate AI providers
    - Tracks costs and token usage
    - Maintains complete audit trail
    - Enforces budget limits
    - Enables multi-AI collaboration
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize AI Nexus
        
        Args:
            storage_dir: Directory for storing nexus state and logs
        """
        if storage_dir is None:
            # Try ~/hands-off/ai_nexus first, fall back to local
            home_nexus = Path.home() / "hands-off" / "ai_nexus"
            if Path.home() / "hands-off" in Path.home().parent.parent.iterdir():
                storage_dir = str(home_nexus)
            else:
                storage_dir = str(Path(__file__).parent.parent / "logs" / "ai_nexus")
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Task queue and history
        self.tasks: Dict[str, AITask] = {}
        self.results: Dict[str, AIResult] = {}
        
        # Cost tracking
        self.daily_costs: Dict[str, float] = {}  # provider -> cost
        self.budget_limits: Dict[str, float] = {
            AIProvider.COPILOT.value: 100.0,  # $100/day
            AIProvider.CHATGPT.value: 50.0,   # $50/day
            AIProvider.CLAUDE.value: 50.0,    # $50/day
            AIProvider.OPENAI.value: 50.0,    # $50/day
        }
        
        # Load state if exists
        self._load_state()
        
        # Audit nexus initialization
        if audit:
            audit.log_action(
                action_type="ai_nexus_initialized",
                action_data={
                    "storage_dir": str(self.storage_dir),
                    "budget_limits": self.budget_limits
                },
                result="success"
            )
    
    def _load_state(self):
        """Load nexus state from disk"""
        state_file = self.storage_dir / "nexus_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.daily_costs = state.get('daily_costs', {})
            except Exception as e:
                if audit:
                    audit.log_error(
                        error_type="StateLoadError",
                        error_message=str(e),
                        context={"file": str(state_file)}
                    )
    
    def _save_state(self):
        """Save nexus state to disk"""
        state_file = self.storage_dir / "nexus_state.json"
        state = {
            'daily_costs': self.daily_costs,
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            if audit:
                audit.log_error(
                    error_type="StateSaveError",
                    error_message=str(e),
                    context={"file": str(state_file)}
                )
    
    def submit_task(self, task: AITask) -> str:
        """
        Submit a task to the AI Nexus
        
        Args:
            task: AITask to execute
            
        Returns:
            task_id: Unique identifier for tracking
        """
        session_id = f"nexus_task_{task.task_id}"
        
        # Store task
        self.tasks[task.task_id] = task
        
        # Audit task submission
        if audit:
            audit.log_action(
                action_type="ai_task_submitted",
                action_data={
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "priority": task.priority.value,
                    "provider": task.provider.value if task.provider else "auto",
                    "max_cost": task.max_cost
                },
                session_id=session_id
            )
        
        # Auto-select provider if not specified
        if task.provider is None:
            task.provider = self._select_provider(task)
        
        # Check budget
        if not self._check_budget(task.provider, task.max_cost):
            if audit:
                audit.log_error(
                    error_type="BudgetExceeded",
                    error_message=f"Budget exceeded for {task.provider.value}",
                    context={
                        "task_id": task.task_id,
                        "provider": task.provider.value,
                        "daily_cost": self.daily_costs.get(task.provider.value, 0),
                        "limit": self.budget_limits.get(task.provider.value, 0)
                    },
                    session_id=session_id
                )
            return task.task_id
        
        return task.task_id
    
    def _select_provider(self, task: AITask) -> AIProvider:
        """
        Intelligently select best AI provider for task
        
        Criteria:
        - Task type and complexity
        - Current costs and budget availability
        - Provider capabilities
        - Historical performance
        """
        # Simple heuristic for now - prefer provider with most budget remaining
        best_provider = AIProvider.COPILOT
        max_remaining = 0
        
        for provider_str, limit in self.budget_limits.items():
            provider = AIProvider(provider_str)
            used = self.daily_costs.get(provider_str, 0)
            remaining = limit - used
            
            if remaining > max_remaining:
                max_remaining = remaining
                best_provider = provider
        
        if audit:
            audit.log_decision(
                decision_type="provider_selection",
                inputs={
                    "task_type": task.task_type,
                    "task_id": task.task_id,
                    "daily_costs": self.daily_costs,
                    "budget_limits": self.budget_limits
                },
                outputs={
                    "selected_provider": best_provider.value,
                    "budget_remaining": max_remaining
                }
            )
        
        return best_provider
    
    def _check_budget(self, provider: AIProvider, estimated_cost: Optional[float]) -> bool:
        """Check if provider has budget for task"""
        limit = self.budget_limits.get(provider.value, 0)
        used = self.daily_costs.get(provider.value, 0)
        remaining = limit - used
        
        if estimated_cost is None:
            estimated_cost = 1.0  # Assume $1 if not specified
        
        return remaining >= estimated_cost
    
    def record_result(self, result: AIResult):
        """
        Record AI task result with full audit trail
        
        Args:
            result: AIResult from task execution
        """
        session_id = f"nexus_task_{result.task_id}"
        
        # Store result
        self.results[result.task_id] = result
        
        # Update costs
        provider_str = result.provider.value
        self.daily_costs[provider_str] = self.daily_costs.get(provider_str, 0) + result.cost
        
        # Save state
        self._save_state()
        
        # Audit result
        if audit:
            audit.log_action(
                action_type="ai_task_completed",
                action_data={
                    "task_id": result.task_id,
                    "provider": result.provider.value,
                    "status": result.status.value,
                    "cost": result.cost,
                    "tokens_used": result.tokens_used,
                    "execution_time": result.execution_time,
                    "error": result.error
                },
                result="success" if result.status == TaskStatus.COMPLETED else "failed",
                session_id=session_id
            )
        
        # Write to ledger
        self._write_ledger_entry(result)
    
    def _write_ledger_entry(self, result: AIResult):
        """Write entry to action ledger for financial tracking"""
        ledger_file = self.storage_dir / f"ledger_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "ai_task",
            "task_id": result.task_id,
            "provider": result.provider.value,
            "cost": result.cost,
            "tokens": result.tokens_used,
            "status": result.status.value,
            "execution_time": result.execution_time
        }
        
        try:
            with open(ledger_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            if audit:
                audit.log_error(
                    error_type="LedgerWriteError",
                    error_message=str(e),
                    context={"file": str(ledger_file)}
                )
    
    def get_daily_costs(self) -> Dict[str, float]:
        """Get current daily costs by provider"""
        return self.daily_costs.copy()
    
    def get_budget_status(self) -> Dict[str, Dict[str, float]]:
        """Get budget status for all providers"""
        status = {}
        for provider_str, limit in self.budget_limits.items():
            used = self.daily_costs.get(provider_str, 0)
            status[provider_str] = {
                "limit": limit,
                "used": used,
                "remaining": limit - used,
                "utilization": (used / limit * 100) if limit > 0 else 0
            }
        return status
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        task = self.tasks.get(task_id)
        result = self.results.get(task_id)
        
        if not task:
            return None
        
        status = {
            "task": task.to_dict(),
            "result": result.to_dict() if result else None
        }
        return status


# Example usage and testing
if __name__ == "__main__":
    print("AI Nexus - Multi-Brain Orchestration System")
    print("=" * 70)
    
    # Initialize nexus
    nexus = AINexus()
    print(f"✓ AI Nexus initialized")
    print(f"  Storage: {nexus.storage_dir}")
    print()
    
    # Create example task
    task = AITask(
        task_id=str(uuid.uuid4())[:8],
        task_type="planning",
        description="Generate roadmap for risk model implementation",
        priority=TaskPriority.HIGH,
        max_cost=5.0
    )
    
    print(f"Submitting task: {task.description}")
    task_id = nexus.submit_task(task)
    print(f"✓ Task submitted: {task_id}")
    print(f"  Provider: {task.provider.value}")
    print()
    
    # Simulate task completion
    result = AIResult(
        task_id=task_id,
        status=TaskStatus.COMPLETED,
        provider=task.provider,
        output={"plan": "1. Define risk formula\n2. Implement caps\n3. Test with simulations"},
        cost=2.50,
        tokens_used=5000,
        execution_time=12.5
    )
    
    nexus.record_result(result)
    print(f"✓ Task completed and recorded")
    print()
    
    # Show budget status
    print("Budget Status:")
    budget_status = nexus.get_budget_status()
    for provider, status in budget_status.items():
        print(f"  {provider}:")
        print(f"    Used: ${status['used']:.2f} / ${status['limit']:.2f}")
        print(f"    Remaining: ${status['remaining']:.2f}")
        print(f"    Utilization: {status['utilization']:.1f}%")
    print()
    
    print(f"Ledger written to: {nexus.storage_dir}")
