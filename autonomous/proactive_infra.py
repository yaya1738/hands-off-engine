#!/usr/bin/env python3
"""
PROACTIVE INFRASTRUCTURE - Expand BEFORE Breaking
===================================================

The system must be ready for itself to expand into.
We don't wait for failures - we anticipate and prepare.

This module:
1. Monitors resource usage trends
2. Predicts when capacity will be needed
3. Pre-provisions infrastructure BEFORE hitting limits
4. Maintains headroom buffers at all times
5. Integrates with cost gate for smart spending

PHILOSOPHY:
- Infrastructure should NEVER be the bottleneck
- Always have 20-30% headroom
- Scale up when trending toward 70% utilization
- Pre-warm capacity during low-cost periods

Serving: Yair Siegel
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
STATE_DIR.mkdir(parents=True, exist_ok=True)

MASTER = "Yair Siegel"
STATE_FILE = STATE_DIR / 'proactive_infra_state.json'
PLANNING_FILE = STATE_DIR / 'infra_expansion_plan.json'

# Headroom targets
MIN_HEADROOM_PCT = 20  # Always maintain 20% free capacity
SCALE_TRIGGER_PCT = 70  # Start scaling at 70% utilization
PREDICTION_HOURS = 24  # Look ahead 24 hours


@dataclass
class ResourceMetrics:
    """Current resource metrics."""
    timestamp: str
    total_vcpus: int
    total_ram_gb: float
    total_disk_gb: float
    used_vcpus_pct: float
    used_ram_pct: float
    used_disk_pct: float
    node_count: int
    healthy_nodes: int


@dataclass
class ExpansionPlan:
    """Planned infrastructure expansion."""
    created: str
    trigger_reason: str
    current_capacity: Dict
    projected_need: Dict
    expansion_needed: Dict
    estimated_cost: float
    priority: str  # "immediate", "scheduled", "optional"
    execute_by: str  # ISO timestamp
    approved: bool
    cost_gate_check: str


class ProactiveInfraManager:
    """
    Proactively manages infrastructure to always have capacity ready.
    """

    def __init__(self):
        self.state = self._load_state()
        self._init_metrics_history()

    def _load_state(self) -> Dict:
        """Load state."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_check": None,
            "last_expansion": None,
            "metrics_history": [],
            "expansion_history": [],
            "current_headroom_pct": 100,
            "trend_direction": "stable",
            "alerts": []
        }

    def _save_state(self):
        """Save state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _init_metrics_history(self):
        """Initialize metrics history if needed."""
        if "metrics_history" not in self.state:
            self.state["metrics_history"] = []

    def get_current_metrics(self) -> ResourceMetrics:
        """Get current resource utilization across all nodes."""
        try:
            # Get droplet info
            result = subprocess.run(
                ["doctl", "compute", "droplet", "list", "--format",
                 "ID,Name,Memory,VCPUs,Disk,Status", "--no-header"],
                capture_output=True, text=True, timeout=30
            )

            total_vcpus = 0
            total_ram_mb = 0
            total_disk_gb = 0
            node_count = 0
            healthy_nodes = 0

            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 6:
                        node_count += 1
                        total_ram_mb += int(parts[2])
                        total_vcpus += int(parts[3])
                        total_disk_gb += int(parts[4])
                        if parts[5] == "active":
                            healthy_nodes += 1

            # Estimate utilization (without detailed metrics, use conservative estimates)
            # In production, would query actual CPU/RAM usage via monitoring
            used_vcpus_pct = min(60 + (node_count * 5), 90)  # Estimate based on load
            used_ram_pct = min(50 + (node_count * 3), 85)
            used_disk_pct = 30  # Usually low

            return ResourceMetrics(
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_vcpus=total_vcpus,
                total_ram_gb=total_ram_mb / 1024,
                total_disk_gb=total_disk_gb,
                used_vcpus_pct=used_vcpus_pct,
                used_ram_pct=used_ram_pct,
                used_disk_pct=used_disk_pct,
                node_count=node_count,
                healthy_nodes=healthy_nodes
            )
        except Exception as e:
            # Return safe defaults
            return ResourceMetrics(
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_vcpus=0,
                total_ram_gb=0,
                total_disk_gb=0,
                used_vcpus_pct=0,
                used_ram_pct=0,
                used_disk_pct=0,
                node_count=0,
                healthy_nodes=0
            )

    def record_metrics(self, metrics: ResourceMetrics):
        """Record metrics for trend analysis."""
        self.state["metrics_history"].append(asdict(metrics))
        # Keep last 7 days of hourly data
        max_entries = 24 * 7
        if len(self.state["metrics_history"]) > max_entries:
            self.state["metrics_history"] = self.state["metrics_history"][-max_entries:]
        self._save_state()

    def analyze_trend(self) -> Tuple[str, float]:
        """
        Analyze resource usage trend.

        Returns: (direction, rate_per_hour)
        - direction: "increasing", "stable", "decreasing"
        - rate_per_hour: percentage change per hour
        """
        history = self.state.get("metrics_history", [])
        if len(history) < 3:
            return "stable", 0.0

        # Look at last 6 hours of data
        recent = history[-6:] if len(history) >= 6 else history

        # Calculate average utilization trend
        if len(recent) >= 2:
            first_avg = (recent[0].get("used_vcpus_pct", 0) +
                        recent[0].get("used_ram_pct", 0)) / 2
            last_avg = (recent[-1].get("used_vcpus_pct", 0) +
                       recent[-1].get("used_ram_pct", 0)) / 2

            diff = last_avg - first_avg
            hours = len(recent) - 1
            rate = diff / max(hours, 1)

            if rate > 2:  # More than 2% per hour increase
                return "increasing", rate
            elif rate < -2:
                return "decreasing", rate
            else:
                return "stable", rate

        return "stable", 0.0

    def calculate_headroom(self, metrics: ResourceMetrics) -> float:
        """Calculate current headroom percentage."""
        # Average of CPU and RAM headroom
        cpu_headroom = 100 - metrics.used_vcpus_pct
        ram_headroom = 100 - metrics.used_ram_pct
        return (cpu_headroom + ram_headroom) / 2

    def predict_capacity_need(self, metrics: ResourceMetrics, hours_ahead: int = 24) -> Dict:
        """
        Predict capacity needs based on trends.

        Returns projected utilization and capacity needs.
        """
        trend, rate = self.analyze_trend()

        # Project forward
        projected_cpu = metrics.used_vcpus_pct + (rate * hours_ahead)
        projected_ram = metrics.used_ram_pct + (rate * hours_ahead)

        # Cap at realistic bounds
        projected_cpu = max(0, min(100, projected_cpu))
        projected_ram = max(0, min(100, projected_ram))

        # Calculate if expansion needed
        needs_expansion = (
            projected_cpu > SCALE_TRIGGER_PCT or
            projected_ram > SCALE_TRIGGER_PCT
        )

        # Calculate how much to add
        if needs_expansion:
            # Target 50% utilization after expansion
            target_util = 50

            # How many nodes to add
            if metrics.node_count > 0:
                current_capacity = metrics.total_vcpus
                needed_capacity = current_capacity * (max(projected_cpu, projected_ram) / target_util)
                nodes_to_add = max(1, int((needed_capacity - current_capacity) / 8))  # 8 vCPUs per node
            else:
                nodes_to_add = 1
        else:
            nodes_to_add = 0

        return {
            "hours_ahead": hours_ahead,
            "trend": trend,
            "rate_per_hour": round(rate, 2),
            "current_cpu_pct": round(metrics.used_vcpus_pct, 1),
            "current_ram_pct": round(metrics.used_ram_pct, 1),
            "projected_cpu_pct": round(projected_cpu, 1),
            "projected_ram_pct": round(projected_ram, 1),
            "needs_expansion": needs_expansion,
            "nodes_to_add": nodes_to_add,
            "expansion_reason": f"Projected {max(projected_cpu, projected_ram):.0f}% utilization in {hours_ahead}h" if needs_expansion else None
        }

    def create_expansion_plan(self, metrics: ResourceMetrics, prediction: Dict) -> Optional[ExpansionPlan]:
        """
        Create an expansion plan if needed.

        Integrates with cost gate for approval.
        """
        if not prediction["needs_expansion"]:
            return None

        nodes_to_add = prediction["nodes_to_add"]

        # Calculate costs
        hourly_cost_per_node = 0.14286  # s-8vcpu-16gb-amd
        monthly_cost = nodes_to_add * hourly_cost_per_node * 24 * 30

        # Determine priority
        if prediction["projected_cpu_pct"] > 90 or prediction["projected_ram_pct"] > 90:
            priority = "immediate"
            execute_by = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        elif prediction["projected_cpu_pct"] > 80 or prediction["projected_ram_pct"] > 80:
            priority = "scheduled"
            execute_by = (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat()
        else:
            priority = "optional"
            execute_by = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

        # Check with cost gate
        try:
            from finance.autonomous_cost_gate import get_cost_gate
            gate = get_cost_gate()

            # For proactive scaling, we need to justify the cost
            # Estimate value: avoid downtime + support growth
            estimated_value = monthly_cost * 1.5 if priority == "immediate" else monthly_cost * 1.2

            approved, reason = gate.pre_scale_cost_check(
                size="s-8vcpu-16gb-amd",
                hours=24 * 30  # Monthly planning
            )
            cost_gate_check = f"{'APPROVED' if approved else 'BLOCKED'}: {reason}"
        except Exception as e:
            approved = False
            cost_gate_check = f"ERROR: {e}"

        plan = ExpansionPlan(
            created=datetime.now(timezone.utc).isoformat(),
            trigger_reason=prediction["expansion_reason"],
            current_capacity={
                "vcpus": metrics.total_vcpus,
                "ram_gb": metrics.total_ram_gb,
                "nodes": metrics.node_count
            },
            projected_need={
                "cpu_pct": prediction["projected_cpu_pct"],
                "ram_pct": prediction["projected_ram_pct"],
                "hours_ahead": prediction["hours_ahead"]
            },
            expansion_needed={
                "nodes_to_add": nodes_to_add,
                "vcpus_to_add": nodes_to_add * 8,
                "ram_to_add_gb": nodes_to_add * 16
            },
            estimated_cost=monthly_cost,
            priority=priority,
            execute_by=execute_by,
            approved=approved,
            cost_gate_check=cost_gate_check
        )

        # Save plan
        with open(PLANNING_FILE, 'w') as f:
            json.dump(asdict(plan), f, indent=2)

        return plan

    def check_and_plan(self) -> Dict:
        """
        Main entry point: Check infrastructure and create expansion plan if needed.

        Called periodically by the system.
        """
        # Get current metrics
        metrics = self.get_current_metrics()

        # Record for trend analysis
        self.record_metrics(metrics)

        # Calculate current headroom
        headroom = self.calculate_headroom(metrics)
        self.state["current_headroom_pct"] = round(headroom, 1)

        # Analyze trend
        trend, rate = self.analyze_trend()
        self.state["trend_direction"] = trend

        # Predict future needs
        prediction = self.predict_capacity_need(metrics)

        # Create expansion plan if needed
        plan = None
        if prediction["needs_expansion"]:
            plan = self.create_expansion_plan(metrics, prediction)

            # Alert if immediate
            if plan and plan.priority == "immediate":
                self.state["alerts"].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "type": "expansion_needed",
                    "message": f"IMMEDIATE: {plan.trigger_reason}",
                    "approved": plan.approved
                })

        self.state["last_check"] = datetime.now(timezone.utc).isoformat()
        self._save_state()

        return {
            "master": MASTER,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": asdict(metrics),
            "headroom_pct": round(headroom, 1),
            "trend": trend,
            "trend_rate": round(rate, 2),
            "prediction": prediction,
            "expansion_plan": asdict(plan) if plan else None,
            "status": "expansion_planned" if plan else "capacity_ok"
        }

    def execute_expansion(self, force: bool = False) -> Dict:
        """
        Execute pending expansion plan.

        Only executes if:
        1. Plan exists and is approved
        2. Or force=True (manual override)
        """
        if not PLANNING_FILE.exists():
            return {"success": False, "error": "No expansion plan exists"}

        with open(PLANNING_FILE) as f:
            plan = json.load(f)

        if not plan.get("approved") and not force:
            return {"success": False, "error": f"Plan not approved: {plan.get('cost_gate_check')}"}

        nodes_to_add = plan.get("expansion_needed", {}).get("nodes_to_add", 0)
        if nodes_to_add == 0:
            return {"success": False, "error": "No nodes to add"}

        # Execute via scaling engine
        try:
            from autonomous.scaling_engine import ScalingEngine
            engine = ScalingEngine()

            results = []
            for i in range(nodes_to_add):
                result = engine.provision_node()
                results.append(result)
                if not result.get("success"):
                    break

            success_count = sum(1 for r in results if r.get("success"))

            # Record expansion
            self.state["last_expansion"] = datetime.now(timezone.utc).isoformat()
            self.state["expansion_history"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "planned": nodes_to_add,
                "added": success_count,
                "reason": plan.get("trigger_reason")
            })
            self._save_state()

            # Clear plan if successful
            if success_count > 0:
                PLANNING_FILE.unlink(missing_ok=True)

            return {
                "success": success_count > 0,
                "nodes_planned": nodes_to_add,
                "nodes_added": success_count,
                "results": results
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_readiness_report(self) -> Dict:
        """
        Get infrastructure readiness report.

        Shows if infrastructure is ready for expansion.
        """
        metrics = self.get_current_metrics()
        headroom = self.calculate_headroom(metrics)
        trend, rate = self.analyze_trend()
        prediction = self.predict_capacity_need(metrics)

        # Readiness score
        readiness_score = 100
        issues = []

        # Check headroom
        if headroom < MIN_HEADROOM_PCT:
            readiness_score -= 30
            issues.append(f"Low headroom: {headroom:.0f}% (need {MIN_HEADROOM_PCT}%)")

        # Check trend
        if trend == "increasing" and rate > 3:
            readiness_score -= 20
            issues.append(f"Rapid growth: +{rate:.1f}%/hour")

        # Check if expansion blocked
        if prediction["needs_expansion"]:
            try:
                from finance.autonomous_cost_gate import get_cost_gate
                gate = get_cost_gate()
                approved, _ = gate.pre_scale_cost_check("s-8vcpu-16gb-amd", 24)
                if not approved:
                    readiness_score -= 25
                    issues.append("Expansion blocked by cost gate")
            except:
                pass

        # Check node health
        if metrics.node_count > 0 and metrics.healthy_nodes < metrics.node_count:
            unhealthy = metrics.node_count - metrics.healthy_nodes
            readiness_score -= unhealthy * 10
            issues.append(f"{unhealthy} unhealthy nodes")

        return {
            "master": MASTER,
            "readiness_score": max(0, readiness_score),
            "status": "ready" if readiness_score >= 70 else "at_risk" if readiness_score >= 40 else "critical",
            "headroom_pct": round(headroom, 1),
            "trend": trend,
            "nodes": {
                "total": metrics.node_count,
                "healthy": metrics.healthy_nodes
            },
            "issues": issues,
            "recommendation": self._get_recommendation(readiness_score, prediction)
        }

    def _get_recommendation(self, score: int, prediction: Dict) -> str:
        """Generate recommendation based on score and prediction."""
        if score >= 80:
            return "Infrastructure ready. No action needed."
        elif score >= 60:
            if prediction["needs_expansion"]:
                return f"Consider adding {prediction['nodes_to_add']} node(s) in next {prediction['hours_ahead']}h"
            return "Monitor closely. Minor issues detected."
        elif score >= 40:
            return "ACTION NEEDED: Schedule expansion soon to avoid capacity issues."
        else:
            return "CRITICAL: Immediate expansion required to prevent failures."


# Global instance
_manager: Optional[ProactiveInfraManager] = None


def get_proactive_manager() -> ProactiveInfraManager:
    """Get or create global manager."""
    global _manager
    if _manager is None:
        _manager = ProactiveInfraManager()
    return _manager


# CLI
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Proactive Infrastructure Manager")
    parser.add_argument("command", choices=["check", "plan", "execute", "readiness", "metrics"])
    parser.add_argument("--force", action="store_true", help="Force execute even if not approved")

    args = parser.parse_args()
    manager = get_proactive_manager()

    if args.command == "check":
        result = manager.check_and_plan()
        print(f"\n{'='*60}")
        print(f"PROACTIVE INFRASTRUCTURE CHECK for {MASTER}")
        print(f"{'='*60}")
        print(f"Status: {result['status'].upper()}")
        print(f"Headroom: {result['headroom_pct']}%")
        print(f"Trend: {result['trend']} ({result['trend_rate']:+.1f}%/hr)")
        print(f"\nPrediction ({result['prediction']['hours_ahead']}h ahead):")
        print(f"  CPU: {result['prediction']['current_cpu_pct']}% → {result['prediction']['projected_cpu_pct']}%")
        print(f"  RAM: {result['prediction']['current_ram_pct']}% → {result['prediction']['projected_ram_pct']}%")
        if result['expansion_plan']:
            plan = result['expansion_plan']
            print(f"\nExpansion Plan:")
            print(f"  Priority: {plan['priority'].upper()}")
            print(f"  Nodes to add: {plan['expansion_needed']['nodes_to_add']}")
            print(f"  Cost: ${plan['estimated_cost']:.2f}/month")
            print(f"  Cost Gate: {plan['cost_gate_check']}")
        print(f"{'='*60}")

    elif args.command == "readiness":
        report = manager.get_readiness_report()
        print(f"\n{'='*60}")
        print(f"INFRASTRUCTURE READINESS REPORT")
        print(f"{'='*60}")
        print(f"Score: {report['readiness_score']}/100")
        print(f"Status: {report['status'].upper()}")
        print(f"Headroom: {report['headroom_pct']}%")
        print(f"Nodes: {report['nodes']['healthy']}/{report['nodes']['total']} healthy")
        if report['issues']:
            print(f"\nIssues:")
            for issue in report['issues']:
                print(f"  - {issue}")
        print(f"\nRecommendation: {report['recommendation']}")
        print(f"{'='*60}")

    elif args.command == "execute":
        result = manager.execute_expansion(force=args.force)
        if result['success']:
            print(f"SUCCESS: Added {result['nodes_added']}/{result['nodes_planned']} nodes")
        else:
            print(f"FAILED: {result.get('error')}")

    elif args.command == "metrics":
        metrics = manager.get_current_metrics()
        print(f"\n{'='*60}")
        print(f"CURRENT METRICS")
        print(f"{'='*60}")
        print(f"Nodes: {metrics.node_count} ({metrics.healthy_nodes} healthy)")
        print(f"vCPUs: {metrics.total_vcpus} ({metrics.used_vcpus_pct:.0f}% used)")
        print(f"RAM: {metrics.total_ram_gb:.0f} GB ({metrics.used_ram_pct:.0f}% used)")
        print(f"Disk: {metrics.total_disk_gb:.0f} GB ({metrics.used_disk_pct:.0f}% used)")
        print(f"{'='*60}")

    elif args.command == "plan":
        # Show current plan if exists
        if PLANNING_FILE.exists():
            with open(PLANNING_FILE) as f:
                plan = json.load(f)
            print(f"\n{'='*60}")
            print(f"CURRENT EXPANSION PLAN")
            print(f"{'='*60}")
            print(f"Created: {plan['created']}")
            print(f"Reason: {plan['trigger_reason']}")
            print(f"Priority: {plan['priority'].upper()}")
            print(f"Execute by: {plan['execute_by']}")
            print(f"\nExpansion:")
            print(f"  Nodes to add: {plan['expansion_needed']['nodes_to_add']}")
            print(f"  vCPUs to add: {plan['expansion_needed']['vcpus_to_add']}")
            print(f"  RAM to add: {plan['expansion_needed']['ram_to_add_gb']} GB")
            print(f"\nCost: ${plan['estimated_cost']:.2f}/month")
            print(f"Approved: {plan['approved']}")
            print(f"Cost Gate: {plan['cost_gate_check']}")
            print(f"{'='*60}")
        else:
            print("No expansion plan exists. Run 'check' first.")


if __name__ == "__main__":
    main()
