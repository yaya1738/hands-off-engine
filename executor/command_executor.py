"""Legacy command-execution compatibility surface.

The historical executor is intentionally fail-closed. Autonomous execution must
route through the authoritative FactoryAuthorityGateway rather than allowing a
caller-controlled task.mode to invoke subprocesses directly.
"""

import datetime

from .task_protocol import ExecutionResult
from .safety_rules import SafetyAuditor


class CommandExecutor:
    def __init__(self, config):
        self.config = config
        self.auditor = SafetyAuditor(config)

    def execute(self, task) -> ExecutionResult:
        start_time = datetime.datetime.now().isoformat()
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
                mode=task.mode,
            )

        mode = str(task.mode).upper()
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
                mode="DRYRUN",
            )

        return ExecutionResult(
            task_id=task.task_id,
            status="rejected",
            exit_code=None,
            stdout="",
            stderr="",
            reason="Legacy direct execution is disabled; route through FactoryAuthorityGateway.",
            started_at=start_time,
            finished_at=datetime.datetime.now().isoformat(),
            mode=mode,
        )
