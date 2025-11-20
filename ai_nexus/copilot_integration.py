"""
Copilot Integration for AI Nexus

This module wraps GitHub Copilot operations to route through AI Nexus
for full audit trail and budget tracking.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
import uuid

# Import AI Nexus components
sys.path.insert(0, str(Path(__file__).parent.parent))
from ai_nexus.nexus import AINexus, AITask, AIResult, AIProvider, TaskPriority, TaskStatus
from ai_nexus.ledger import ActionLedger

class CopilotNexusWrapper:
    """
    Wraps Copilot operations to route through AI Nexus
    
    All Copilot actions (code generation, reviews, etc.) are:
    - Tracked in AI Nexus for cost monitoring
    - Recorded in action ledger for financial accountability  
    - Fully audited for transparency
    """
    
    def __init__(self):
        """Initialize Copilot Nexus wrapper"""
        self.nexus = AINexus()
        self.ledger = ActionLedger()
        self.session_id = f"copilot_session_{uuid.uuid4().hex[:8]}"
    
    def start_task(self, task_type: str, description: str, 
                   priority: TaskPriority = TaskPriority.MEDIUM,
                   max_cost: float = 10.0) -> str:
        """
        Start a new Copilot task through AI Nexus
        
        Args:
            task_type: Type of task (code, review, plan, etc.)
            description: Task description
            priority: Task priority
            max_cost: Maximum cost in USD
            
        Returns:
            task_id: Unique identifier for tracking
        """
        task = AITask(
            task_id=str(uuid.uuid4())[:8],
            task_type=task_type,
            description=description,
            priority=priority,
            provider=AIProvider.COPILOT,
            max_cost=max_cost
        )
        
        task_id = self.nexus.submit_task(task)
        return task_id
    
    def complete_task(self, task_id: str, output: Any, 
                     cost: float, tokens_used: int, 
                     execution_time: float, success: bool = True):
        """
        Mark task as complete and record results
        
        Args:
            task_id: Task identifier
            output: Task output/result
            cost: Actual cost in USD
            tokens_used: Number of tokens consumed
            execution_time: Execution time in seconds
            success: Whether task completed successfully
        """
        result = AIResult(
            task_id=task_id,
            status=TaskStatus.COMPLETED if success else TaskStatus.FAILED,
            provider=AIProvider.COPILOT,
            output=output,
            cost=cost,
            tokens_used=tokens_used,
            execution_time=execution_time
        )
        
        # Record in nexus
        self.nexus.record_result(result)
        
        # Record in ledger
        self.ledger.record_ai_task(
            task_id=task_id,
            provider="copilot",
            cost=cost,
            tokens=tokens_used,
            success=success,
            metadata={
                "execution_time": execution_time,
                "session_id": self.session_id
            }
        )
    
    def log_code_generation(self, files_changed: int, lines_added: int, 
                           lines_deleted: int, cost: float = 0.5):
        """Log a code generation operation"""
        task_id = self.start_task(
            task_type="code_generation",
            description=f"Generated code: {files_changed} files, +{lines_added}/-{lines_deleted} lines",
            priority=TaskPriority.MEDIUM,
            max_cost=cost * 2  # Allow 2x buffer
        )
        
        # Estimate tokens based on lines
        estimated_tokens = (lines_added + lines_deleted) * 4  # Rough estimate
        
        self.complete_task(
            task_id=task_id,
            output={
                "files_changed": files_changed,
                "lines_added": lines_added,
                "lines_deleted": lines_deleted
            },
            cost=cost,
            tokens_used=estimated_tokens,
            execution_time=files_changed * 2.0,  # Rough estimate
            success=True
        )
        
        return task_id
    
    def log_code_review(self, files_reviewed: int, issues_found: int, cost: float = 1.0):
        """Log a code review operation"""
        task_id = self.start_task(
            task_type="code_review",
            description=f"Reviewed {files_reviewed} files, found {issues_found} issues",
            priority=TaskPriority.HIGH,
            max_cost=cost * 2
        )
        
        estimated_tokens = files_reviewed * 1000  # Rough estimate
        
        self.complete_task(
            task_id=task_id,
            output={
                "files_reviewed": files_reviewed,
                "issues_found": issues_found
            },
            cost=cost,
            tokens_used=estimated_tokens,
            execution_time=files_reviewed * 5.0,
            success=True
        )
        
        return task_id
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current Copilot session"""
        budget_status = self.nexus.get_budget_status()
        copilot_status = budget_status.get(AIProvider.COPILOT.value, {})
        
        # Get ledger summary for today
        ledger_summary = self.ledger.get_daily_summary()
        
        return {
            "session_id": self.session_id,
            "budget": copilot_status,
            "ledger": ledger_summary
        }


# Example usage
if __name__ == "__main__":
    print("Copilot AI Nexus Integration")
    print("=" * 70)
    
    # Initialize wrapper
    wrapper = CopilotNexusWrapper()
    print(f"✓ Copilot wrapper initialized")
    print(f"  Session: {wrapper.session_id}")
    print()
    
    # Simulate code generation
    print("Simulating code generation...")
    task_id = wrapper.log_code_generation(
        files_changed=3,
        lines_added=150,
        lines_deleted=20,
        cost=2.50
    )
    print(f"✓ Code generation logged: {task_id}")
    print()
    
    # Simulate code review
    print("Simulating code review...")
    task_id = wrapper.log_code_review(
        files_reviewed=5,
        issues_found=2,
        cost=1.50
    )
    print(f"✓ Code review logged: {task_id}")
    print()
    
    # Get session summary
    summary = wrapper.get_session_summary()
    print("Session Summary:")
    print(f"  Session ID: {summary['session_id']}")
    print(f"  Budget Used: ${summary['budget']['used']:.2f} / ${summary['budget']['limit']:.2f}")
    print(f"  Budget Remaining: ${summary['budget']['remaining']:.2f}")
    print(f"  Today's Entries: {summary['ledger']['entry_count']}")
    print(f"  Today's Cost: ${summary['ledger']['total_cost']:.2f}")
    print(f"  Today's Profit: ${summary['ledger']['total_profit']:.2f}")
