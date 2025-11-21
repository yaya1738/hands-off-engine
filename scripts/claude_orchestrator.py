#!/usr/bin/env python3
"""
Autonomous Claude Code Orchestrator

This script autonomously determines when Claude Code analysis/optimization is needed
and invokes Claude Code sessions automatically to serve user Yair Siegel.

Runs continuously (via cron) and invokes Claude Code when:
- System health issues detected
- Performance metrics show degradation
- Optimization opportunities identified
- Scheduled autonomous improvement cycles

Part of CLM/Nexus/System serving Yair Siegel's domain.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class ClaudeOrchestrator:
    """Autonomous orchestrator for Claude Code engagement"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.state_dir = repo_root / 'state'
        self.orchestrator_state = self.state_dir / 'claude_orchestrator.json'
        self.metrics_file = self.state_dir / 'performance_metrics.jsonl'
        self.execution_plan = repo_root / 'executor' / 'execution_plan.json'

    def load_orchestrator_state(self) -> Dict:
        """Load orchestrator state (last Claude invocation, etc.)"""
        if self.orchestrator_state.exists():
            with open(self.orchestrator_state) as f:
                return json.load(f)
        return {
            'last_claude_invocation': None,
            'last_optimization_cycle': None,
            'total_autonomous_invocations': 0
        }

    def save_orchestrator_state(self, state: Dict):
        """Save orchestrator state"""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with open(self.orchestrator_state, 'w') as f:
            json.dump(state, f, indent=2)

    def should_invoke_claude(self, state: Dict) -> tuple[bool, str]:
        """
        Determine if Claude Code should be invoked and why.

        Returns:
            (should_invoke: bool, reason: str)
        """
        now = datetime.now(timezone.utc)

        # Check 1: Daily autonomous optimization cycle
        last_optimization = state.get('last_optimization_cycle')
        if last_optimization:
            last_opt_dt = datetime.fromisoformat(last_optimization)
            if (now - last_opt_dt) > timedelta(hours=24):
                return True, "Daily autonomous optimization cycle due"
        else:
            return True, "Initial autonomous optimization cycle"

        # Check 2: Health issues detected
        health_issue = self.check_health_issues()
        if health_issue:
            return True, f"Health issue detected: {health_issue}"

        # Check 3: Performance degradation
        degradation = self.check_performance_degradation()
        if degradation:
            return True, f"Performance degradation: {degradation}"

        # Check 4: New optimization opportunities
        opportunity = self.check_optimization_opportunities()
        if opportunity:
            return True, f"Optimization opportunity: {opportunity}"

        return False, "No autonomous invocation needed"

    def check_health_issues(self) -> Optional[str]:
        """Check for system health issues"""
        # Check if execution plan is stale
        if self.execution_plan.exists():
            try:
                with open(self.execution_plan) as f:
                    plan = json.load(f)

                plan_ts = plan.get('timestamp', '')
                if plan_ts:
                    ts_clean = plan_ts.replace('Z', '+00:00')
                    plan_dt = datetime.fromisoformat(ts_clean)
                    if plan_dt.tzinfo is None:
                        plan_dt = plan_dt.replace(tzinfo=timezone.utc)

                    age_hours = (datetime.now(timezone.utc) - plan_dt).total_seconds() / 3600
                    if age_hours > 3:  # More than 3 hours old
                        return f"Execution plan stale ({age_hours:.1f} hours old)"
            except Exception as e:
                return f"Error reading execution plan: {e}"
        else:
            return "Execution plan missing"

        return None

    def check_performance_degradation(self) -> Optional[str]:
        """Check for performance degradation in recent metrics"""
        if not self.metrics_file.exists():
            return None

        try:
            # Get last 10 metrics
            recent_metrics = []
            with open(self.metrics_file) as f:
                for line in f:
                    try:
                        metric = json.loads(line)
                        recent_metrics.append(metric)
                    except:
                        continue

            if len(recent_metrics) < 5:
                return None  # Not enough data

            recent_metrics = recent_metrics[-10:]

            # Check for increasing failure rates
            unhealthy_count = sum(
                1 for m in recent_metrics[-5:]
                if not (m.get('health', {}).get('plan_fresh') and
                       m.get('health', {}).get('signals_fresh'))
            )

            if unhealthy_count >= 3:
                return f"{unhealthy_count}/5 recent runs unhealthy"

        except Exception as e:
            return f"Error analyzing metrics: {e}"

        return None

    def check_optimization_opportunities(self) -> Optional[str]:
        """Identify optimization opportunities"""
        if not self.metrics_file.exists():
            return None

        try:
            # Get recent metrics
            recent_metrics = []
            with open(self.metrics_file) as f:
                for line in f:
                    try:
                        recent_metrics.append(json.loads(line))
                    except:
                        continue

            if len(recent_metrics) < 20:  # Need 20+ runs for pattern analysis
                return None

            recent_20 = recent_metrics[-20:]

            # Check if selection rate is consistently very high (>90%)
            avg_selection_rate = sum(
                m.get('alpha_signals', {}).get('selection_rate', 0)
                for m in recent_20
            ) / len(recent_20)

            if avg_selection_rate > 0.90:
                return f"High selection rate ({avg_selection_rate*100:.1f}%) - alpha model tuning needed"

        except Exception as e:
            pass

        return None

    def add_task_to_queue(self, reason: str) -> bool:
        """
        Add an autonomous task to the queue for Claude Code to execute.

        This is more reliable than trying to invoke Claude directly.
        When Claude Code runs (current or future sessions), it will
        check the queue and execute pending tasks.

        Args:
            reason: Why this task is needed

        Returns:
            True if task added successfully
        """
        print(f"[{datetime.now().isoformat()}] Adding autonomous task to queue")
        print(f"Reason: {reason}")

        try:
            # Import task queue (avoiding circular import)
            sys.path.insert(0, str(self.repo_root / 'scripts'))
            from autonomous_task_queue import AutonomousTaskQueue

            queue = AutonomousTaskQueue(self.repo_root)

            # Determine priority based on reason
            priority = 'high' if any(
                keyword in reason.lower()
                for keyword in ['health', 'error', 'failure', 'critical']
            ) else 'normal'

            # Add task
            task_id = queue.add_task(
                title=reason,
                description=self.build_task_description(reason),
                priority=priority,
                source='orchestrator'
            )

            print(f"✓ Task added to queue (ID: {task_id[:8]}...)")
            print("Next Claude Code session will execute this task autonomously")

            return True

        except Exception as e:
            print(f"ERROR: Failed to add task to queue: {e}")
            return False

    def build_task_description(self, reason: str) -> str:
        """Build detailed task description for Claude Code"""
        return f"""Autonomous system task - {reason}

Following autonomous operation protocol (.claude/AUTONOMOUS_OPERATION.md):

1. Assess current system state:
   - Check health via ./scripts/healthcheck.sh
   - Review recent metrics in state/performance_metrics.jsonl
   - Check logs in /var/log/hands-off-engine.log

2. Identify and implement improvements:
   - Fix any issues found
   - Optimize performance
   - Reduce user workload further

3. Document all changes made

This task was created autonomously by the orchestrator system.
Make decisions independently to serve user Yair Siegel.
Focus on tangible improvements that reduce workload and improve system quality.

When complete, mark this task as done in the autonomous task queue.
"""

    def get_system_prompt(self) -> str:
        """Get the system prompt for Claude Code"""
        return """You are operating autonomously as part of user Yair Siegel's servant domain.

Context:
- User: Yair Siegel (aka Joseph Siegel, aka Froggy)
- System: CLM/Nexus/Hands-Off Engine
- Purpose: Serve user autonomously, reduce workload, improve life quality

This session was invoked automatically by the orchestrator system.
Make autonomous decisions to improve the system.
Document all changes.

Refer to .claude/USER_PROFILE.md and .claude/AUTONOMOUS_OPERATION.md for full context.
"""

    def run(self):
        """Main orchestrator run cycle"""
        print(f"[{datetime.now().isoformat()}] Claude Orchestrator - Autonomous Check")
        print("="*60)

        # Load state
        state = self.load_orchestrator_state()

        # Determine if Claude should be invoked
        should_invoke, reason = self.should_invoke_claude(state)

        if should_invoke:
            print(f"✓ Claude Code task needed: {reason}")

            # Add task to queue for Claude Code to execute
            success = self.add_task_to_queue(reason)

            # Update state
            state['total_autonomous_invocations'] += 1
            state['last_claude_invocation'] = datetime.now(timezone.utc).isoformat()

            if 'optimization' in reason.lower() or 'cycle' in reason.lower():
                state['last_optimization_cycle'] = datetime.now(timezone.utc).isoformat()

            self.save_orchestrator_state(state)

            if success:
                print("\n✓ Autonomous task added to queue successfully")
                return 0
            else:
                print("\n✗ Failed to add autonomous task")
                return 1
        else:
            print(f"○ No invocation needed: {reason}")
            return 0


def main():
    repo_root = Path(__file__).parent.parent
    orchestrator = ClaudeOrchestrator(repo_root)
    return orchestrator.run()


if __name__ == '__main__':
    sys.exit(main())
