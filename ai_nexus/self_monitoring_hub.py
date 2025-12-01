"""
Self-Monitoring Hub v1.0

Centralized system health aggregator for the CLM AI Nexus.
Provides unified visibility into all components' health, performance, and learning status.

This module addresses the critical gap: LACK OF UNIFIED SELF-MONITORING.

Features:
- Real-time system health aggregation
- Component status tracking
- Anomaly baseline calculation
- Health score computation
- Alert generation for degraded states
- Integration with existing monitoring systems

API:
    hub = SelfMonitoringHub()
    health = hub.get_system_health()
    score = hub.compute_health_score()
    anomalies = hub.detect_anomalies()

CLI:
    python -m ai_nexus.self_monitoring_hub status
    python -m ai_nexus.self_monitoring_hub health-score
    python -m ai_nexus.self_monitoring_hub anomalies
"""

import json
import os
import sys
import time
import statistics
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


class HealthStatus(Enum):
    """System health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Types of monitored components"""
    AI_AGENT = "ai_agent"
    MEMORY_KERNEL = "memory_kernel"
    INFRASTRUCTURE = "infrastructure"
    DATA_PIPELINE = "data_pipeline"
    MONITORING = "monitoring"
    LEARNING = "learning"


@dataclass
class ComponentHealth:
    """Health status for a single component"""
    component_id: str
    component_type: ComponentType
    status: HealthStatus
    last_active: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    score: float = 1.0  # 0.0 to 1.0

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['component_type'] = self.component_type.value
        data['status'] = self.status.value
        return data


