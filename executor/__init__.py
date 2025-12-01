"""
Autonomous Executor Module

A safe, deterministic execution engine that provides:
- Safety guardrails (SafetyAuditor)
- Command execution with DRYRUN/LIVE modes
- Structured task/result protocol
"""

from .task_protocol import ExecutionTask, ExecutionResult
from .safety_rules import SafetyAuditor
from .command_executor import CommandExecutor
from .autonomous_agent import run_agent_single_task, load_config

__all__ = [
    "ExecutionTask",
    "ExecutionResult",
    "SafetyAuditor",
    "CommandExecutor",
    "run_agent_single_task",
    "load_config",
]
