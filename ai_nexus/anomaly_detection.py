"""
Anomaly Detection Engine v1.0

Statistical anomaly detection for the CLM AI Nexus system.
Addresses the critical gap: NO PREDICTIVE ANOMALY DETECTION.

Features:
- Time-series anomaly detection using statistical methods
- Z-score based outlier detection
- Moving average deviation detection
- Pattern change detection
- Multi-metric correlation analysis
- Alert generation with severity levels

Methods:
- Z-Score: Detect values outside N standard deviations
- IQR: Interquartile range for robust outlier detection
- Moving Average Deviation: Detect trend changes
- Baseline Drift: Detect gradual degradation

API:
    detector = AnomalyDetector()
    anomalies = detector.detect_all()
    report = detector.generate_report()

CLI:
    python -m ai_nexus.anomaly_detection detect
    python -m ai_nexus.anomaly_detection report
    python -m ai_nexus.anomaly_detection train-baseline
"""

import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


class AnomalySeverity(Enum):
    """Severity levels for detected anomalies"""
    INFO = "info"           # Notable but not concerning
    WARNING = "warning"     # Needs attention
    CRITICAL = "critical"   # Requires immediate action


class AnomalyType(Enum):
    """Types of anomalies that can be detected"""
    ZSCORE_OUTLIER = "zscore_outlier"
    IQR_OUTLIER = "iqr_outlier"
    TREND_CHANGE = "trend_change"
    BASELINE_DRIFT = "baseline_drift"
    MISSING_DATA = "missing_data"
    SUDDEN_DROP = "sudden_drop"
    SUDDEN_SPIKE = "sudden_spike"
    PATTERN_BREAK = "pattern_break"


