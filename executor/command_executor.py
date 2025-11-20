import subprocess
import datetime
import json
import sys
from .task_protocol import ExecutionResult
from .safety_rules import SafetyAuditor

class CommandExecutor:
    def __init__(self, config):
        self.config = config
        self.auditor = SafetyAuditor(config)

    def execute(self, task) -> ExecutionResult:
        start_time = datetime.datetime.now().isoformat()

        # 1. Safety Check
        is_safe, reason = self.auditor.audit_task(task)

        if not is_safe:
            return ExecutionResult(
                task_id=task.task_id,
                status="rejected",
                exit_code=None,
                stdout="",
                stderr="",
                reason=reason,
                started_at=start_time,
                finished_at=datetime.datetime.now().isoformat(),
                mode=task.mode
            )

        # 2. Determine Mode (Config overrides Task if Config is strictly DRYRUN?)
        # For V1, let's say Task can request LIVE, but we respect Config default if not specified.
        # Here we just trust the task's requested mode if valid.
        mode = task.mode.upper()

        if mode == "DRYRUN":
            return ExecutionResult(
                task_id=task.task_id,
                status="success",
                exit_code=0,
                stdout=f"[DRYRUN] Would execute: {' '.join(task.command)} in {task.working_dir}",
                stderr="",
                reason="Dry run simulation",
                started_at=start_time,
                finished_at=datetime.datetime.now().isoformat(),
                mode="DRYRUN"
            )

        # 3. Live Execution
        try:
            # Ensure stdout is captured immediately
            proc = subprocess.run(
                task.command,
                cwd=task.working_dir,
                capture_output=True,
                text=True,
                timeout=task.timeout_sec
            )

            status = "success" if proc.returncode == 0 else "error"

            return ExecutionResult(
                task_id=task.task_id,
                status=status,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                reason=None,
                started_at=start_time,
                finished_at=datetime.datetime.now().isoformat(),
                mode="LIVE"
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                task_id=task.task_id,
                status="timeout",
                exit_code=None,
                stdout="",
                stderr=f"Command timed out after {task.timeout_sec}s",
                reason="Timeout",
                started_at=start_time,
                finished_at=datetime.datetime.now().isoformat(),
                mode="LIVE"
            )
        except Exception as e:
             return ExecutionResult(
                task_id=task.task_id,
                status="error",
                exit_code=-1,
                stdout="",
                stderr=str(e),
                reason="Execution exception",
                started_at=start_time,
                finished_at=datetime.datetime.now().isoformat(),
                mode="LIVE"
            )
