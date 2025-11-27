"""
AI System Monitor - Unified monitoring for all AI agents and AI Nexus

This module provides comprehensive monitoring of:
- All AI agents (Copilot, ChatGPT, Claude, etc.)
- AI Nexus task submissions and costs
- Coordination system health
- Business-aligned metrics and health checks

Integrates with the AI Nexus for centralized oversight of the multi-agent system.
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from audit import get_audit_logger
    audit = get_audit_logger(component="ai_system_monitor")
except ImportError:
    audit = None


class HealthStatus(Enum):
    """System health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class AgentStatus:
    """Status of a single AI agent"""
    agent_id: str
    agent_type: str  # llm, coordination, self-healing
    status: HealthStatus
    last_active: Optional[str] = None
    tasks_completed_24h: int = 0
    cost_24h: float = 0.0
    error_count_24h: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        d = asdict(self)
        d['status'] = self.status.value
        return d


@dataclass
class SystemHealthReport:
    """Comprehensive system health report"""
    timestamp: str
    overall_status: HealthStatus
    agents: List[AgentStatus]
    nexus_status: Dict[str, Any]
    coordination_status: Dict[str, Any]
    business_metrics: Dict[str, Any]
    warnings: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status.value,
            "agents": [a.to_dict() for a in self.agents],
            "nexus_status": self.nexus_status,
            "coordination_status": self.coordination_status,
            "business_metrics": self.business_metrics,
            "warnings": self.warnings,
            "recommendations": self.recommendations
        }


