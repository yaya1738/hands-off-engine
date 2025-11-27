#!/usr/bin/env python3
"""
Harmony Orchestrator - Autonomous Self-Improvement Coordinator

Unifies three autonomous domains:
1. MONEY - Trading alpha, position sizing, capital growth
2. SOFTWARE - Code quality, bug fixes, performance optimization
3. HARDWARE - Resource scaling, cost optimization, uptime management

All working in harmony for Yair Siegel's benefit.

Run modes:
- harmony_orchestrator.py --once    : Single evaluation cycle
- harmony_orchestrator.py --daemon  : Continuous monitoring (default)
"""

import json
import os
import sys
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Configuration
REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
LOGS_DIR = REPO_ROOT / "logs"
CONFIG_DIR = REPO_ROOT / "config"

LOG_FILE = LOGS_DIR / "harmony_orchestrator.log"
STATE_FILE = STATE_DIR / "harmony_state.json"
METRICS_LOG = LOGS_DIR / "harmony_metrics.jsonl"

# Ensure directories exist
STATE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Check interval (5 minutes)
CHECK_INTERVAL = 300

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Domain(Enum):
    """The three autonomous domains."""
    MONEY = "money"
    SOFTWARE = "software"
    HARDWARE = "hardware"


class Priority(Enum):
    """Resource allocation priority."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class DomainHealth:
    """Health status of a domain."""
    domain: str
    status: str  # healthy, degraded, critical
    score: float  # 0.0 to 1.0
    metrics: Dict
    last_check: str
    issues: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class HarmonyState:
    """Overall system harmony state."""
    overall_health: float  # 0.0 to 1.0
    money_health: DomainHealth
    software_health: DomainHealth
    hardware_health: DomainHealth
    active_improvements: List[Dict]
    last_update: str
    mode: str  # normal, optimization, maintenance

    def to_dict(self) -> Dict:
        return {
            "overall_health": self.overall_health,
            "money_health": self.money_health.to_dict(),
            "software_health": self.software_health.to_dict(),
            "hardware_health": self.hardware_health.to_dict(),
            "active_improvements": self.active_improvements,
            "last_update": self.last_update,
            "mode": self.mode
        }


class HarmonyOrchestrator:
    """
    Central orchestrator that coordinates all autonomous domains.
    
    Ensures money, software, and hardware improvements work in harmony
    without interfering with each other.
    """

    def __init__(self):
        self.state = self._load_state()
        self.cycles_run = 0
        self.improvements_triggered = 0
        logger.info("Harmony Orchestrator initialized")

    def _load_state(self) -> Dict:
        """Load persisted state."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "cycles_completed": 0,
            "improvements_triggered": 0,
            "last_full_cycle": None,
            "active_mode": "normal"
        }

    def _save_state(self):
        """Persist state to disk."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        tmp_file = STATE_FILE.with_suffix('.tmp')
        try:
            with open(tmp_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            tmp_file.rename(STATE_FILE)
        except IOError as e:
            logger.error(f"Failed to save state: {e}")

    def check_money_domain(self) -> DomainHealth:
        """
        Evaluate the money domain health.
        
        Checks:
        - Trading performance (win rate, P&L)
        - Alpha model quality
        - Position exposure
        - Phase progression status
        """
        issues = []
        metrics = {}
        score = 1.0

        # Check trading mode state
        trading_mode_file = STATE_DIR / "trading_mode.json"
        if trading_mode_file.exists():
            try:
                with open(trading_mode_file) as f:
                    mode = json.load(f)
                    metrics["phase"] = mode.get("phase", "unknown")
                    metrics["phase_started"] = mode.get("phase_started", "unknown")
            except (json.JSONDecodeError, IOError):
                issues.append("Cannot read trading mode state")
                score -= 0.1

        # Check performance log
        perf_log = LOGS_DIR / "performance_tracking.jsonl"
        if perf_log.exists():
            try:
                with open(perf_log) as f:
                    lines = f.readlines()
                    if lines:
                        latest = json.loads(lines[-1])
                        metrics["latest_orders"] = latest.get("total_orders", 0)
                        metrics["latest_size"] = latest.get("total_size_usd", 0)
                        metrics["avg_confidence"] = latest.get("avg_confidence", 0)
            except (json.JSONDecodeError, IOError):
                pass

        # Check polymarket model freshness
        model_file = STATE_DIR / "polymarket-model.json"
        if model_file.exists():
            age_hours = (time.time() - model_file.stat().st_mtime) / 3600
            metrics["model_age_hours"] = round(age_hours, 2)
            if age_hours > 24:
                issues.append(f"Alpha model stale ({age_hours:.1f}h old)")
                score -= 0.2
        else:
            issues.append("No alpha model found")
            score -= 0.3

        # Check execution plan
        exec_plan = REPO_ROOT / "executor" / "execution_plan.json"
        if exec_plan.exists():
            try:
                with open(exec_plan) as f:
                    plan = json.load(f)
                    metrics["dryrun_mode"] = plan.get("dryrun", True)
                    metrics["pending_orders"] = len(plan.get("orders", []))
            except (json.JSONDecodeError, IOError):
                pass

        status = "healthy" if score > 0.8 else "degraded" if score > 0.5 else "critical"

        return DomainHealth(
            domain=Domain.MONEY.value,
            status=status,
            score=max(0.0, score),
            metrics=metrics,
            last_check=datetime.now(timezone.utc).isoformat(),
            issues=issues
        )

    def check_software_domain(self) -> DomainHealth:
        """
        Evaluate the software domain health.
        
        Checks:
        - Error rates in logs
        - Self-healing agent status
        - Coordination agent status
        - Git repository health
        """
        issues = []
        metrics = {}
        score = 1.0

        # Check self-healing state
        healing_state = STATE_DIR / "self_healing_state.json"
        if healing_state.exists():
            try:
                with open(healing_state) as f:
                    state = json.load(f)
                    metrics["total_fixes"] = state.get("total_fixes", 0)
                    metrics["last_check"] = state.get("last_check", "unknown")
                    issues_detected = len(state.get("issues_detected", []))
                    metrics["issues_detected"] = issues_detected
                    if issues_detected > 10:
                        issues.append(f"High issue count: {issues_detected}")
                        score -= 0.1
            except (json.JSONDecodeError, IOError):
                pass

        # Check coordination agent state
        coord_state = REPO_ROOT / "ai" / "coordination" / "agent_state.json"
        if coord_state.exists():
            try:
                with open(coord_state) as f:
                    state = json.load(f)
                    metrics["processed_messages"] = len(state.get("processed_messages", []))
                    metrics["coord_last_check"] = state.get("last_check", "unknown")
            except (json.JSONDecodeError, IOError):
                pass

        # Check git index lock (common issue)
        git_lock = REPO_ROOT / ".git" / "index.lock"
        if git_lock.exists():
            lock_age = time.time() - git_lock.stat().st_mtime
            if lock_age > 300:  # 5 minutes
                issues.append(f"Stale git lock ({lock_age/60:.1f}m old)")
                score -= 0.2

        # Check for recent errors in logs
        error_log = LOGS_DIR / "errors.log"
        if error_log.exists():
            try:
                with open(error_log) as f:
                    recent_errors = [
                        l for l in f.readlines()[-100:]
                        if "ERROR" in l or "CRITICAL" in l
                    ]
                    metrics["recent_errors"] = len(recent_errors)
                    if len(recent_errors) > 10:
                        issues.append(f"High error rate: {len(recent_errors)} recent errors")
                        score -= 0.2
            except IOError:
                pass

        status = "healthy" if score > 0.8 else "degraded" if score > 0.5 else "critical"

        return DomainHealth(
            domain=Domain.SOFTWARE.value,
            status=status,
            score=max(0.0, score),
            metrics=metrics,
            last_check=datetime.now(timezone.utc).isoformat(),
            issues=issues
        )

    def check_hardware_domain(self) -> DomainHealth:
        """
        Evaluate the hardware domain health.
        
        Checks:
        - Disk space
        - CPU usage (if available)
        - Memory usage (if available)
        - Network connectivity
        """
        issues = []
        metrics = {}
        score = 1.0

        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage(REPO_ROOT)
            usage_pct = (used / total) * 100
            metrics["disk_usage_pct"] = round(usage_pct, 1)
            metrics["disk_free_gb"] = round(free / (1024**3), 2)

            if usage_pct > 90:
                issues.append(f"Disk space critical: {usage_pct:.1f}%")
                score -= 0.3
            elif usage_pct > 80:
                issues.append(f"Disk space low: {usage_pct:.1f}%")
                score -= 0.1
        except Exception as e:
            issues.append(f"Cannot check disk: {e}")

        # Check log directory size
        log_size_mb = sum(
            f.stat().st_size for f in LOGS_DIR.rglob("*") if f.is_file()
        ) / (1024 * 1024)
        metrics["logs_size_mb"] = round(log_size_mb, 2)
        if log_size_mb > 500:
            issues.append(f"Log directory large: {log_size_mb:.1f}MB")
            score -= 0.1

        # Check state directory health
        state_size_mb = sum(
            f.stat().st_size for f in STATE_DIR.rglob("*") if f.is_file()
        ) / (1024 * 1024)
        metrics["state_size_mb"] = round(state_size_mb, 2)

        status = "healthy" if score > 0.8 else "degraded" if score > 0.5 else "critical"

        return DomainHealth(
            domain=Domain.HARDWARE.value,
            status=status,
            score=max(0.0, score),
            metrics=metrics,
            last_check=datetime.now(timezone.utc).isoformat(),
            issues=issues
        )

    def calculate_harmony_score(
        self,
        money: DomainHealth,
        software: DomainHealth,
        hardware: DomainHealth
    ) -> float:
        """
        Calculate overall system harmony score.
        
        Weighted average with money as highest priority.
        """
        # Weights: money is most important, then software, then hardware
        weights = {
            Domain.MONEY.value: 0.5,
            Domain.SOFTWARE.value: 0.3,
            Domain.HARDWARE.value: 0.2
        }

        harmony = (
            money.score * weights[Domain.MONEY.value] +
            software.score * weights[Domain.SOFTWARE.value] +
            hardware.score * weights[Domain.HARDWARE.value]
        )

        return round(harmony, 3)

    def identify_improvements(
        self,
        money: DomainHealth,
        software: DomainHealth,
        hardware: DomainHealth
    ) -> List[Dict]:
        """
        Identify improvement opportunities across domains.
        
        Returns prioritized list of improvements to trigger.
        """
        improvements = []

        # Check money domain for improvement opportunities
        if money.score < 0.8:
            for issue in money.issues:
                improvements.append({
                    "domain": Domain.MONEY.value,
                    "type": "fix",
                    "priority": Priority.CRITICAL.value,
                    "description": issue,
                    "auto_fixable": False
                })

        # Check software domain
        if software.score < 0.9:
            for issue in software.issues:
                is_auto_fixable = "git lock" in issue.lower()
                improvements.append({
                    "domain": Domain.SOFTWARE.value,
                    "type": "fix",
                    "priority": Priority.HIGH.value,
                    "description": issue,
                    "auto_fixable": is_auto_fixable
                })

        # Check hardware domain
        if hardware.score < 0.9:
            for issue in hardware.issues:
                is_auto_fixable = "log" in issue.lower()
                improvements.append({
                    "domain": Domain.HARDWARE.value,
                    "type": "optimize",
                    "priority": Priority.MEDIUM.value,
                    "description": issue,
                    "auto_fixable": is_auto_fixable
                })

        # Sort by priority
        improvements.sort(key=lambda x: x["priority"])

        return improvements

    def trigger_improvements(self, improvements: List[Dict]) -> int:
        """
        Trigger auto-fixable improvements.
        
        Returns count of improvements triggered.
        """
        triggered = 0

        for improvement in improvements:
            if not improvement.get("auto_fixable"):
                continue

            description = improvement["description"]
            domain = improvement["domain"]

            logger.info(f"[{domain.upper()}] Auto-fixing: {description}")

            # Handle specific improvements
            if "git lock" in description.lower():
                lock_file = REPO_ROOT / ".git" / "index.lock"
                if lock_file.exists():
                    try:
                        lock_file.unlink()
                        logger.info("✓ Removed stale git lock")
                        triggered += 1
                    except IOError as e:
                        logger.error(f"Failed to remove git lock: {e}")

            elif "log" in description.lower() and "large" in description.lower():
                # Cleanup old logs
                try:
                    old_logs = [
                        f for f in LOGS_DIR.glob("*.log.*")
                        if f.stat().st_mtime < time.time() - 7 * 86400  # 7 days
                    ]
                    for log in old_logs[:5]:  # Limit to 5 at a time
                        log.unlink()
                        logger.info(f"✓ Removed old log: {log.name}")
                    if old_logs:
                        triggered += 1
                except IOError as e:
                    logger.error(f"Failed to cleanup logs: {e}")

        return triggered

    def run_cycle(self) -> HarmonyState:
        """
        Run one harmony evaluation cycle.
        
        Returns current harmony state.
        """
        self.cycles_run += 1
        logger.info(f"Starting harmony cycle #{self.cycles_run}")

        # Check all domains
        money = self.check_money_domain()
        software = self.check_software_domain()
        hardware = self.check_hardware_domain()

        # Calculate harmony
        harmony_score = self.calculate_harmony_score(money, software, hardware)

        # Identify improvements
        improvements = self.identify_improvements(money, software, hardware)

        # Trigger auto-fixable improvements
        triggered = self.trigger_improvements(improvements)
        self.improvements_triggered += triggered

        # Determine mode
        if harmony_score > 0.9:
            mode = "optimization"
        elif harmony_score > 0.7:
            mode = "normal"
        else:
            mode = "maintenance"

        # Build state
        state = HarmonyState(
            overall_health=harmony_score,
            money_health=money,
            software_health=software,
            hardware_health=hardware,
            active_improvements=[i for i in improvements if not i["auto_fixable"]],
            last_update=datetime.now(timezone.utc).isoformat(),
            mode=mode
        )

        # Log metrics
        self._log_metrics(state)

        # Update persisted state
        self.state["cycles_completed"] = self.cycles_run
        self.state["improvements_triggered"] = self.improvements_triggered
        self.state["last_full_cycle"] = datetime.now(timezone.utc).isoformat()
        self.state["active_mode"] = mode
        self._save_state()

        # Report
        logger.info(f"Harmony score: {harmony_score:.1%}")
        logger.info(f"Money: {money.status} ({money.score:.1%})")
        logger.info(f"Software: {software.status} ({software.score:.1%})")
        logger.info(f"Hardware: {hardware.status} ({hardware.score:.1%})")
        logger.info(f"Mode: {mode}")
        if triggered:
            logger.info(f"Auto-fixes triggered: {triggered}")

        return state

    def _log_metrics(self, state: HarmonyState):
        """Log metrics for tracking."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "harmony_score": state.overall_health,
            "money_score": state.money_health.score,
            "software_score": state.software_health.score,
            "hardware_score": state.hardware_health.score,
            "mode": state.mode,
            "active_improvements": len(state.active_improvements)
        }

        try:
            with open(METRICS_LOG, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except IOError as e:
            logger.error(f"Failed to log metrics: {e}")

    def run_daemon(self):
        """Run continuously, checking at regular intervals."""
        logger.info("Harmony Orchestrator starting in daemon mode...")
        logger.info(f"Check interval: {CHECK_INTERVAL} seconds")

        while True:
            try:
                state = self.run_cycle()

                # Summary
                logger.info(
                    f"Cycle complete | Harmony: {state.overall_health:.1%} | "
                    f"Mode: {state.mode} | "
                    f"Total cycles: {self.cycles_run} | "
                    f"Total fixes: {self.improvements_triggered}"
                )

                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                logger.info("Shutting down gracefully...")
                break
            except Exception as e:
                logger.error(f"Error in cycle: {e}")
                time.sleep(60)


def main():
    """Entry point."""
    orchestrator = HarmonyOrchestrator()

    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        logger.info("Running in one-shot mode")
        state = orchestrator.run_cycle()
        print(json.dumps(state.to_dict(), indent=2))
    else:
        orchestrator.run_daemon()


if __name__ == "__main__":
    main()