@dataclass
class Anomaly:
    """Represents a detected anomaly"""
    anomaly_id: str
    timestamp: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    metric_name: str
    current_value: float
    expected_value: float
    deviation: float  # How far from expected (in std devs or percentage)
    description: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['anomaly_type'] = self.anomaly_type.value
        data['severity'] = self.severity.value
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class MetricBaseline:
    """Statistical baseline for a metric"""
    metric_name: str
    mean: float
    std: float
    min: float
    max: float
    median: float
    q1: float  # 25th percentile
    q3: float  # 75th percentile
    sample_count: int
    last_updated: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AnomalyReport:
    """Complete anomaly detection report"""
    timestamp: str
    anomalies: List[Anomaly]
    metrics_analyzed: int
    total_data_points: int
    baselines_used: Dict[str, MetricBaseline]
    recommendations: List[str]

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "metrics_analyzed": self.metrics_analyzed,
            "total_data_points": self.total_data_points,
            "baselines_used": {k: v.to_dict() for k, v in self.baselines_used.items()},
            "recommendations": self.recommendations,
            "summary": {
                "total_anomalies": len(self.anomalies),
                "critical": sum(1 for a in self.anomalies if a.severity == AnomalySeverity.CRITICAL),
                "warning": sum(1 for a in self.anomalies if a.severity == AnomalySeverity.WARNING),
                "info": sum(1 for a in self.anomalies if a.severity == AnomalySeverity.INFO)
            }
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class AnomalyDetector:
    """
    Statistical anomaly detection engine.

    Analyzes:
    - Performance metrics (orders, sizes, edges, confidence)
    - System health metrics (freshness, availability)
    - Learning metrics (kernel updates, history events)
    - AI agent metrics (cost, errors, latency)
    """

    # Detection thresholds
    ZSCORE_WARNING = 2.0   # 2 standard deviations
    ZSCORE_CRITICAL = 3.0  # 3 standard deviations
    IQR_MULTIPLIER = 1.5   # Standard IQR multiplier
    TREND_CHANGE_THRESHOLD = 0.3  # 30% change
    BASELINE_DRIFT_THRESHOLD = 0.2  # 20% drift

    def __init__(self):
        self.repo_root = REPO_ROOT
        self.state_dir = self.repo_root / "state"
        self.baselines_file = self.state_dir / "anomaly_baselines.json"
        self.anomaly_log = self.state_dir / "detected_anomalies.jsonl"

        # Load or initialize baselines
        self.baselines: Dict[str, MetricBaseline] = self._load_baselines()

        # Anomaly counter for unique IDs
        self._anomaly_counter = 0

    # =========================================================================
    # Core Detection Methods
    # =========================================================================

    def detect_all(self) -> List[Anomaly]:
        """
        Run all anomaly detection checks.

        Returns list of detected anomalies sorted by severity.
        """
        anomalies = []

        # Detect anomalies in performance metrics
        anomalies.extend(self._detect_performance_anomalies())

        # Detect anomalies in system health
        anomalies.extend(self._detect_health_anomalies())

        # Detect anomalies in learning metrics
        anomalies.extend(self._detect_learning_anomalies())

        # Detect anomalies in AI agent costs
        anomalies.extend(self._detect_cost_anomalies())

        # Sort by severity (critical first)
        severity_order = {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.WARNING: 1,
            AnomalySeverity.INFO: 2
        }
        anomalies.sort(key=lambda a: severity_order.get(a.severity, 99))

        # Log anomalies
        self._log_anomalies(anomalies)

        return anomalies

    def generate_report(self) -> AnomalyReport:
        """Generate complete anomaly detection report"""
        anomalies = self.detect_all()

        # Count metrics and data points
        metrics_analyzed = len(self.baselines)
        total_data_points = sum(b.sample_count for b in self.baselines.values())

        # Generate recommendations
        recommendations = self._generate_recommendations(anomalies)

        return AnomalyReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            anomalies=anomalies,
            metrics_analyzed=metrics_analyzed,
            total_data_points=total_data_points,
            baselines_used=self.baselines.copy(),
            recommendations=recommendations
        )

    # =========================================================================
    # Statistical Detection Methods
    # =========================================================================

    def detect_zscore_anomaly(
        self,
        metric_name: str,
        current_value: float,
        baseline: Optional[MetricBaseline] = None
    ) -> Optional[Anomaly]:
        """
        Detect anomaly using Z-score method.

        Z-score = (x - mean) / std_dev
        """
        if baseline is None:
            baseline = self.baselines.get(metric_name)

        if baseline is None or baseline.std == 0:
            return None

        zscore = abs(current_value - baseline.mean) / baseline.std

        if zscore >= self.ZSCORE_CRITICAL:
            severity = AnomalySeverity.CRITICAL
        elif zscore >= self.ZSCORE_WARNING:
            severity = AnomalySeverity.WARNING
        else:
            return None  # Not anomalous

        direction = "above" if current_value > baseline.mean else "below"

        return self._create_anomaly(
            anomaly_type=AnomalyType.ZSCORE_OUTLIER,
            severity=severity,
            metric_name=metric_name,
            current_value=current_value,
            expected_value=baseline.mean,
            deviation=zscore,
            description=f"{metric_name} is {zscore:.1f} std devs {direction} mean "
                       f"({current_value:.2f} vs {baseline.mean:.2f})",
            context={"zscore": zscore, "direction": direction}
        )

    def detect_iqr_anomaly(
        self,
        metric_name: str,
        current_value: float,
        baseline: Optional[MetricBaseline] = None
    ) -> Optional[Anomaly]:
        """
        Detect anomaly using Interquartile Range (IQR) method.

        More robust to extreme outliers than Z-score.
        Anomaly if value < Q1 - 1.5*IQR or value > Q3 + 1.5*IQR
        """
        if baseline is None:
            baseline = self.baselines.get(metric_name)

        if baseline is None:
            return None

        iqr = baseline.q3 - baseline.q1
        lower_bound = baseline.q1 - self.IQR_MULTIPLIER * iqr
        upper_bound = baseline.q3 + self.IQR_MULTIPLIER * iqr

        if current_value < lower_bound or current_value > upper_bound:
            severity = AnomalySeverity.WARNING

            # Extreme outliers are critical
            extreme_lower = baseline.q1 - 3 * iqr
            extreme_upper = baseline.q3 + 3 * iqr
            if current_value < extreme_lower or current_value > extreme_upper:
                severity = AnomalySeverity.CRITICAL

            direction = "below" if current_value < lower_bound else "above"
            deviation = (current_value - baseline.median) / iqr if iqr > 0 else 0

            return self._create_anomaly(
                anomaly_type=AnomalyType.IQR_OUTLIER,
                severity=severity,
                metric_name=metric_name,
                current_value=current_value,
                expected_value=baseline.median,
                deviation=deviation,
                description=f"{metric_name} is {direction} IQR bounds "
                           f"({current_value:.2f} vs [{lower_bound:.2f}, {upper_bound:.2f}])",
                context={"iqr": iqr, "bounds": [lower_bound, upper_bound]}
            )

        return None

    def detect_trend_change(
        self,
        metric_name: str,
        values: List[Tuple[str, float]],
        window_size: int = 5
    ) -> Optional[Anomaly]:
        """
        Detect sudden trend changes using moving average comparison.

        Compares recent window average to previous window average.
        """
        if len(values) < window_size * 2:
            return None

        # Sort by timestamp and extract values
        sorted_values = sorted(values, key=lambda x: x[0])
        recent_values = [v[1] for v in sorted_values[-window_size:]]
        previous_values = [v[1] for v in sorted_values[-(window_size*2):-window_size]]

        recent_avg = sum(recent_values) / len(recent_values)
        previous_avg = sum(previous_values) / len(previous_values)

        if previous_avg == 0:
            return None

        change_pct = (recent_avg - previous_avg) / abs(previous_avg)

        if abs(change_pct) >= self.TREND_CHANGE_THRESHOLD:
            severity = AnomalySeverity.CRITICAL if abs(change_pct) > 0.5 else AnomalySeverity.WARNING
            direction = "increased" if change_pct > 0 else "decreased"

            return self._create_anomaly(
                anomaly_type=AnomalyType.TREND_CHANGE,
                severity=severity,
                metric_name=metric_name,
                current_value=recent_avg,
                expected_value=previous_avg,
                deviation=change_pct,
                description=f"{metric_name} {direction} by {abs(change_pct):.0%} "
                           f"({previous_avg:.2f} -> {recent_avg:.2f})",
                context={"change_pct": change_pct, "window_size": window_size}
            )

        return None

    def detect_baseline_drift(
        self,
        metric_name: str,
        recent_mean: float
    ) -> Optional[Anomaly]:
        """
        Detect gradual baseline drift.

        When recent average has drifted significantly from historical baseline.
        """
        baseline = self.baselines.get(metric_name)
        if baseline is None or baseline.mean == 0:
            return None

        drift_pct = (recent_mean - baseline.mean) / abs(baseline.mean)

        if abs(drift_pct) >= self.BASELINE_DRIFT_THRESHOLD:
            severity = AnomalySeverity.WARNING
            direction = "increased" if drift_pct > 0 else "decreased"

            return self._create_anomaly(
                anomaly_type=AnomalyType.BASELINE_DRIFT,
                severity=severity,
                metric_name=metric_name,
                current_value=recent_mean,
                expected_value=baseline.mean,
                deviation=drift_pct,
                description=f"{metric_name} baseline has {direction} by {abs(drift_pct):.0%} "
                           f"(was {baseline.mean:.2f}, now {recent_mean:.2f})",
                context={"drift_pct": drift_pct, "baseline_age": baseline.last_updated}
            )

        return None

    def detect_sudden_change(
        self,
        metric_name: str,
        current_value: float,
        previous_value: float,
        threshold: float = 0.5
    ) -> Optional[Anomaly]:
        """Detect sudden spike or drop between consecutive values"""
        if previous_value == 0:
            return None

        change_pct = (current_value - previous_value) / abs(previous_value)

        if abs(change_pct) >= threshold:
            anomaly_type = AnomalyType.SUDDEN_SPIKE if change_pct > 0 else AnomalyType.SUDDEN_DROP
            severity = AnomalySeverity.CRITICAL if abs(change_pct) > 1.0 else AnomalySeverity.WARNING

            return self._create_anomaly(
                anomaly_type=anomaly_type,
                severity=severity,
                metric_name=metric_name,
                current_value=current_value,
                expected_value=previous_value,
                deviation=change_pct,
                description=f"{metric_name} {'spiked' if change_pct > 0 else 'dropped'} "
                           f"by {abs(change_pct):.0%} ({previous_value:.2f} -> {current_value:.2f})",
                context={"change_pct": change_pct}
            )

        return None

    # =========================================================================
    # Domain-Specific Detection
    # =========================================================================

    def _detect_performance_anomalies(self) -> List[Anomaly]:
        """Detect anomalies in performance metrics"""
        anomalies = []
        metrics_file = self.state_dir / "performance_metrics.jsonl"

        if not metrics_file.exists():
            return anomalies

        # Load recent metrics
        recent_metrics = self._load_recent_metrics(metrics_file, hours=24)
        if not recent_metrics:
            return anomalies

        # Extract time series for key metrics
        metrics_to_check = [
            ("execution_plan.total_orders", "orders"),
            ("execution_plan.total_size_usd", "size_usd"),
            ("execution_plan.avg_confidence", "confidence"),
            ("alpha_signals.avg_edge", "edge"),
            ("alpha_signals.selection_rate", "selection_rate")
        ]

        for metric_path, metric_name in metrics_to_check:
            values = self._extract_metric_series(recent_metrics, metric_path)

            if values:
                current_value = values[-1][1]

                # Z-score check
                baseline = self.baselines.get(metric_name)
                if baseline:
                    anomaly = self.detect_zscore_anomaly(metric_name, current_value, baseline)
                    if anomaly:
                        anomalies.append(anomaly)

                # Trend change check
                if len(values) >= 10:
                    anomaly = self.detect_trend_change(metric_name, values)
                    if anomaly:
                        anomalies.append(anomaly)

                # Sudden change check
                if len(values) >= 2:
                    anomaly = self.detect_sudden_change(
                        metric_name,
                        values[-1][1],
                        values[-2][1]
                    )
                    if anomaly:
                        anomalies.append(anomaly)

        return anomalies

    def _detect_health_anomalies(self) -> List[Anomaly]:
        """Detect anomalies in system health metrics"""
        anomalies = []
        health_file = self.state_dir / "health_history.jsonl"

        if not health_file.exists():
            return anomalies

        # Load recent health reports
        recent_health = []
        try:
            with open(health_file) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        recent_health.append(entry)
                    except:
                        continue
        except:
            return anomalies

        if not recent_health:
            return anomalies

        # Check health score trend
        scores = [(h.get("timestamp", ""), h.get("overall_score", 0)) for h in recent_health]
        if scores:
            current_score = scores[-1][1]

            # Sudden health drop
            if len(scores) >= 2:
                anomaly = self.detect_sudden_change(
                    "health_score",
                    current_score,
                    scores[-2][1],
                    threshold=0.2
                )
                if anomaly:
                    anomalies.append(anomaly)

            # Health trend change
            if len(scores) >= 10:
                anomaly = self.detect_trend_change("health_score", scores)
                if anomaly:
                    anomalies.append(anomaly)

        return anomalies

    def _detect_learning_anomalies(self) -> List[Anomaly]:
        """Detect anomalies in learning system metrics"""
        anomalies = []

        # Check history event frequency
        history_dir = self.repo_root / "ai" / "history"
        events_file = history_dir / "events.jsonl"

        if events_file.exists():
            # Count events per day
            events_per_day = defaultdict(int)
            try:
                with open(events_file) as f:
                    for line in f:
                        try:
                            event = json.loads(line)
                            ts = event.get("ts", "")[:10]  # Get date part
                            if ts:
                                events_per_day[ts] += 1
                        except:
                            continue
            except:
                pass

            if events_per_day:
                counts = list(events_per_day.values())
                if len(counts) >= 3:
                    recent_count = counts[-1]
                    avg_count = sum(counts[:-1]) / len(counts[:-1])

                    if avg_count > 0:
                        change = (recent_count - avg_count) / avg_count
                        if abs(change) > 0.5:
                            severity = AnomalySeverity.WARNING
                            direction = "increased" if change > 0 else "decreased"

                            anomalies.append(self._create_anomaly(
                                anomaly_type=AnomalyType.PATTERN_BREAK,
                                severity=severity,
                                metric_name="history_events_daily",
                                current_value=recent_count,
                                expected_value=avg_count,
                                deviation=change,
                                description=f"Daily history events {direction} by {abs(change):.0%}",
                                context={"recent": recent_count, "average": avg_count}
                            ))

        return anomalies

    def _detect_cost_anomalies(self) -> List[Anomaly]:
        """Detect anomalies in AI agent costs"""
        anomalies = []
        ledger_file = self.state_dir / "ai_task_ledger.jsonl"

        if not ledger_file.exists():
            return anomalies

        # Load costs by day
        costs_by_day = defaultdict(float)
        try:
            with open(ledger_file) as f:
                for line in f:
                    try:
                        task = json.loads(line)
                        ts = task.get("timestamp", "")[:10]
                        cost = task.get("cost_usd", 0)
                        if ts and cost:
                            costs_by_day[ts] += cost
                    except:
                        continue
        except:
            return anomalies

        if len(costs_by_day) >= 3:
            costs = list(costs_by_day.values())
            recent_cost = costs[-1]
            avg_cost = sum(costs[:-1]) / len(costs[:-1])

            # Check for cost spike
            if avg_cost > 0:
                change = (recent_cost - avg_cost) / avg_cost
                if change > 0.5:  # 50% increase
                    anomalies.append(self._create_anomaly(
                        anomaly_type=AnomalyType.SUDDEN_SPIKE,
                        severity=AnomalySeverity.WARNING if change < 1 else AnomalySeverity.CRITICAL,
                        metric_name="daily_ai_cost",
                        current_value=recent_cost,
                        expected_value=avg_cost,
                        deviation=change,
                        description=f"Daily AI cost spiked by {change:.0%} "
                                   f"(${avg_cost:.2f} -> ${recent_cost:.2f})",
                        context={"change_pct": change}
                    ))

        return anomalies

    # =========================================================================
    # Baseline Management
    # =========================================================================

    def train_baselines(self, hours: int = 168) -> Dict[str, MetricBaseline]:
        """
        Train statistical baselines from historical data.

        Args:
            hours: Hours of historical data to use (default: 168 = 7 days)
        """
        metrics_file = self.state_dir / "performance_metrics.jsonl"

        if not metrics_file.exists():
            print("No performance metrics file found for training")
            return {}

        recent_metrics = self._load_recent_metrics(metrics_file, hours=hours)

        if not recent_metrics:
            print("No recent metrics found for training")
            return {}

        # Metrics to build baselines for
        metric_paths = [
            ("execution_plan.total_orders", "orders"),
            ("execution_plan.total_size_usd", "size_usd"),
            ("execution_plan.avg_confidence", "confidence"),
            ("alpha_signals.avg_edge", "edge"),
            ("alpha_signals.selection_rate", "selection_rate")
        ]

        baselines = {}

        for metric_path, metric_name in metric_paths:
            values = self._extract_metric_series(recent_metrics, metric_path)

            if values and len(values) >= 5:
                numeric_values = [v[1] for v in values]
                baseline = self._compute_baseline(metric_name, numeric_values)
                baselines[metric_name] = baseline

        self.baselines = baselines
        self._save_baselines()

        return baselines

    def _compute_baseline(self, metric_name: str, values: List[float]) -> MetricBaseline:
        """Compute statistical baseline from values"""
        sorted_vals = sorted(values)
        n = len(sorted_vals)

        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std = math.sqrt(variance)

        median = sorted_vals[n // 2] if n % 2 else (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[(3 * n) // 4]

        return MetricBaseline(
            metric_name=metric_name,
            mean=mean,
            std=std,
            min=min(values),
            max=max(values),
            median=median,
            q1=q1,
            q3=q3,
            sample_count=n,
            last_updated=datetime.now(timezone.utc).isoformat()
        )

    def _load_baselines(self) -> Dict[str, MetricBaseline]:
        """Load baselines from file"""
        if not self.baselines_file.exists():
            return {}

        try:
            with open(self.baselines_file) as f:
                data = json.load(f)

            return {
                name: MetricBaseline(**baseline_data)
                for name, baseline_data in data.items()
            }
        except Exception as e:
            print(f"Error loading baselines: {e}")
            return {}

    def _save_baselines(self):
        """Save baselines to file"""
        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)

            data = {name: baseline.to_dict() for name, baseline in self.baselines.items()}

            with open(self.baselines_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving baselines: {e}")

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _create_anomaly(
        self,
        anomaly_type: AnomalyType,
        severity: AnomalySeverity,
        metric_name: str,
        current_value: float,
        expected_value: float,
        deviation: float,
        description: str,
        context: Dict[str, Any]
    ) -> Anomaly:
        """Create a new Anomaly with unique ID"""
        self._anomaly_counter += 1

        return Anomaly(
            anomaly_id=f"anomaly_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._anomaly_counter}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            anomaly_type=anomaly_type,
            severity=severity,
            metric_name=metric_name,
            current_value=current_value,
            expected_value=expected_value,
            deviation=deviation,
            description=description,
            context=context
        )

    def _load_recent_metrics(self, metrics_file: Path, hours: int) -> List[Dict]:
        """Load metrics from the last N hours"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent = []

        try:
            with open(metrics_file) as f:
                for line in f:
                    try:
                        metric = json.loads(line)
                        ts = metric.get("timestamp", "")
                        if ts:
                            metric_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            if metric_dt >= cutoff:
                                recent.append(metric)
                    except:
                        continue
        except:
            pass

        return recent

    def _extract_metric_series(
        self,
        metrics: List[Dict],
        metric_path: str
    ) -> List[Tuple[str, float]]:
        """Extract a time series from metrics by path (e.g., 'execution_plan.total_orders')"""
        series = []

        for metric in metrics:
            ts = metric.get("timestamp", "")
            value = metric

            # Navigate the path
            for key in metric_path.split("."):
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    value = None
                    break

            if ts and value is not None:
                try:
                    series.append((ts, float(value)))
                except:
                    pass

        return series

    def _log_anomalies(self, anomalies: List[Anomaly]):
        """Log anomalies to file"""
        if not anomalies:
            return

        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)

            with open(self.anomaly_log, 'a') as f:
                for anomaly in anomalies:
                    f.write(anomaly.to_json().replace('\n', ' ') + '\n')
        except:
            pass

    def _generate_recommendations(self, anomalies: List[Anomaly]) -> List[str]:
        """Generate recommendations based on detected anomalies"""
        recommendations = []

        # Group by type
        by_type = defaultdict(list)
        for a in anomalies:
            by_type[a.anomaly_type].append(a)

        # Generate type-specific recommendations
        if AnomalyType.SUDDEN_DROP in by_type:
            recommendations.append(
                "Investigate sudden drops in metrics - may indicate system failure or data issue"
            )

        if AnomalyType.SUDDEN_SPIKE in by_type:
            recommendations.append(
                "Review sudden spikes - may indicate unusual activity or cost overrun"
            )

        if AnomalyType.TREND_CHANGE in by_type:
            recommendations.append(
                "Trend changes detected - review recent configuration or market changes"
            )

        if AnomalyType.BASELINE_DRIFT in by_type:
            recommendations.append(
                "Baseline drift detected - consider retraining baselines if drift is expected"
            )

        # Severity-based recommendations
        critical_count = sum(1 for a in anomalies if a.severity == AnomalySeverity.CRITICAL)
        if critical_count > 0:
            recommendations.insert(0, f"URGENT: {critical_count} critical anomalies require immediate attention")

        return recommendations


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Anomaly Detection Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run anomaly detection
  python -m ai_nexus.anomaly_detection detect

  # Generate full report
  python -m ai_nexus.anomaly_detection report

  # Train baselines from last 7 days
  python -m ai_nexus.anomaly_detection train-baseline

  # JSON output
  python -m ai_nexus.anomaly_detection report --json
        """
    )

    parser.add_argument(
        "command",
        choices=["detect", "report", "train-baseline", "show-baselines"],
        help="Command to run"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    parser.add_argument(
        "--hours",
        type=int,
        default=168,
        help="Hours of data for baseline training (default: 168)"
    )

    args = parser.parse_args()

    detector = AnomalyDetector()

    if args.command == "detect":
        anomalies = detector.detect_all()

        if args.json:
            print(json.dumps([a.to_dict() for a in anomalies], indent=2))
        else:
            if not anomalies:
                print("✅ No anomalies detected")
            else:
                print(f"\n⚠️ {len(anomalies)} Anomalies Detected:")
                print("="*60)

                severity_emoji = {
                    AnomalySeverity.CRITICAL: "🔴",
                    AnomalySeverity.WARNING: "🟠",
                    AnomalySeverity.INFO: "🔵"
                }

                for anomaly in anomalies:
                    emoji = severity_emoji.get(anomaly.severity, "❓")
                    print(f"\n{emoji} [{anomaly.severity.value.upper()}] {anomaly.metric_name}")
                    print(f"   {anomaly.description}")
                    print(f"   Type: {anomaly.anomaly_type.value}")
                    print(f"   Deviation: {anomaly.deviation:.2f}")

    elif args.command == "report":
        report = detector.generate_report()

        if args.json:
            print(report.to_json())
        else:
            print("\n" + "="*70)
            print("🔍 ANOMALY DETECTION REPORT")
            print("="*70)
            print(f"\n⏰ Timestamp: {report.timestamp}")
            print(f"📊 Metrics Analyzed: {report.metrics_analyzed}")
            print(f"📈 Data Points: {report.total_data_points}")

            summary = report.to_dict()["summary"]
            print(f"\n📋 Summary:")
            print(f"   Total Anomalies: {summary['total_anomalies']}")
            print(f"   🔴 Critical: {summary['critical']}")
            print(f"   🟠 Warning: {summary['warning']}")
            print(f"   🔵 Info: {summary['info']}")

            if report.anomalies:
                print(f"\n⚠️ Anomalies:")
                print("-"*50)
                for anomaly in report.anomalies[:10]:
                    print(f"  • [{anomaly.severity.value}] {anomaly.description}")

            if report.recommendations:
                print(f"\n💡 Recommendations:")
                print("-"*50)
                for rec in report.recommendations:
                    print(f"  • {rec}")

            print("\n" + "="*70)

    elif args.command == "train-baseline":
        print(f"Training baselines from last {args.hours} hours of data...")
        baselines = detector.train_baselines(hours=args.hours)

        if args.json:
            print(json.dumps({name: b.to_dict() for name, b in baselines.items()}, indent=2))
        else:
            print(f"\n✅ Trained {len(baselines)} baselines:")
            for name, baseline in baselines.items():
                print(f"\n  {name}:")
                print(f"    Mean: {baseline.mean:.4f}")
                print(f"    Std:  {baseline.std:.4f}")
                print(f"    Range: [{baseline.min:.4f}, {baseline.max:.4f}]")
                print(f"    Samples: {baseline.sample_count}")

    elif args.command == "show-baselines":
        if args.json:
            print(json.dumps({name: b.to_dict() for name, b in detector.baselines.items()}, indent=2))
        else:
            if not detector.baselines:
                print("No baselines found. Run 'train-baseline' first.")
            else:
                print(f"\n📊 Current Baselines ({len(detector.baselines)}):")
                print("="*50)
                for name, baseline in detector.baselines.items():
                    print(f"\n  {name}:")
                    print(f"    Mean: {baseline.mean:.4f} ± {baseline.std:.4f}")
                    print(f"    IQR: [{baseline.q1:.4f}, {baseline.q3:.4f}]")
                    print(f"    Updated: {baseline.last_updated}")


if __name__ == "__main__":
    main()