class AISystemMonitor:
    """
    Unified monitoring system for all AI agents and AI Nexus.
    
    Provides:
    - Real-time agent health monitoring
    - AI Nexus task and cost tracking
    - Coordination system health checks
    - Business-aligned metrics
    - Proactive recommendations
    """
    
    def __init__(self, repo_root: Optional[str] = None):
        """
        Initialize the AI System Monitor.
        
        Args:
            repo_root: Root directory of the repository
        """
        if repo_root is None:
            self.repo_root = Path(__file__).parent.parent
        else:
            self.repo_root = Path(repo_root)
        
        # Key paths
        self.coordination_dir = self.repo_root / "ai" / "coordination"
        self.agents_registry = self.repo_root / "ai" / "agents" / "AGENTS_REGISTRY_v0.1.json"
        self.nexus_state_dir = self.repo_root / "logs" / "ai_nexus"
        self.ledger_dir = self.repo_root / "logs" / "ledger"
        self.state_dir = self.repo_root / "state"
        
        # Load agents registry
        self.agents_config = self._load_agents_registry()
        
        # Audit initialization
        if audit:
            audit.log_action(
                action_type="system_monitor_initialized",
                action_data={
                    "repo_root": str(self.repo_root),
                    "agents_count": len(self.agents_config.get("agents", []))
                },
                result="success"
            )
    
    def _load_agents_registry(self) -> Dict[str, Any]:
        """Load agents registry configuration"""
        if self.agents_registry.exists():
            with open(self.agents_registry) as f:
                return json.load(f)
        return {"agents": [], "version": "unknown"}
    
    def _load_coordination_status(self) -> Dict[str, Any]:
        """Load coordination system status"""
        status_file = self.coordination_dir / "status.json"
        if status_file.exists():
            with open(status_file) as f:
                return json.load(f)
        return {}
    
    def _load_coordination_messages(self, limit: int = 50) -> List[Dict]:
        """Load recent coordination messages"""
        messages_file = self.coordination_dir / "messages.jsonl"
        messages = []
        
        if messages_file.exists():
            with open(messages_file) as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    if line.strip():
                        try:
                            messages.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        
        return messages
    
    def _load_nexus_state(self) -> Dict[str, Any]:
        """Load AI Nexus state"""
        state_file = self.nexus_state_dir / "nexus_state.json"
        if state_file.exists():
            with open(state_file) as f:
                return json.load(f)
        return {"daily_costs": {}}
    
    def _load_ledger_entries_24h(self) -> List[Dict]:
        """Load ledger entries from the last 24 hours"""
        entries = []
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        
        for date_str in [today, yesterday]:
            ledger_file = self.ledger_dir / f"ledger_{date_str}.jsonl"
            if ledger_file.exists():
                with open(ledger_file) as f:
                    for line in f:
                        if line.strip():
                            try:
                                entries.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
        
        return entries
    
    def check_agent_health(self, agent_config: Dict) -> AgentStatus:
        """
        Check health of a specific AI agent.
        
        Args:
            agent_config: Agent configuration from registry
            
        Returns:
            AgentStatus with health information
        """
        agent_id = agent_config.get("id", "unknown")
        agent_kind = agent_config.get("kind", "unknown")
        
        # Default status
        status = HealthStatus.UNKNOWN
        last_active = None
        tasks_completed = 0
        cost_24h = 0.0
        error_count = 0
        metadata = {}
        
        # Check coordination messages for activity
        messages = self._load_coordination_messages()
        agent_messages = [m for m in messages if m.get("from") == agent_id]
        
        if agent_messages:
            last_message = agent_messages[-1]
            last_active = last_message.get("timestamp")
            tasks_completed = len(agent_messages)
            status = HealthStatus.HEALTHY
        
        # Check nexus state for costs
        nexus_state = self._load_nexus_state()
        cost_24h = nexus_state.get("daily_costs", {}).get(agent_id, 0.0)
        
        # Check coordination status for agent state
        coord_status = self._load_coordination_status()
        autonomous_mode = coord_status.get("autonomous_mode", {})
        
        if autonomous_mode.get(agent_id, False):
            metadata["autonomous_mode"] = True
            if status == HealthStatus.UNKNOWN:
                status = HealthStatus.HEALTHY
        
        # Check pending tasks
        pending_tasks = coord_status.get("pending_tasks", [])
        agent_tasks = [t for t in pending_tasks if t.get("assigned_to") == agent_id]
        metadata["pending_tasks"] = len(agent_tasks)
        
        # Determine health based on activity
        if last_active:
            try:
                last_dt = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                hours_since_active = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
                
                if hours_since_active > 24:
                    status = HealthStatus.WARNING
                    metadata["hours_inactive"] = round(hours_since_active, 1)
            except (ValueError, TypeError):
                pass
        
        return AgentStatus(
            agent_id=agent_id,
            agent_type=agent_kind,
            status=status,
            last_active=last_active,
            tasks_completed_24h=tasks_completed,
            cost_24h=cost_24h,
            error_count_24h=error_count,
            metadata=metadata
        )
    
    def check_nexus_health(self) -> Dict[str, Any]:
        """
        Check AI Nexus system health.
        
        Returns:
            Dictionary with nexus health information
        """
        nexus_state = self._load_nexus_state()
        
        # Calculate total costs
        daily_costs = nexus_state.get("daily_costs", {})
        total_cost = sum(daily_costs.values())
        
        # Check budget utilization
        budget_limits = {
            "copilot": 100.0,
            "chatgpt": 50.0,
            "claude": 50.0,
            "openai": 50.0,
        }
        
        budget_status = {}
        warnings = []
        
        for provider, limit in budget_limits.items():
            used = daily_costs.get(provider, 0)
            utilization = (used / limit * 100) if limit > 0 else 0
            budget_status[provider] = {
                "limit": limit,
                "used": used,
                "remaining": limit - used,
                "utilization": round(utilization, 1)
            }
            
            if utilization > 80:
                warnings.append(f"{provider} budget at {utilization:.0f}% utilization")
        
        # Load ledger for task counts
        ledger_entries = self._load_ledger_entries_24h()
        ai_tasks = [e for e in ledger_entries if e.get("entry_type") == "ai_task"]
        
        return {
            "status": "healthy" if not warnings else "warning",
            "total_cost_24h": total_cost,
            "tasks_24h": len(ai_tasks),
            "budget_status": budget_status,
            "warnings": warnings,
            "last_updated": nexus_state.get("last_updated")
        }
    
    def check_coordination_health(self) -> Dict[str, Any]:
        """
        Check coordination system health.
        
        Returns:
            Dictionary with coordination health information
        """
        coord_status = self._load_coordination_status()
        messages = self._load_coordination_messages()
        
        # Calculate message activity
        recent_messages = [
            m for m in messages
            if self._is_within_hours(m.get("timestamp"), 24)
        ]
        
        # Check for stale handoffs
        handoffs_file = self.coordination_dir / "handoffs.json"
        pending_handoffs = 0
        stale_handoffs = 0
        
        if handoffs_file.exists():
            with open(handoffs_file) as f:
                handoffs = json.load(f)
                for handoff in handoffs.get("handoffs", []):
                    if handoff.get("status") == "pending":
                        pending_handoffs += 1
                        if self._is_stale(handoff.get("created_at"), hours=48):
                            stale_handoffs += 1
        
        # Determine health
        warnings = []
        if stale_handoffs > 0:
            warnings.append(f"{stale_handoffs} stale handoffs (>48h)")
        if len(recent_messages) == 0:
            warnings.append("No agent coordination messages in last 24h")
        
        return {
            "status": "healthy" if not warnings else "warning",
            "messages_24h": len(recent_messages),
            "pending_handoffs": pending_handoffs,
            "stale_handoffs": stale_handoffs,
            "active_agents": coord_status.get("active_agents", []),
            "current_phase": coord_status.get("current_phase"),
            "autonomous_mode": coord_status.get("autonomous_mode", {}),
            "warnings": warnings
        }
    
    def _calculate_roi(self, total_profit: float, total_cost: float) -> float:
        """
        Calculate Return on Investment (ROI) as a percentage.
        
        Formula: ROI = ((Profit - Cost) / Cost) * 100
        
        This measures the net return per dollar spent on AI operations.
        - Positive ROI: AI operations are generating more value than cost
        - Zero ROI: Break-even
        - Negative ROI: AI operations cost more than they generate
        
        Args:
            total_profit: Total trading profit from AI-assisted decisions
            total_cost: Total cost of AI operations (API calls, etc.)
            
        Returns:
            ROI as percentage (e.g., 150.0 means 150% return)
        """
        if total_cost <= 0:
            return 0.0
        return ((total_profit - total_cost) / total_cost) * 100
    
    def _is_within_hours(self, timestamp: Optional[str], hours: int) -> bool:
        """Check if timestamp is within given hours from now"""
        if not timestamp:
            return False
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            delta = datetime.now(timezone.utc) - dt
            return delta.total_seconds() < hours * 3600
        except (ValueError, TypeError):
            return False
    
    def _is_stale(self, timestamp: Optional[str], hours: int) -> bool:
        """Check if timestamp is older than given hours"""
        if not timestamp:
            return True
        return not self._is_within_hours(timestamp, hours)
    
    def calculate_business_metrics(self) -> Dict[str, Any]:
        """
        Calculate business-aligned metrics.
        
        Returns:
            Dictionary with business metrics
        """
        ledger_entries = self._load_ledger_entries_24h()
        
        # Calculate costs and revenues
        total_ai_cost = sum(
            e.get("cost", 0) for e in ledger_entries
            if e.get("entry_type") == "ai_task"
        )
        
        total_trade_revenue = sum(
            e.get("revenue", 0) for e in ledger_entries
            if e.get("entry_type") == "trade"
        )
        
        total_trade_profit = sum(
            e.get("profit", 0) for e in ledger_entries
            if e.get("entry_type") == "trade"
        )
        
        # Calculate ROI (Return on Investment)
        # Formula: ROI = ((Net Profit - AI Cost) / AI Cost) * 100
        # This measures how much return we get for every dollar spent on AI operations
        # A positive ROI means the system is generating more value than its AI costs
        roi = self._calculate_roi(total_trade_profit, total_ai_cost)
        
        # Check state files for trading status
        model_file = self.state_dir / "polymarket-model.json"
        model_age_hours = None
        markets_analyzed = 0
        
        if model_file.exists():
            with open(model_file) as f:
                model = json.load(f)
                gen_at = model.get("generated_at")
                if gen_at:
                    try:
                        dt = datetime.fromisoformat(gen_at.replace('Z', '+00:00'))
                        model_age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                    except (ValueError, TypeError):
                        pass
                markets_analyzed = model.get("total_markets_analyzed", 0)
        
        return {
            "ai_cost_24h": round(total_ai_cost, 2),
            "trade_revenue_24h": round(total_trade_revenue, 2),
            "trade_profit_24h": round(total_trade_profit, 2),
            "net_profit_24h": round(total_trade_profit - total_ai_cost, 2),
            "roi_24h": round(roi, 1),
            "model_age_hours": round(model_age_hours, 1) if model_age_hours else None,
            "markets_analyzed": markets_analyzed,
            "self_financing": total_trade_profit > total_ai_cost
        }
    
    def generate_recommendations(
        self,
        agents: List[AgentStatus],
        nexus_status: Dict,
        coord_status: Dict,
        business_metrics: Dict
    ) -> List[str]:
        """
        Generate actionable recommendations based on system state.
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Check for inactive agents
        inactive_agents = [
            a for a in agents
            if a.status in [HealthStatus.WARNING, HealthStatus.UNKNOWN]
        ]
        if inactive_agents:
            agent_names = [a.agent_id for a in inactive_agents]
            recommendations.append(
                f"Investigate inactive agents: {', '.join(agent_names)}"
            )
        
        # Check budget warnings
        budget_warnings = nexus_status.get("warnings", [])
        for warning in budget_warnings:
            recommendations.append(f"Budget alert: {warning}")
        
        # Check coordination warnings
        coord_warnings = coord_status.get("warnings", [])
        for warning in coord_warnings:
            recommendations.append(f"Coordination: {warning}")
        
        # Business recommendations
        if business_metrics.get("model_age_hours", 0) and business_metrics["model_age_hours"] > 6:
            recommendations.append(
                f"Alpha model is {business_metrics['model_age_hours']:.1f}h old - consider refresh"
            )
        
        if business_metrics.get("roi_24h", 0) < 0:
            recommendations.append(
                "ROI is negative - review AI task efficiency"
            )
        
        if not business_metrics.get("self_financing", False) and business_metrics.get("ai_cost_24h", 0) > 0:
            recommendations.append(
                "System not self-financing - trade profits < AI costs"
            )
        
        return recommendations
    
    def generate_health_report(self) -> SystemHealthReport:
        """
        Generate comprehensive system health report.
        
        Returns:
            SystemHealthReport with all monitoring data
        """
        # Check all agents
        agents_statuses = []
        for agent_config in self.agents_config.get("agents", []):
            agent_status = self.check_agent_health(agent_config)
            agents_statuses.append(agent_status)
        
        # Check AI Nexus
        nexus_status = self.check_nexus_health()
        
        # Check coordination system
        coord_status = self.check_coordination_health()
        
        # Calculate business metrics
        business_metrics = self.calculate_business_metrics()
        
        # Collect all warnings
        warnings = []
        warnings.extend(nexus_status.get("warnings", []))
        warnings.extend(coord_status.get("warnings", []))
        
        for agent in agents_statuses:
            if agent.status == HealthStatus.WARNING:
                warnings.append(f"Agent {agent.agent_id} needs attention")
            elif agent.status == HealthStatus.CRITICAL:
                warnings.append(f"Agent {agent.agent_id} is critical")
        
        # Generate recommendations
        recommendations = self.generate_recommendations(
            agents_statuses, nexus_status, coord_status, business_metrics
        )
        
        # Determine overall status
        if any(a.status == HealthStatus.CRITICAL for a in agents_statuses):
            overall_status = HealthStatus.CRITICAL
        elif warnings:
            overall_status = HealthStatus.WARNING
        elif all(a.status == HealthStatus.HEALTHY for a in agents_statuses):
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN
        
        report = SystemHealthReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            overall_status=overall_status,
            agents=agents_statuses,
            nexus_status=nexus_status,
            coordination_status=coord_status,
            business_metrics=business_metrics,
            warnings=warnings,
            recommendations=recommendations
        )
        
        # Audit report generation
        if audit:
            audit.log_action(
                action_type="health_report_generated",
                action_data={
                    "overall_status": overall_status.value,
                    "agents_count": len(agents_statuses),
                    "warnings_count": len(warnings),
                    "recommendations_count": len(recommendations)
                },
                result="success"
            )
        
        return report
    
    def save_report(self, report: SystemHealthReport, output_path: Optional[Path] = None):
        """
        Save health report to file.
        
        Args:
            report: SystemHealthReport to save
            output_path: Optional path to save report (defaults to state/)
        """
        if output_path is None:
            output_path = self.state_dir / "ai_system_health.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
    
    def get_summary_text(self, report: SystemHealthReport) -> str:
        """
        Get human-readable summary of health report.
        
        Args:
            report: SystemHealthReport to summarize
            
        Returns:
            Formatted text summary
        """
        status_emoji = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.WARNING: "⚠️",
            HealthStatus.CRITICAL: "🚨",
            HealthStatus.UNKNOWN: "❓"
        }
        
        lines = []
        lines.append("=" * 60)
        lines.append("  AI SYSTEM HEALTH REPORT")
        lines.append("=" * 60)
        lines.append(f"Time: {report.timestamp}")
        lines.append(f"Status: {status_emoji.get(report.overall_status, '?')} {report.overall_status.value.upper()}")
        lines.append("")
        
        # Agents section
        lines.append("📡 AI AGENTS")
        lines.append("-" * 40)
        for agent in report.agents:
            emoji = status_emoji.get(agent.status, "?")
            lines.append(f"  {emoji} {agent.agent_id} ({agent.agent_type})")
            if agent.cost_24h > 0:
                lines.append(f"     Cost 24h: ${agent.cost_24h:.2f}")
            if agent.metadata.get("pending_tasks", 0) > 0:
                lines.append(f"     Pending tasks: {agent.metadata['pending_tasks']}")
        lines.append("")
        
        # AI Nexus section
        lines.append("🧠 AI NEXUS")
        lines.append("-" * 40)
        nexus = report.nexus_status
        lines.append(f"  Total cost 24h: ${nexus.get('total_cost_24h', 0):.2f}")
        lines.append(f"  Tasks 24h: {nexus.get('tasks_24h', 0)}")
        lines.append("")
        
        # Business metrics
        lines.append("💰 BUSINESS METRICS")
        lines.append("-" * 40)
        biz = report.business_metrics
        lines.append(f"  AI Cost: ${biz.get('ai_cost_24h', 0):.2f}")
        lines.append(f"  Trade Profit: ${biz.get('trade_profit_24h', 0):.2f}")
        lines.append(f"  Net: ${biz.get('net_profit_24h', 0):.2f}")
        lines.append(f"  ROI: {biz.get('roi_24h', 0):.1f}%")
        lines.append(f"  Self-financing: {'✅' if biz.get('self_financing') else '❌'}")
        lines.append("")
        
        # Warnings
        if report.warnings:
            lines.append("⚠️ WARNINGS")
            lines.append("-" * 40)
            for warning in report.warnings:
                lines.append(f"  • {warning}")
            lines.append("")
        
        # Recommendations
        if report.recommendations:
            lines.append("💡 RECOMMENDATIONS")
            lines.append("-" * 40)
            for rec in report.recommendations:
                lines.append(f"  • {rec}")
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


def main():
    """CLI entrypoint for testing"""
    print("AI System Monitor - Unified AI Monitoring")
    print()
    
    # Initialize monitor
    monitor = AISystemMonitor()
    print(f"✓ Monitor initialized")
    print(f"  Repository: {monitor.repo_root}")
    print(f"  Agents configured: {len(monitor.agents_config.get('agents', []))}")
    print()
    
    # Generate health report
    print("Generating health report...")
    report = monitor.generate_health_report()
    
    # Print summary
    print(monitor.get_summary_text(report))
    
    # Save report
    monitor.save_report(report)
    print(f"\nReport saved to: {monitor.state_dir / 'ai_system_health.json'}")


if __name__ == "__main__":
    main()