@dataclass
class SystemHealthReport:
    """Complete system health report"""
    timestamp: str
    overall_status: HealthStatus
    overall_score: float
    components: List[ComponentHealth]
    anomalies: List[Dict[str, Any]]
    recommendations: List[str]
    learning_status: Dict[str, Any]

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status.value,
            "overall_score": self.overall_score,
            "components": [c.to_dict() for c in self.components],
            "anomalies": self.anomalies,
            "recommendations": self.recommendations,
            "learning_status": self.learning_status
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class SelfMonitoringHub:
    """
    Central hub for all system self-monitoring.

    Aggregates health signals from:
    - AI agents (ChatGPT, Claude, Copilot)
    - Memory kernels (Part 2)
    - Infrastructure (self-healing agent)
    - Data pipelines (alpha, risk, execution)
    - Learning systems (kernel updates, history)
    """

    def __init__(self):
        self.repo_root = REPO_ROOT
        self.state_dir = self.repo_root / "state"
        self.ai_dir = self.repo_root / "ai"
        self.history_dir = self.ai_dir / "history"
        self.kernels_dir = self.ai_dir / "memory" / "kernels"

        # Cache for performance baselines
        self._baselines: Dict[str, Any] = {}
        self._baseline_timestamp: Optional[datetime] = None

        # Health history for trend analysis
        self.health_history_file = self.state_dir / "health_history.jsonl"

    # =========================================================================
    # Core Health Monitoring
    # =========================================================================

    def get_system_health(self) -> SystemHealthReport:
        """
        Get comprehensive system health report.

        Aggregates health from all monitored components and computes
        overall system status.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Collect component health
        components = []
        components.extend(self._check_ai_agents())
        components.extend(self._check_memory_kernels())
        components.extend(self._check_infrastructure())
        components.extend(self._check_data_pipelines())
        components.extend(self._check_learning_systems())

        # Compute overall score
        overall_score = self._compute_overall_score(components)

        # Determine overall status
        overall_status = self._determine_status(overall_score, components)

        # Detect anomalies
        anomalies = self._detect_current_anomalies(components)

        # Generate recommendations
        recommendations = self._generate_recommendations(components, anomalies)

        # Learning status
        learning_status = self._get_learning_status()

        report = SystemHealthReport(
            timestamp=timestamp,
            overall_status=overall_status,
            overall_score=overall_score,
            components=components,
            anomalies=anomalies,
            recommendations=recommendations,
            learning_status=learning_status
        )

        # Log health history
        self._log_health_report(report)

        return report

    def compute_health_score(self) -> float:
        """Quick health score computation (0.0-1.0)"""
        report = self.get_system_health()
        return report.overall_score

    # =========================================================================
    # Component Health Checks
    # =========================================================================

    def _check_ai_agents(self) -> List[ComponentHealth]:
        """Check health of AI agent integrations"""
        agents = []

        # Check ChatGPT/OpenAI
        openai_health = self._check_openai_integration()
        agents.append(openai_health)

        # Check Claude
        claude_health = self._check_claude_integration()
        agents.append(claude_health)

        # Check Copilot (stub)
        copilot_health = self._check_copilot_integration()
        agents.append(copilot_health)

        # Check Nexus orchestrator
        nexus_health = self._check_nexus_health()
        agents.append(nexus_health)

        return agents

    def _check_openai_integration(self) -> ComponentHealth:
        """Check OpenAI/ChatGPT integration health"""
        issues = []
        score = 1.0
        metrics = {}

        # Check API key
        if not os.getenv("OPENAI_API_KEY"):
            issues.append("OPENAI_API_KEY not set")
            score -= 0.5

        # Check recent usage from ledger
        ledger_file = self.state_dir / "ai_task_ledger.jsonl"
        if ledger_file.exists():
            recent_tasks = self._get_recent_tasks(ledger_file, "openai", hours=24)
            metrics["tasks_24h"] = len(recent_tasks)
            metrics["cost_24h"] = sum(t.get("cost_usd", 0) for t in recent_tasks)

            # Check for errors
            errors = [t for t in recent_tasks if t.get("status") == "error"]
            if errors:
                error_rate = len(errors) / len(recent_tasks) if recent_tasks else 0
                if error_rate > 0.2:
                    issues.append(f"High error rate: {error_rate:.0%}")
                    score -= 0.3

        status = HealthStatus.HEALTHY if score > 0.7 else HealthStatus.DEGRADED if score > 0.3 else HealthStatus.CRITICAL

        return ComponentHealth(
            component_id="openai_chatgpt",
            component_type=ComponentType.AI_AGENT,
            status=status,
            last_active=self._get_last_active(ledger_file, "openai"),
            metrics=metrics,
            issues=issues,
            score=max(0, score)
        )

    def _check_claude_integration(self) -> ComponentHealth:
        """Check Claude integration health"""
        issues = []
        score = 1.0
        metrics = {}

        # Check API key
        if not os.getenv("ANTHROPIC_API_KEY"):
            issues.append("ANTHROPIC_API_KEY not set")
            score -= 0.5

        # Check recent usage
        ledger_file = self.state_dir / "ai_task_ledger.jsonl"
        if ledger_file.exists():
            recent_tasks = self._get_recent_tasks(ledger_file, "claude", hours=24)
            metrics["tasks_24h"] = len(recent_tasks)
            metrics["cost_24h"] = sum(t.get("cost_usd", 0) for t in recent_tasks)

        status = HealthStatus.HEALTHY if score > 0.7 else HealthStatus.DEGRADED if score > 0.3 else HealthStatus.CRITICAL

        return ComponentHealth(
            component_id="claude",
            component_type=ComponentType.AI_AGENT,
            status=status,
            metrics=metrics,
            issues=issues,
            score=max(0, score)
        )

    def _check_copilot_integration(self) -> ComponentHealth:
        """Check GitHub Copilot integration health (currently stub)"""
        return ComponentHealth(
            component_id="github_copilot",
            component_type=ComponentType.AI_AGENT,
            status=HealthStatus.UNKNOWN,
            metrics={"status": "stub_only"},
            issues=["GitHub Copilot integration is stub only"],
            score=0.5
        )

    def _check_nexus_health(self) -> ComponentHealth:
        """Check AI Nexus orchestrator health"""
        issues = []
        score = 1.0
        metrics = {}

        # Check task queue
        queue_file = self.state_dir / "autonomous_task_queue.json"
        if queue_file.exists():
            try:
                with open(queue_file) as f:
                    queue = json.load(f)

                current_tasks = queue.get("tasks", [])
                completed_tasks = queue.get("completed", [])

                metrics["pending_tasks"] = len(current_tasks)
                metrics["completed_tasks"] = len(completed_tasks)

                # Check for stale tasks
                for task in current_tasks:
                    created = task.get("created_at", "")
                    if created:
                        try:
                            created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                            age_hours = (datetime.now(timezone.utc) - created_dt).total_seconds() / 3600
                            if age_hours > 24:
                                issues.append(f"Stale task: {task.get('task_id', 'unknown')} ({age_hours:.0f}h old)")
                                score -= 0.1
                        except:
                            pass
            except Exception as e:
                issues.append(f"Error reading task queue: {e}")
                score -= 0.2

        status = HealthStatus.HEALTHY if score > 0.7 else HealthStatus.DEGRADED if score > 0.3 else HealthStatus.CRITICAL

        return ComponentHealth(
            component_id="ai_nexus",
            component_type=ComponentType.AI_AGENT,
            status=status,
            metrics=metrics,
            issues=issues,
            score=max(0, score)
        )

    def _check_memory_kernels(self) -> List[ComponentHealth]:
        """Check health of all memory kernels"""
        kernels = []

        if not self.kernels_dir.exists():
            return [ComponentHealth(
                component_id="memory_kernels",
                component_type=ComponentType.MEMORY_KERNEL,
                status=HealthStatus.CRITICAL,
                issues=["Kernels directory does not exist"],
                score=0.0
            )]

        for kernel_file in self.kernels_dir.glob("*.json"):
            kernel_id = kernel_file.stem
            health = self._check_single_kernel(kernel_id, kernel_file)
            kernels.append(health)

        return kernels

    def _check_single_kernel(self, kernel_id: str, kernel_file: Path) -> ComponentHealth:
        """Check health of a single memory kernel"""
        issues = []
        score = 1.0
        metrics = {}

        try:
            with open(kernel_file) as f:
                kernel = json.load(f)

            # Check last updated
            last_updated = kernel.get("last_updated", "")
            metrics["last_updated"] = last_updated

            if last_updated:
                try:
                    updated_dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                    age_days = (datetime.now(timezone.utc) - updated_dt).days
                    metrics["age_days"] = age_days

                    if age_days > 30:
                        issues.append(f"Kernel stale: {age_days} days since update")
                        score -= 0.2
                    elif age_days > 7:
                        issues.append(f"Kernel aging: {age_days} days since update")
                        score -= 0.1
                except:
                    pass

            # Check content quality
            key_decisions = len(kernel.get("key_decisions", []))
            failed_paths = len(kernel.get("failed_paths", []))
            open_questions = len(kernel.get("open_questions", []))

            metrics["key_decisions"] = key_decisions
            metrics["failed_paths"] = failed_paths
            metrics["open_questions"] = open_questions

            # Empty kernel is less healthy
            if key_decisions == 0 and failed_paths == 0:
                issues.append("Kernel has no learned decisions")
                score -= 0.3

            # Too many open questions might indicate stagnation
            if open_questions > 10:
                issues.append(f"Many unresolved questions: {open_questions}")
                score -= 0.1

        except Exception as e:
            issues.append(f"Error reading kernel: {e}")
            score = 0.2

        status = HealthStatus.HEALTHY if score > 0.7 else HealthStatus.DEGRADED if score > 0.3 else HealthStatus.CRITICAL

        return ComponentHealth(
            component_id=f"kernel_{kernel_id}",
            component_type=ComponentType.MEMORY_KERNEL,
            status=status,
            last_active=metrics.get("last_updated"),
            metrics=metrics,
            issues=issues,
            score=max(0, score)
        )

    def _check_infrastructure(self) -> List[ComponentHealth]:
        """Check infrastructure health"""
        components = []

        # Self-healing agent
        components.append(self._check_self_healing_agent())

        # Cron automation
        components.append(self._check_cron_automation())

        # Disk/storage
        components.append(self._check_storage())

        return components

    def _check_self_healing_agent(self) -> ComponentHealth:
        """Check self-healing agent status"""
        issues = []
        score = 1.0
        metrics = {}

        state_file = self.state_dir / "self_healing_state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state = json.load(f)

                metrics["total_fixes"] = state.get("total_fixes", 0)
                metrics["last_check"] = state.get("last_check")

                # Check if agent is actively running
                last_check = state.get("last_check")
                if last_check:
                    try:
                        check_dt = datetime.fromisoformat(last_check)
                        age_minutes = (datetime.now() - check_dt).total_seconds() / 60
                        metrics["minutes_since_check"] = age_minutes

                        if age_minutes > 30:
                            issues.append("Self-healing agent may not be running")
                            score -= 0.3
                    except:
                        pass

            except Exception as e:
                issues.append(f"Error reading state: {e}")
                score -= 0.2
        else:
            issues.append("Self-healing agent state not found")
            score -= 0.3

        status = HealthStatus.HEALTHY if score > 0.7 else HealthStatus.DEGRADED if score > 0.3 else HealthStatus.CRITICAL

        return ComponentHealth(
            component_id="self_healing_agent",
            component_type=ComponentType.INFRASTRUCTURE,
            status=status,
            last_active=metrics.get("last_check"),
            metrics=metrics,
            issues=issues,
            score=max(0, score)
        )

    def _check_cron_automation(self) -> ComponentHealth:
        """Check cron job automation status"""
        issues = []
        score = 1.0

        try:
            import subprocess
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                issues.append("No cron jobs configured")
                score -= 0.5
            elif "hands-off" not in result.stdout:
                issues.append("Hands-off-engine cron job missing")
                score -= 0.3
        except Exception as e:
            issues.append(f"Cannot check cron: {e}")
            score -= 0.4

        status = HealthStatus.HEALTHY if score > 0.7 else HealthStatus.DEGRADED if score > 0.3 else HealthStatus.CRITICAL

        return ComponentHealth(
            component_id="cron_automation",
            component_type=ComponentType.INFRASTRUCTURE,
            status=status,
            issues=issues,
            score=max(0, score)
        )

    def _check_storage(self) -> ComponentHealth:
        """Check storage/disk health"""
        issues = []
        score = 1.0
        metrics = {}

        try:
            import shutil
            total, used, free = shutil.disk_usage(str(self.repo_root))
            usage_pct = (used / total) * 100

            metrics["total_gb"] = total / (1024**3)
            metrics["used_gb"] = used / (1024**3)
            metrics["free_gb"] = free / (1024**3)
            metrics["usage_pct"] = usage_pct

            if usage_pct > 90:
                issues.append(f"Disk critically full: {usage_pct:.0f}%")
                score -= 0.5
            elif usage_pct > 80:
                issues.append(f"Disk usage high: {usage_pct:.0f}%")
                score -= 0.2
        except Exception as e:
            issues.append(f"Cannot check disk: {e}")
            score -= 0.3

        status = HealthStatus.HEALTHY if score > 0.7 else HealthStatus.DEGRADED if score > 0.3 else HealthStatus.CRITICAL

        return ComponentHealth(
            component_id="storage",
            component_type=ComponentType.INFRASTRUCTURE,
            status=status,
            metrics=metrics,
            issues=issues,
            score=max(0, score)
        )

    def _check_data_pipelines(self) -> List[ComponentHealth]:
        """Check data pipeline health"""
        components = []

        # Alpha signals
        components.append(self._check_alpha_pipeline())

        # Execution plan
        components.append(self._check_execution_pipeline())

        # Performance metrics
        components.append(self._check_performance_pipeline())

        return components

    def _check_alpha_pipeline(self) -> ComponentHealth:
        """Check alpha signal generation pipeline"""
        issues = []
        score = 1.0
        metrics = {}

        model_file = self.state_dir / "polymarket-model.json"
        if model_file.exists():
            try:
                with open(model_file) as f:
                    model = json.load(f)

                metrics["markets_analyzed"] = model.get("total_markets_analyzed", 0)
                metrics["markets_selected"] = model.get("markets_selected", 0)

                generated_at = model.get("generated_at", "")
                if generated_at:
                    try:
                        gen_dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                        age_hours = (datetime.now(timezone.utc) - gen_dt).total_seconds() / 3600
                        metrics["age_hours"] = age_hours

                        if age_hours > 6:
                            issues.append(f"Alpha signals stale: {age_hours:.1f}h old")
                            score -= 0.3
                        elif age_hours > 2:
                            issues.append(f"Alpha signals aging: {age_hours:.1f}h old")
                            score -= 0.1
                    except:
                        pass

            except Exception as e:
                issues.append(f"Error reading model: {e}")
                score -= 0.3
        else:
            issues.append("Alpha model file not found")
            score -= 0.5

        status = HealthStatus.HEALTHY if score > 0.7 else HealthStatus.DEGRADED if score > 0.3 else HealthStatus.CRITICAL

        return ComponentHealth(
            component_id="alpha_pipeline",
            component_type=ComponentType.DATA_PIPELINE,
            status=status,
            metrics=metrics,
            issues=issues,
            score=max(0, score)
        )

    def _check_execution_pipeline(self) -> ComponentHealth:
        """Check execution plan pipeline"""
        issues = []
        score = 1.0
        metrics = {}

        plan_file = self.repo_root / "executor" / "execution_plan.json"
        if plan_file.exists():
            try:
                with open(plan_file) as f:
                    plan = json.load(f)

                metrics["total_orders"] = plan.get("total_orders", 0)
                metrics["total_size_usd"] = plan.get("total_size_usd", 0)
                metrics["dryrun"] = plan.get("dryrun", True)

                timestamp = plan.get("timestamp", "")
                if timestamp:
                    try:
                        plan_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        age_hours = (datetime.now(timezone.utc) - plan_dt).total_seconds() / 3600
                        metrics["age_hours"] = age_hours

                        if age_hours > 4:
                            issues.append(f"Execution plan stale: {age_hours:.1f}h old")
                            score -= 0.3
                    except:
                        pass

            except Exception as e:
                issues.append(f"Error reading plan: {e}")
                score -= 0.3
        else:
            issues.append("Execution plan file not found")
            score -= 0.4

        status = HealthStatus.HEALTHY if score > 0.7 else HealthStatus.DEGRADED if score > 0.3 else HealthStatus.CRITICAL

        return ComponentHealth(
            component_id="execution_pipeline",
            component_type=ComponentType.DATA_PIPELINE,
            status=status,
            metrics=metrics,
            issues=issues,
            score=max(0, score)
        )

    def _check_performance_pipeline(self) -> ComponentHealth:
        """Check performance metrics pipeline"""
        issues = []
        score = 1.0
        metrics = {}

        metrics_file = self.state_dir / "performance_metrics.jsonl"
        if metrics_file.exists():
            try:
                # Count recent entries
                recent_count = 0
                latest_timestamp = None

                with open(metrics_file) as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            ts = entry.get("timestamp", "")
                            if ts:
                                entry_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                                if (datetime.now(timezone.utc) - entry_dt).total_seconds() < 86400:
                                    recent_count += 1
                                if latest_timestamp is None or ts > latest_timestamp:
                                    latest_timestamp = ts
                        except:
                            continue

                metrics["entries_24h"] = recent_count
                metrics["latest_entry"] = latest_timestamp

                if recent_count < 12:  # Expecting hourly
                    issues.append(f"Low metric collection rate: {recent_count}/24h")
                    score -= 0.2

            except Exception as e:
                issues.append(f"Error reading metrics: {e}")
                score -= 0.2
        else:
            issues.append("Performance metrics file not found")
            score -= 0.3

        status = HealthStatus.HEALTHY if score > 0.7 else HealthStatus.DEGRADED if score > 0.3 else HealthStatus.CRITICAL

        return ComponentHealth(
            component_id="performance_pipeline",
            component_type=ComponentType.DATA_PIPELINE,
            status=status,
            metrics=metrics,
            issues=issues,
            score=max(0, score)
        )

    def _check_learning_systems(self) -> List[ComponentHealth]:
        """Check learning/improvement systems health"""
        components = []

        # History logging
        components.append(self._check_history_logging())

        # Kernel update system
        components.append(self._check_kernel_updates())

        # Feedback loop
        components.append(self._check_feedback_loop())

        return components

    def _check_history_logging(self) -> ComponentHealth:
        """Check history event logging health"""
        issues = []
        score = 1.0
        metrics = {}

        events_file = self.history_dir / "events.jsonl"
        legacy_file = self.history_dir / "user_events.jsonl"

        event_count = 0
        latest_event = None

        for events_path in [events_file, legacy_file]:
            if events_path.exists():
                try:
                    with open(events_path) as f:
                        for line in f:
                            try:
                                event = json.loads(line)
                                event_count += 1
                                ts = event.get("ts") or event.get("timestamp", "")
                                if ts and (latest_event is None or ts > latest_event):
                                    latest_event = ts
                            except:
                                continue
                except:
                    pass

        metrics["total_events"] = event_count
        metrics["latest_event"] = latest_event

        if event_count == 0:
            issues.append("No history events recorded")
            score -= 0.4

        if latest_event:
            try:
                event_dt = datetime.fromisoformat(latest_event.replace("Z", "+00:00"))
                age_days = (datetime.now(timezone.utc) - event_dt).days
                metrics["days_since_event"] = age_days

                if age_days > 7:
                    issues.append(f"No recent events: {age_days} days")
                    score -= 0.3
            except:
                pass

        status = HealthStatus.HEALTHY if score > 0.7 else HealthStatus.DEGRADED if score > 0.3 else HealthStatus.CRITICAL

        return ComponentHealth(
            component_id="history_logging",
            component_type=ComponentType.LEARNING,
            status=status,
            metrics=metrics,
            issues=issues,
            score=max(0, score)
        )

    def _check_kernel_updates(self) -> ComponentHealth:
        """Check kernel update system health"""
        issues = []
        score = 1.0
        metrics = {}

        # Check intercom threads for CPU sessions
        intercom_dir = self.ai_dir / "intercom"
        if intercom_dir.exists():
            sessions = list(intercom_dir.glob("*/thread.jsonl"))
            metrics["cpu_sessions"] = len(sessions)

            recent_sessions = 0
            for session_path in sessions:
                try:
                    stat = session_path.stat()
                    if (time.time() - stat.st_mtime) < 86400 * 7:  # 7 days
                        recent_sessions += 1
                except:
                    pass

            metrics["recent_sessions_7d"] = recent_sessions

            if recent_sessions == 0:
                issues.append("No CPU sessions in last 7 days")
                score -= 0.2
        else:
            issues.append("No CPU intercom directory")
            score -= 0.3

        # Check if auto-apply is working (it's currently manual)
        issues.append("Kernel updates require manual application (gap)")
        score -= 0.15  # Known gap

        status = HealthStatus.HEALTHY if score > 0.7 else HealthStatus.DEGRADED if score > 0.3 else HealthStatus.CRITICAL

        return ComponentHealth(
            component_id="kernel_updates",
            component_type=ComponentType.LEARNING,
            status=status,
            metrics=metrics,
            issues=issues,
            score=max(0, score)
        )

    def _check_feedback_loop(self) -> ComponentHealth:
        """Check feedback loop closure health"""
        issues = []
        score = 1.0
        metrics = {}

        # Check if performance metrics are being analyzed
        # Currently: they're collected but not fed back to kernels
        issues.append("Performance metrics not auto-feeding to kernels (gap)")
        score -= 0.2

        # Check if anomaly detection exists
        issues.append("No predictive anomaly detection (gap)")
        score -= 0.2

        # Check decision attribution
        issues.append("No performance-to-decision attribution (gap)")
        score -= 0.15

        status = HealthStatus.DEGRADED  # Known gaps

        return ComponentHealth(
            component_id="feedback_loop",
            component_type=ComponentType.LEARNING,
            status=status,
            metrics=metrics,
            issues=issues,
            score=max(0, score)
        )

    # =========================================================================
    # Scoring & Analysis
    # =========================================================================

    def _compute_overall_score(self, components: List[ComponentHealth]) -> float:
        """Compute weighted overall health score"""
        if not components:
            return 0.0

        # Weight by component type
        weights = {
            ComponentType.AI_AGENT: 1.0,
            ComponentType.MEMORY_KERNEL: 0.8,
            ComponentType.INFRASTRUCTURE: 1.2,
            ComponentType.DATA_PIPELINE: 1.0,
            ComponentType.MONITORING: 0.9,
            ComponentType.LEARNING: 0.9
        }

        total_weight = 0
        weighted_sum = 0

        for comp in components:
            weight = weights.get(comp.component_type, 1.0)
            weighted_sum += comp.score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _determine_status(self, score: float, components: List[ComponentHealth]) -> HealthStatus:
        """Determine overall system status"""
        # Check for any critical components
        critical_count = sum(1 for c in components if c.status == HealthStatus.CRITICAL)
        if critical_count > 0:
            return HealthStatus.CRITICAL

        # Score-based determination
        if score >= 0.8:
            return HealthStatus.HEALTHY
        elif score >= 0.5:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.CRITICAL

    def _detect_current_anomalies(self, components: List[ComponentHealth]) -> List[Dict[str, Any]]:
        """Detect anomalies in current component states"""
        anomalies = []

        for comp in components:
            # Check for score degradation
            if comp.score < 0.5:
                anomalies.append({
                    "type": "low_score",
                    "component": comp.component_id,
                    "score": comp.score,
                    "issues": comp.issues,
                    "severity": "high" if comp.score < 0.3 else "medium"
                })

            # Check specific patterns
            if comp.component_type == ComponentType.DATA_PIPELINE:
                age = comp.metrics.get("age_hours", 0)
                if age > 4:
                    anomalies.append({
                        "type": "stale_data",
                        "component": comp.component_id,
                        "age_hours": age,
                        "severity": "medium"
                    })

        return anomalies

    def _generate_recommendations(
        self,
        components: List[ComponentHealth],
        anomalies: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # API key recommendations
        for comp in components:
            if any("API_KEY not set" in issue for issue in comp.issues):
                recommendations.append(f"Set missing API key for {comp.component_id}")

        # Stale data recommendations
        stale_pipelines = [c for c in components
                          if c.component_type == ComponentType.DATA_PIPELINE
                          and c.metrics.get("age_hours", 0) > 2]
        if stale_pipelines:
            recommendations.append("Run pipeline refresh to update stale data")

        # Learning system recommendations
        learning_issues = [c for c in components
                         if c.component_type == ComponentType.LEARNING
                         and c.score < 0.7]
        if learning_issues:
            recommendations.append("Review and run kernel refresh to update learning systems")

        # Known gaps
        recommendations.append("Implement automatic kernel update application (known gap)")
        recommendations.append("Add predictive anomaly detection (known gap)")
        recommendations.append("Implement performance-to-decision attribution (known gap)")

        return recommendations

    def _get_learning_status(self) -> Dict[str, Any]:
        """Get current learning system status"""
        status = {
            "kernels_active": 0,
            "recent_updates": 0,
            "feedback_loops_closed": 0,
            "gaps_identified": [
                "Kernel updates not auto-applied",
                "Performance metrics not feeding kernels",
                "No anomaly detection",
                "No decision attribution"
            ]
        }

        # Count active kernels
        if self.kernels_dir.exists():
            status["kernels_active"] = len(list(self.kernels_dir.glob("*.json")))

        return status

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _get_recent_tasks(
        self,
        ledger_file: Path,
        provider: str,
        hours: int = 24
    ) -> List[Dict]:
        """Get recent tasks for a provider"""
        if not ledger_file.exists():
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        tasks = []

        try:
            with open(ledger_file) as f:
                for line in f:
                    try:
                        task = json.loads(line)
                        if task.get("provider", "").lower() == provider.lower():
                            ts = task.get("timestamp", "")
                            if ts:
                                task_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                                if task_dt >= cutoff:
                                    tasks.append(task)
                    except:
                        continue
        except:
            pass

        return tasks

    def _get_last_active(self, ledger_file: Path, provider: str) -> Optional[str]:
        """Get last active timestamp for a provider"""
        tasks = self._get_recent_tasks(ledger_file, provider, hours=168)  # 7 days
        if tasks:
            timestamps = [t.get("timestamp", "") for t in tasks if t.get("timestamp")]
            if timestamps:
                return max(timestamps)
        return None

    def _log_health_report(self, report: SystemHealthReport):
        """Log health report to history file"""
        try:
            self.health_history_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.health_history_file, "a") as f:
                f.write(json.dumps({
                    "timestamp": report.timestamp,
                    "overall_score": report.overall_score,
                    "overall_status": report.overall_status.value,
                    "anomaly_count": len(report.anomalies),
                    "component_scores": {c.component_id: c.score for c in report.components}
                }) + "\n")
        except:
            pass  # Best effort


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Self-Monitoring Hub - System Health Aggregator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get full system health status
  python -m ai_nexus.self_monitoring_hub status

  # Get health score (0.0-1.0)
  python -m ai_nexus.self_monitoring_hub health-score

  # Check for anomalies
  python -m ai_nexus.self_monitoring_hub anomalies

  # Get JSON output
  python -m ai_nexus.self_monitoring_hub status --json
        """
    )

    parser.add_argument(
        "command",
        choices=["status", "health-score", "anomalies", "recommendations"],
        help="Command to run"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    hub = SelfMonitoringHub()

    if args.command == "status":
        report = hub.get_system_health()

        if args.json:
            print(report.to_json())
        else:
            print("\n" + "="*70)
            print("🔍 SELF-MONITORING HUB - SYSTEM HEALTH REPORT")
            print("="*70)
            print(f"\n⏰ Timestamp: {report.timestamp}")
            print(f"📊 Overall Score: {report.overall_score:.1%}")
            print(f"🚦 Status: {report.overall_status.value.upper()}")

            print("\n📦 COMPONENTS:")
            print("-"*50)

            # Group by type
            by_type: Dict[ComponentType, List[ComponentHealth]] = {}
            for comp in report.components:
                if comp.component_type not in by_type:
                    by_type[comp.component_type] = []
                by_type[comp.component_type].append(comp)

            status_emoji = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.DEGRADED: "⚠️",
                HealthStatus.CRITICAL: "🔴",
                HealthStatus.UNKNOWN: "❓"
            }

            for comp_type, comps in by_type.items():
                print(f"\n  {comp_type.value.upper()}:")
                for comp in comps:
                    emoji = status_emoji.get(comp.status, "❓")
                    print(f"    {emoji} {comp.component_id}: {comp.score:.0%}")
                    for issue in comp.issues[:2]:  # Show first 2 issues
                        print(f"       └─ {issue}")

            if report.anomalies:
                print(f"\n⚠️ ANOMALIES ({len(report.anomalies)}):")
                print("-"*50)
                for anomaly in report.anomalies[:5]:
                    print(f"  • [{anomaly['severity']}] {anomaly['type']}: {anomaly['component']}")

            print(f"\n💡 RECOMMENDATIONS ({len(report.recommendations)}):")
            print("-"*50)
            for rec in report.recommendations[:5]:
                print(f"  • {rec}")

            print("\n" + "="*70)

    elif args.command == "health-score":
        score = hub.compute_health_score()
        if args.json:
            print(json.dumps({"health_score": score}))
        else:
            print(f"Health Score: {score:.1%}")

    elif args.command == "anomalies":
        report = hub.get_system_health()
        if args.json:
            print(json.dumps({"anomalies": report.anomalies}))
        else:
            if report.anomalies:
                print(f"\n⚠️ {len(report.anomalies)} Anomalies Detected:")
                for anomaly in report.anomalies:
                    print(f"  [{anomaly['severity']}] {anomaly['type']}: {anomaly['component']}")
            else:
                print("✅ No anomalies detected")

    elif args.command == "recommendations":
        report = hub.get_system_health()
        if args.json:
            print(json.dumps({"recommendations": report.recommendations}))
        else:
            print(f"\n💡 Recommendations ({len(report.recommendations)}):")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"  {i}. {rec}")


if __name__ == "__main__":
    main()
