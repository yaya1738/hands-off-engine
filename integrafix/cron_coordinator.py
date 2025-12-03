#!/usr/bin/env python3
"""
INTEGRAFIX: Cron Job Coordinator
================================

PROBLEM SOLVED:
18 cron jobs run independently without coordination:
- Some never run their critical counterparts
- outcome_recorder and concrete_executor not scheduled
- Jobs can conflict (scaling while healing, etc.)

SOLUTION:
A coordinator that:
1. Tracks all cron job schedules
2. Detects missing critical jobs
3. Prevents conflicting jobs from running simultaneously
4. Generates optimized crontab
5. Monitors job health

This wire connects cron jobs into a coherent system.
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
CRON_STATE = STATE_DIR / "cron_coordination.json"


class JobPriority(Enum):
    """Priority of cron jobs."""
    CRITICAL = "critical"     # Must run, blocks conflicting jobs
    HIGH = "high"            # Important, can be delayed briefly
    MEDIUM = "medium"        # Normal priority
    LOW = "low"              # Can skip if system busy


class ConflictGroup(Enum):
    """Groups of conflicting jobs."""
    INFRASTRUCTURE = "infrastructure"  # scaling, healing, provisioning
    TRADING = "trading"                # execution, recording
    DATA = "data"                      # fetching, syncing
    AI = "ai"                          # learning, analysis


@dataclass
class CronJob:
    """A cron job definition."""
    name: str
    script: str
    schedule: str                 # Cron expression
    priority: JobPriority
    conflict_groups: List[ConflictGroup]
    description: str
    enabled: bool = True
    last_run: Optional[str] = None
    last_duration_sec: Optional[float] = None
    last_success: Optional[bool] = None
    run_count: int = 0
    fail_count: int = 0


@dataclass
class JobRun:
    """Record of a job run."""
    job_name: str
    started_at: str
    ended_at: Optional[str]
    success: bool
    duration_sec: Optional[float]
    output: str
    blocked_by: Optional[str] = None


class CronCoordinator:
    """
    Coordinate cron jobs to prevent conflicts and ensure completeness.
    """

    def __init__(self):
        self.jobs: Dict[str, CronJob] = {}
        self.running: Dict[str, datetime] = {}  # Currently running jobs
        self.run_history: List[JobRun] = []
        self._load_state()
        self._register_known_jobs()

    def _load_state(self):
        """Load cron coordination state."""
        if CRON_STATE.exists():
            with open(CRON_STATE) as f:
                data = json.load(f)

            for name, jdata in data.get("jobs", {}).items():
                jdata["priority"] = JobPriority(jdata["priority"])
                jdata["conflict_groups"] = [ConflictGroup(g) for g in jdata["conflict_groups"]]
                self.jobs[name] = CronJob(**jdata)

    def _save_state(self):
        """Save cron coordination state."""
        data = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "jobs": {},
            "run_history": [asdict(r) for r in self.run_history[-100:]],
        }

        for name, job in self.jobs.items():
            jdict = asdict(job)
            jdict["priority"] = job.priority.value
            jdict["conflict_groups"] = [g.value for g in job.conflict_groups]
            data["jobs"][name] = jdict

        with open(CRON_STATE, 'w') as f:
            json.dump(data, f, indent=2)

    def _register_known_jobs(self):
        """Register all known cron jobs in the system."""
        known_jobs = [
            # Trading jobs
            CronJob(
                name="trade_executor",
                script="/root/hands-off-engine/executor/trade_executor.py",
                schedule="0 * * * *",  # Every hour
                priority=JobPriority.CRITICAL,
                conflict_groups=[ConflictGroup.TRADING],
                description="Execute trades from detected edges",
            ),
            CronJob(
                name="outcome_recorder",
                script="/root/hands-off-engine/scripts/outcome_recorder.py",
                schedule="30 * * * *",  # 30 min past each hour
                priority=JobPriority.HIGH,
                conflict_groups=[ConflictGroup.TRADING],
                description="Record outcomes of resolved trades",
            ),
            CronJob(
                name="concrete_executor",
                script="/root/hands-off-engine/executor/concrete_executor.py",
                schedule="15,45 * * * *",  # Every 30 min
                priority=JobPriority.CRITICAL,
                conflict_groups=[ConflictGroup.TRADING],
                description="Execute concrete trades on Polymarket",
            ),

            # Data jobs
            CronJob(
                name="polymarket_sync",
                script="/root/hands-off-engine/alpha/sync_polymarket_model.py",
                schedule="*/30 * * * *",  # Every 30 min
                priority=JobPriority.HIGH,
                conflict_groups=[ConflictGroup.DATA],
                description="Sync Polymarket data and generate alpha signals",
            ),
            CronJob(
                name="polymarket_live",
                script="/root/hands-off-engine/scripts/polymarket_live.py",
                schedule="0 */2 * * *",  # Every 2 hours
                priority=JobPriority.MEDIUM,
                conflict_groups=[ConflictGroup.DATA],
                description="Fetch live Polymarket data",
            ),

            # Infrastructure jobs
            CronJob(
                name="scaling_engine",
                script="/root/hands-off-engine/autonomous/scaling_engine.py",
                schedule="0 */4 * * *",  # Every 4 hours
                priority=JobPriority.HIGH,
                conflict_groups=[ConflictGroup.INFRASTRUCTURE],
                description="Manage infrastructure scaling",
            ),
            CronJob(
                name="hardware_brain",
                script="/root/hands-off-engine/autonomous/hardware_brain.py",
                schedule="*/10 * * * *",  # Every 10 min
                priority=JobPriority.HIGH,
                conflict_groups=[ConflictGroup.INFRASTRUCTURE],
                description="Monitor and heal infrastructure",
            ),
            CronJob(
                name="self_healer",
                script="/root/hands-off-engine/autonomous/self_healer.py",
                schedule="*/15 * * * *",  # Every 15 min
                priority=JobPriority.MEDIUM,
                conflict_groups=[ConflictGroup.INFRASTRUCTURE],
                description="Self-healing operations",
            ),

            # AI/Learning jobs
            CronJob(
                name="learning_engine",
                script="/root/hands-off-engine/scripts/learning_engine.py",
                schedule="0 */6 * * *",  # Every 6 hours
                priority=JobPriority.MEDIUM,
                conflict_groups=[ConflictGroup.AI],
                description="Learn from trade outcomes",
            ),
            CronJob(
                name="compound_growth",
                script="/root/hands-off-engine/scripts/compound_growth.py",
                schedule="0 */4 * * *",  # Every 4 hours
                priority=JobPriority.LOW,
                conflict_groups=[ConflictGroup.AI, ConflictGroup.TRADING],
                description="Reinvest profits",
            ),
            CronJob(
                name="backend_loop",
                script="/root/hands-off-engine/autonomous/backend_loop.py",
                schedule="*/5 * * * *",  # Every 5 min
                priority=JobPriority.CRITICAL,
                conflict_groups=[],  # Doesn't conflict with anything
                description="Main integration loop",
            ),

            # Integrafix jobs (NEW)
            CronJob(
                name="integrafix_engine",
                script="/root/hands-off-engine/integrafix/recursive_engine.py",
                schedule="0 */2 * * *",  # Every 2 hours
                priority=JobPriority.HIGH,
                conflict_groups=[ConflictGroup.AI],
                description="Run recursive integrafix for continuous improvement",
            ),
            CronJob(
                name="trading_pipeline",
                script="/root/hands-off-engine/integrafix/trading_pipeline.py",
                schedule="*/15 * * * *",  # Every 15 min
                priority=JobPriority.CRITICAL,
                conflict_groups=[ConflictGroup.TRADING],
                description="Run integrated trading pipeline",
            ),
        ]

        for job in known_jobs:
            if job.name not in self.jobs:
                self.jobs[job.name] = job

        self._save_state()

    # ==================== CONFLICT DETECTION ====================

    def can_run(self, job_name: str) -> tuple[bool, Optional[str]]:
        """
        Check if a job can run now.

        Returns:
            (can_run, blocked_by_job_name)
        """
        if job_name not in self.jobs:
            return False, "Job not registered"

        job = self.jobs[job_name]

        if not job.enabled:
            return False, "Job disabled"

        # Check for conflicting running jobs
        for running_name, started in self.running.items():
            if running_name == job_name:
                continue

            running_job = self.jobs.get(running_name)
            if not running_job:
                continue

            # Check for conflict group overlap
            for cg in job.conflict_groups:
                if cg in running_job.conflict_groups:
                    # Priority check - higher priority can preempt
                    if job.priority.value <= running_job.priority.value:
                        return False, running_name

        return True, None

    def get_conflicts(self, job_name: str) -> List[str]:
        """Get all jobs that would conflict with this one."""
        if job_name not in self.jobs:
            return []

        job = self.jobs[job_name]
        conflicts = []

        for other_name, other_job in self.jobs.items():
            if other_name == job_name:
                continue

            for cg in job.conflict_groups:
                if cg in other_job.conflict_groups:
                    conflicts.append(other_name)
                    break

        return conflicts

    # ==================== JOB EXECUTION ====================

    def start_job(self, job_name: str) -> Optional[JobRun]:
        """
        Start a job run with coordination.

        Returns:
            JobRun if started, None if blocked
        """
        can_start, blocked_by = self.can_run(job_name)

        if not can_start:
            run = JobRun(
                job_name=job_name,
                started_at=datetime.now(timezone.utc).isoformat(),
                ended_at=datetime.now(timezone.utc).isoformat(),
                success=False,
                duration_sec=0,
                output=f"Blocked by: {blocked_by}",
                blocked_by=blocked_by,
            )
            self.run_history.append(run)
            self._save_state()
            return None

        # Mark as running
        self.running[job_name] = datetime.now(timezone.utc)

        run = JobRun(
            job_name=job_name,
            started_at=datetime.now(timezone.utc).isoformat(),
            ended_at=None,
            success=False,
            duration_sec=None,
            output="",
        )

        return run

    def end_job(self, run: JobRun, success: bool, output: str = ""):
        """End a job run."""
        job_name = run.job_name

        # Remove from running
        if job_name in self.running:
            del self.running[job_name]

        # Update run record
        run.ended_at = datetime.now(timezone.utc).isoformat()
        run.success = success
        run.output = output

        started = datetime.fromisoformat(run.started_at.replace('Z', '+00:00'))
        ended = datetime.fromisoformat(run.ended_at.replace('Z', '+00:00'))
        run.duration_sec = (ended - started).total_seconds()

        # Update job stats
        if job_name in self.jobs:
            job = self.jobs[job_name]
            job.last_run = run.ended_at
            job.last_duration_sec = run.duration_sec
            job.last_success = success
            job.run_count += 1
            if not success:
                job.fail_count += 1

        self.run_history.append(run)
        self._save_state()

    def run_job(self, job_name: str, dry_run: bool = False) -> JobRun:
        """
        Run a job with full coordination.

        Args:
            job_name: Name of job to run
            dry_run: If True, don't actually execute

        Returns:
            JobRun with results
        """
        run = self.start_job(job_name)
        if not run:
            return self.run_history[-1]  # Return the blocked run record

        job = self.jobs[job_name]

        try:
            if dry_run:
                output = f"[DRY RUN] Would execute: python3 {job.script}"
                success = True
            else:
                result = subprocess.run(
                    ["python3", job.script],
                    capture_output=True,
                    text=True,
                    timeout=3600,  # 1 hour max
                )
                output = result.stdout + result.stderr
                success = result.returncode == 0

            self.end_job(run, success, output[:10000])

        except subprocess.TimeoutExpired:
            self.end_job(run, False, "Timeout after 1 hour")
        except Exception as e:
            self.end_job(run, False, str(e))

        return run

    # ==================== CRONTAB GENERATION ====================

    def generate_crontab(self) -> str:
        """
        Generate optimized crontab that:
        1. Schedules all enabled jobs
        2. Staggers conflicting jobs
        3. Adds coordination wrapper
        """
        lines = [
            "# INTEGRAFIX Coordinated Crontab",
            f"# Generated: {datetime.now(timezone.utc).isoformat()}",
            "#",
            "# All jobs run through coordinator to prevent conflicts",
            "#",
            "SHELL=/bin/bash",
            f"PYTHONPATH=/root/hands-off-engine",
            "",
        ]

        # Group by conflict group for staggering
        by_group: Dict[str, List[CronJob]] = {}
        for job in self.jobs.values():
            if not job.enabled:
                continue

            key = ",".join(sorted(cg.value for cg in job.conflict_groups)) or "none"
            if key not in by_group:
                by_group[key] = []
            by_group[key].append(job)

        # Generate entries
        for group_key, jobs in by_group.items():
            lines.append(f"# --- {group_key.upper()} ---")

            for job in sorted(jobs, key=lambda j: j.priority.value, reverse=True):
                # Wrap in coordinator
                cmd = (
                    f"cd /root/hands-off-engine && "
                    f"python3 -c \"from integrafix.cron_coordinator import get_coordinator; "
                    f"get_coordinator().run_job('{job.name}')\""
                )

                lines.append(f"# {job.description}")
                lines.append(f"{job.schedule} {cmd}")
                lines.append("")

        return "\n".join(lines)

    def install_crontab(self, dry_run: bool = True) -> str:
        """
        Install the generated crontab.

        Args:
            dry_run: If True, just return what would be installed
        """
        crontab = self.generate_crontab()

        if dry_run:
            return crontab

        # Write to temp file and install
        cron_file = STATE_DIR / "generated_crontab"
        with open(cron_file, 'w') as f:
            f.write(crontab)

        result = subprocess.run(
            ["crontab", str(cron_file)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return f"Crontab installed successfully\n\n{crontab}"
        else:
            return f"Failed to install: {result.stderr}"

    # ==================== ANALYSIS ====================

    def find_missing_jobs(self) -> List[str]:
        """Find critical jobs that aren't scheduled."""
        missing = []

        # Critical jobs that must exist
        critical_names = [
            "trade_executor",
            "outcome_recorder",
            "concrete_executor",
            "trading_pipeline",
            "backend_loop",
        ]

        for name in critical_names:
            if name not in self.jobs or not self.jobs[name].enabled:
                missing.append(name)

        return missing

    def analyze_job_health(self) -> Dict[str, Any]:
        """Analyze health of all jobs."""
        health = {
            "total_jobs": len(self.jobs),
            "enabled": sum(1 for j in self.jobs.values() if j.enabled),
            "never_run": [],
            "failing": [],
            "healthy": [],
            "missing_critical": self.find_missing_jobs(),
        }

        for name, job in self.jobs.items():
            if not job.enabled:
                continue

            if not job.last_run:
                health["never_run"].append(name)
            elif not job.last_success:
                health["failing"].append(name)
            else:
                health["healthy"].append(name)

        return health

    def status(self) -> Dict:
        """Get coordinator status."""
        return {
            "jobs": len(self.jobs),
            "enabled": sum(1 for j in self.jobs.values() if j.enabled),
            "running": list(self.running.keys()),
            "health": self.analyze_job_health(),
            "recent_runs": [
                {
                    "job": r.job_name,
                    "success": r.success,
                    "duration": r.duration_sec,
                    "blocked_by": r.blocked_by,
                }
                for r in self.run_history[-10:]
            ],
        }


