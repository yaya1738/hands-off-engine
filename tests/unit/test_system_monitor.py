"""
Unit tests for AI System Monitor

Tests the unified monitoring system for AI agents and AI Nexus.
"""

import json
import pytest
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_nexus.system_monitor import (
    AISystemMonitor,
    SystemHealthReport,
    AgentStatus,
    HealthStatus
)


@pytest.fixture
def temp_repo_dir():
    """Create temporary repository structure for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        
        # Create directory structure
        (temp_path / "ai" / "coordination").mkdir(parents=True)
        (temp_path / "ai" / "agents").mkdir(parents=True)
        (temp_path / "logs" / "ai_nexus").mkdir(parents=True)
        (temp_path / "logs" / "ledger").mkdir(parents=True)
        (temp_path / "state").mkdir(parents=True)
        
        yield temp_path


@pytest.fixture
def sample_agents_registry(temp_repo_dir):
    """Create sample agents registry"""
    registry = {
        "version": "0.1",
        "agents": [
            {
                "id": "chatgpt",
                "kind": "llm",
                "role": "research_and_design"
            },
            {
                "id": "claude_cli",
                "kind": "llm",
                "role": "primary_repo_implementer"
            },
            {
                "id": "github_copilot_agent",
                "kind": "llm",
                "role": "github_native_helper"
            }
        ]
    }
    
    registry_file = temp_repo_dir / "ai" / "agents" / "AGENTS_REGISTRY_v0.1.json"
    with open(registry_file, 'w') as f:
        json.dump(registry, f)
    
    return registry_file


@pytest.fixture
def sample_coordination_status(temp_repo_dir):
    """Create sample coordination status"""
    status = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "active_agents": ["copilot", "claude-code", "chatgpt"],
        "autonomous_mode": {
            "copilot": True,
            "chatgpt": True,
            "claude-code": True
        },
        "current_phase": "Autonomous Operation",
        "pending_tasks": [
            {
                "id": "test-task-1",
                "assigned_to": "copilot",
                "status": "in_progress"
            }
        ]
    }
    
    status_file = temp_repo_dir / "ai" / "coordination" / "status.json"
    with open(status_file, 'w') as f:
        json.dump(status, f)
    
    return status_file


@pytest.fixture
def sample_coordination_messages(temp_repo_dir):
    """Create sample coordination messages"""
    messages = [
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from": "chatgpt",
            "to": "claude-code",
            "type": "request",
            "message": "Test message"
        },
        {
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "from": "copilot",
            "to": "claude-code",
            "type": "response",
            "message": "Test response"
        }
    ]
    
    messages_file = temp_repo_dir / "ai" / "coordination" / "messages.jsonl"
    with open(messages_file, 'w') as f:
        for msg in messages:
            f.write(json.dumps(msg) + '\n')
    
    return messages_file


@pytest.fixture
def sample_nexus_state(temp_repo_dir):
    """Create sample AI Nexus state"""
    state = {
        "daily_costs": {
            "copilot": 15.50,
            "chatgpt": 8.25,
            "claude": 5.00
        },
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    
    state_file = temp_repo_dir / "logs" / "ai_nexus" / "nexus_state.json"
    with open(state_file, 'w') as f:
        json.dump(state, f)
    
    return state_file


@pytest.fixture
def sample_ledger_entries(temp_repo_dir):
    """Create sample ledger entries"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries = [
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entry_type": "ai_task",
            "action": "AI task via copilot",
            "cost": 2.50,
            "revenue": 0.0,
            "profit": -2.50
        },
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entry_type": "trade",
            "action": "Trade: SELL 100 btc_100k @ 0.35",
            "cost": 0.0,
            "revenue": 35.0,
            "profit": 15.0
        }
    ]
    
    ledger_file = temp_repo_dir / "logs" / "ledger" / f"ledger_{today}.jsonl"
    with open(ledger_file, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')
    
    return ledger_file


class TestAISystemMonitor:
    """Test AISystemMonitor class"""
    
    def test_initialization(self, temp_repo_dir, sample_agents_registry):
        """Test monitor initialization"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        
        assert monitor.repo_root == temp_repo_dir
        assert len(monitor.agents_config.get("agents", [])) == 3
    
    def test_load_agents_registry(self, temp_repo_dir, sample_agents_registry):
        """Test loading agents registry"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        
        agents = monitor.agents_config.get("agents", [])
        assert len(agents) == 3
        
        agent_ids = [a["id"] for a in agents]
        assert "chatgpt" in agent_ids
        assert "claude_cli" in agent_ids
        assert "github_copilot_agent" in agent_ids
    
    def test_load_coordination_status(
        self, 
        temp_repo_dir, 
        sample_agents_registry,
        sample_coordination_status
    ):
        """Test loading coordination status"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        status = monitor._load_coordination_status()
        
        assert "active_agents" in status
        assert len(status["active_agents"]) == 3
        assert "autonomous_mode" in status
    
    def test_load_coordination_messages(
        self,
        temp_repo_dir,
        sample_agents_registry,
        sample_coordination_messages
    ):
        """Test loading coordination messages"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        messages = monitor._load_coordination_messages()
        
        assert len(messages) == 2
        assert messages[0]["from"] == "chatgpt"
    
    def test_load_nexus_state(
        self,
        temp_repo_dir,
        sample_agents_registry,
        sample_nexus_state
    ):
        """Test loading AI Nexus state"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        state = monitor._load_nexus_state()
        
        assert "daily_costs" in state
        assert state["daily_costs"]["copilot"] == 15.50


class TestAgentHealthCheck:
    """Test agent health checking"""
    
    def test_check_agent_health_healthy(
        self,
        temp_repo_dir,
        sample_agents_registry,
        sample_coordination_status,
        sample_coordination_messages
    ):
        """Test checking healthy agent"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        
        agent_config = {"id": "chatgpt", "kind": "llm"}
        status = monitor.check_agent_health(agent_config)
        
        assert status.agent_id == "chatgpt"
        assert status.agent_type == "llm"
        assert status.status == HealthStatus.HEALTHY
        assert status.tasks_completed_24h > 0
    
    def test_check_agent_health_unknown(
        self,
        temp_repo_dir,
        sample_agents_registry
    ):
        """Test checking unknown agent status"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        
        agent_config = {"id": "unknown_agent", "kind": "llm"}
        status = monitor.check_agent_health(agent_config)
        
        assert status.agent_id == "unknown_agent"
        assert status.status == HealthStatus.UNKNOWN
        assert status.tasks_completed_24h == 0


class TestNexusHealthCheck:
    """Test AI Nexus health checking"""
    
    def test_check_nexus_health(
        self,
        temp_repo_dir,
        sample_agents_registry,
        sample_nexus_state
    ):
        """Test checking AI Nexus health"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        status = monitor.check_nexus_health()
        
        assert status["status"] in ["healthy", "warning"]
        assert "total_cost_24h" in status
        assert "budget_status" in status
        assert status["total_cost_24h"] == 28.75  # 15.50 + 8.25 + 5.00
    
    def test_check_nexus_budget_warning(self, temp_repo_dir, sample_agents_registry):
        """Test budget warning detection"""
        # Create state with high budget usage
        state = {
            "daily_costs": {
                "copilot": 95.00  # 95% of $100 limit
            }
        }
        state_file = temp_repo_dir / "logs" / "ai_nexus" / "nexus_state.json"
        with open(state_file, 'w') as f:
            json.dump(state, f)
        
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        status = monitor.check_nexus_health()
        
        assert status["status"] == "warning"
        assert len(status["warnings"]) > 0
        assert any("copilot" in w for w in status["warnings"])


class TestCoordinationHealthCheck:
    """Test coordination system health checking"""
    
    def test_check_coordination_health(
        self,
        temp_repo_dir,
        sample_agents_registry,
        sample_coordination_status,
        sample_coordination_messages
    ):
        """Test checking coordination health"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        status = monitor.check_coordination_health()
        
        assert status["status"] in ["healthy", "warning"]
        assert "messages_24h" in status
        assert "active_agents" in status
    
    def test_check_coordination_no_messages(
        self,
        temp_repo_dir,
        sample_agents_registry,
        sample_coordination_status
    ):
        """Test warning when no recent messages"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        status = monitor.check_coordination_health()
        
        # No messages file created, should warn
        assert status["status"] == "warning"
        assert any("No agent coordination messages" in w for w in status["warnings"])


class TestBusinessMetrics:
    """Test business metrics calculation"""
    
    def test_calculate_business_metrics(
        self,
        temp_repo_dir,
        sample_agents_registry,
        sample_ledger_entries
    ):
        """Test business metrics calculation"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        metrics = monitor.calculate_business_metrics()
        
        assert "ai_cost_24h" in metrics
        assert "trade_profit_24h" in metrics
        assert "net_profit_24h" in metrics
        assert "roi_24h" in metrics
        assert "self_financing" in metrics
        
        # Based on sample data: AI cost 2.50, trade profit 15.00
        assert metrics["ai_cost_24h"] == 2.50
        assert metrics["trade_profit_24h"] == 15.0
        assert metrics["net_profit_24h"] == 12.50
        assert metrics["self_financing"] == True
    
    def test_calculate_business_metrics_empty(
        self,
        temp_repo_dir,
        sample_agents_registry
    ):
        """Test metrics with no ledger entries"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        metrics = monitor.calculate_business_metrics()
        
        assert metrics["ai_cost_24h"] == 0
        assert metrics["trade_profit_24h"] == 0
        assert metrics["net_profit_24h"] == 0
        assert metrics["roi_24h"] == 0


class TestROICalculation:
    """Test ROI calculation helper"""
    
    def test_calculate_roi_positive(self, temp_repo_dir, sample_agents_registry):
        """Test ROI calculation with profit"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        
        # $15 profit on $5 cost = 200% ROI
        roi = monitor._calculate_roi(15.0, 5.0)
        assert roi == 200.0
    
    def test_calculate_roi_negative(self, temp_repo_dir, sample_agents_registry):
        """Test ROI calculation with loss"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        
        # $3 profit on $10 cost = -70% ROI (lost $7)
        roi = monitor._calculate_roi(3.0, 10.0)
        assert roi == -70.0
    
    def test_calculate_roi_zero_cost(self, temp_repo_dir, sample_agents_registry):
        """Test ROI with zero cost"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        
        roi = monitor._calculate_roi(100.0, 0.0)
        assert roi == 0.0
    
    def test_calculate_roi_breakeven(self, temp_repo_dir, sample_agents_registry):
        """Test ROI at breakeven"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        
        # $10 profit on $10 cost = 0% ROI (breakeven)
        roi = monitor._calculate_roi(10.0, 10.0)
        assert roi == 0.0


class TestHealthReport:
    """Test health report generation"""
    
    def test_generate_health_report(
        self,
        temp_repo_dir,
        sample_agents_registry,
        sample_coordination_status,
        sample_coordination_messages,
        sample_nexus_state,
        sample_ledger_entries
    ):
        """Test generating complete health report"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        report = monitor.generate_health_report()
        
        assert isinstance(report, SystemHealthReport)
        assert report.timestamp is not None
        assert report.overall_status in HealthStatus
        assert len(report.agents) == 3
        assert "budget_status" in report.nexus_status
        assert "active_agents" in report.coordination_status
        assert "ai_cost_24h" in report.business_metrics
    
    def test_health_report_to_dict(
        self,
        temp_repo_dir,
        sample_agents_registry,
        sample_coordination_status
    ):
        """Test converting report to dictionary"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        report = monitor.generate_health_report()
        
        report_dict = report.to_dict()
        
        assert isinstance(report_dict, dict)
        assert "timestamp" in report_dict
        assert "overall_status" in report_dict
        assert isinstance(report_dict["overall_status"], str)
        assert "agents" in report_dict
        assert isinstance(report_dict["agents"], list)
    
    def test_save_report(
        self,
        temp_repo_dir,
        sample_agents_registry,
        sample_coordination_status
    ):
        """Test saving report to file"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        report = monitor.generate_health_report()
        
        output_path = temp_repo_dir / "state" / "test_report.json"
        monitor.save_report(report, output_path)
        
        assert output_path.exists()
        
        with open(output_path) as f:
            saved = json.load(f)
        
        assert saved["timestamp"] == report.timestamp
        assert saved["overall_status"] == report.overall_status.value


class TestRecommendations:
    """Test recommendation generation"""
    
    def test_generate_recommendations_inactive_agents(
        self,
        temp_repo_dir,
        sample_agents_registry
    ):
        """Test recommendations for inactive agents"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        
        agents = [
            AgentStatus(
                agent_id="agent1",
                agent_type="llm",
                status=HealthStatus.WARNING
            ),
            AgentStatus(
                agent_id="agent2",
                agent_type="llm",
                status=HealthStatus.HEALTHY
            )
        ]
        
        recommendations = monitor.generate_recommendations(
            agents,
            {"warnings": []},
            {"warnings": []},
            {"model_age_hours": 2, "roi_24h": 10, "self_financing": True}
        )
        
        assert any("inactive agents" in r.lower() for r in recommendations)
    
    def test_generate_recommendations_negative_roi(
        self,
        temp_repo_dir,
        sample_agents_registry
    ):
        """Test recommendations for negative ROI"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        
        agents = [
            AgentStatus(
                agent_id="agent1",
                agent_type="llm",
                status=HealthStatus.HEALTHY
            )
        ]
        
        recommendations = monitor.generate_recommendations(
            agents,
            {"warnings": []},
            {"warnings": []},
            {"model_age_hours": 2, "roi_24h": -20, "self_financing": False, "ai_cost_24h": 10}
        )
        
        assert any("roi is negative" in r.lower() for r in recommendations)
        assert any("self-financing" in r.lower() for r in recommendations)


class TestSummaryText:
    """Test human-readable summary generation"""
    
    def test_get_summary_text(
        self,
        temp_repo_dir,
        sample_agents_registry,
        sample_coordination_status
    ):
        """Test generating summary text"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        report = monitor.generate_health_report()
        
        summary = monitor.get_summary_text(report)
        
        assert isinstance(summary, str)
        assert "AI SYSTEM HEALTH REPORT" in summary
        assert "AI AGENTS" in summary
        assert "AI NEXUS" in summary
        assert "BUSINESS METRICS" in summary


class TestHelperMethods:
    """Test helper methods"""
    
    def test_is_within_hours_true(self, temp_repo_dir, sample_agents_registry):
        """Test is_within_hours returns True for recent timestamp"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        
        recent = datetime.now(timezone.utc).isoformat()
        result = monitor._is_within_hours(recent, 24)
        
        assert result == True
    
    def test_is_within_hours_false(self, temp_repo_dir, sample_agents_registry):
        """Test is_within_hours returns False for old timestamp"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        
        old = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        result = monitor._is_within_hours(old, 24)
        
        assert result == False
    
    def test_is_stale_true(self, temp_repo_dir, sample_agents_registry):
        """Test is_stale returns True for old timestamp"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        
        old = (datetime.now(timezone.utc) - timedelta(hours=100)).isoformat()
        result = monitor._is_stale(old, 48)
        
        assert result == True
    
    def test_is_stale_none(self, temp_repo_dir, sample_agents_registry):
        """Test is_stale returns True for None timestamp"""
        monitor = AISystemMonitor(repo_root=str(temp_repo_dir))
        
        result = monitor._is_stale(None, 48)
        
        assert result == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