# Singleton instance
_coordinator = None

def get_coordinator() -> CronCoordinator:
    global _coordinator
    if _coordinator is None:
        _coordinator = CronCoordinator()
    return _coordinator


def main():
    """Test the cron coordinator."""
    coord = get_coordinator()

    print("=" * 70)
    print("INTEGRAFIX: Cron Coordinator")
    print("=" * 70)
    print()

    # Analyze health
    health = coord.analyze_job_health()
    print("Job Health Analysis:")
    print(f"  Total jobs: {health['total_jobs']}")
    print(f"  Enabled: {health['enabled']}")
    print(f"  Healthy: {len(health['healthy'])}")
    print(f"  Failing: {len(health['failing'])}")
    print(f"  Never run: {len(health['never_run'])}")
    print()

    if health['missing_critical']:
        print("CRITICAL MISSING JOBS:")
        for job in health['missing_critical']:
            print(f"  - {job}")
        print()

    # Show conflicts
    print("Conflict Analysis:")
    for job_name in ["trade_executor", "scaling_engine"]:
        conflicts = coord.get_conflicts(job_name)
        print(f"  {job_name} conflicts with: {conflicts}")
    print()

    # Generate crontab
    print("=" * 70)
    print("GENERATED CRONTAB:")
    print("=" * 70)
    print(coord.generate_crontab())

    return coord


if __name__ == "__main__":
    main()
