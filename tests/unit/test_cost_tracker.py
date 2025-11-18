"""Unit tests for LLM Cost Tracker"""
import sys
from pathlib import Path
import json
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm.cost_tracker import CostTracker, SessionSummary, TokenUsage
import pytest


@pytest.mark.unit
class TestCostTracker:
    """Test suite for CostTracker"""

    def test_cost_tracker_initialization(self):
        """Should initialize with empty tracking state"""
        tracker = CostTracker()

        assert len(tracker.calls) == 0
        assert tracker.session_start is not None

    def test_track_call_basic(self):
        """Should track a single API call"""
        tracker = CostTracker()

        cost = tracker.track_call(
            model_name="claude-sonnet-4",
            tokens_in=100,
            tokens_out=50,
            backend="claude-api",
        )

        assert len(tracker.calls) == 1
        assert cost > 0

    def test_track_call_returns_cost(self):
        """Should return calculated cost for Claude API"""
        tracker = CostTracker()

        # Claude Sonnet 4: $3/MTok input, $15/MTok output
        cost = tracker.track_call(
            model_name="claude-sonnet-4",
            tokens_in=1000,  # $0.003
            tokens_out=1000,  # $0.015
            backend="claude-api",
        )

        # Total: $0.018
        assert abs(cost - 0.018) < 0.0001

    def test_track_call_openrouter_pricing(self):
        """Should calculate OpenRouter pricing correctly"""
        tracker = CostTracker()

        # OpenRouter GPT-4: $10/MTok input, $30/MTok output
        cost = tracker.track_call(
            model_name="gpt-4-turbo",
            tokens_in=1000,  # $0.01
            tokens_out=1000,  # $0.03
            backend="openrouter-gpt4",
        )

        # Total: $0.04
        assert abs(cost - 0.04) < 0.0001

    def test_track_call_fallback_pricing(self):
        """Should use zero cost for unknown models"""
        tracker = CostTracker()

        # Unknown model defaults to zero cost
        cost = tracker.track_call(
            model_name="unknown-model",
            tokens_in=1000,
            tokens_out=1000,
            backend="unknown",
        )

        # Total: $0.00
        assert cost == 0.0

    def test_track_call_simulation_zero_cost(self):
        """Should track zero cost for simulation/DRYRUN calls"""
        tracker = CostTracker()

        cost = tracker.track_call(
            model_name="dryrun",
            tokens_in=1000,
            tokens_out=1000,
            backend="simulation",
        )

        assert cost == 0.0

    def test_track_multiple_calls(self):
        """Should track multiple calls and accumulate"""
        tracker = CostTracker()

        tracker.track_call("claude-sonnet-4", 100, 50, "claude-api")
        tracker.track_call("claude-sonnet-4", 200, 100, "claude-api")
        tracker.track_call("gpt-4-turbo", 150, 75, "openrouter-gpt4")

        assert len(tracker.calls) == 3

    def test_aggregate_session_totals(self):
        """Should aggregate session totals correctly"""
        tracker = CostTracker()

        tracker.track_call("claude-sonnet-4", 1000, 500, "claude-api")  # $0.0105
        tracker.track_call("claude-sonnet-4", 2000, 1000, "claude-api")  # $0.021
        tracker.track_call("dryrun", 1000, 1000, "simulation")  # $0

        summary = tracker.aggregate_session()

        assert summary.total_calls == 3
        assert summary.total_tokens_in == 4000
        assert summary.total_tokens_out == 2500
        assert abs(summary.total_cost_usd - 0.0315) < 0.0001

    def test_aggregate_session_by_backend(self):
        """Should break down calls and costs by backend"""
        tracker = CostTracker()

        tracker.track_call("claude-sonnet-4", 1000, 500, "claude-api")
        tracker.track_call("gpt-4-turbo", 1000, 500, "openrouter-gpt4")
        tracker.track_call("dryrun", 1000, 500, "simulation")

        summary = tracker.aggregate_session()

        # Check calls_by_backend
        assert "claude-api" in summary.calls_by_backend
        assert "openrouter-gpt4" in summary.calls_by_backend
        assert "simulation" in summary.calls_by_backend

        assert summary.calls_by_backend["claude-api"] == 1
        assert summary.calls_by_backend["openrouter-gpt4"] == 1
        assert summary.calls_by_backend["simulation"] == 1

        # Check cost_by_backend
        assert "claude-api" in summary.cost_by_backend
        assert summary.cost_by_backend["claude-api"] > 0
        assert summary.cost_by_backend["simulation"] == 0.0

    def test_aggregate_session_by_model(self):
        """Should break down calls by model"""
        tracker = CostTracker()

        tracker.track_call("claude-sonnet-4", 1000, 500, "claude-api")
        tracker.track_call("claude-sonnet-4", 2000, 1000, "claude-api")
        tracker.track_call("gpt-4-turbo", 1000, 500, "openrouter-gpt4")

        summary = tracker.aggregate_session()

        assert "claude-sonnet-4" in summary.calls_by_model
        assert "gpt-4-turbo" in summary.calls_by_model

        # Two claude calls
        assert summary.calls_by_model["claude-sonnet-4"] == 2
        assert summary.calls_by_model["gpt-4-turbo"] == 1

    def test_check_budget_under_limit(self):
        """Should return over_budget=False when under budget"""
        tracker = CostTracker()

        tracker.track_call("claude-sonnet-4", 100, 50, "claude-api")  # ~$0.001

        result = tracker.check_budget(budget_usd=1.0)

        assert result["over_budget"] is False
        assert result["spent_usd"] < 1.0
        assert result["remaining_usd"] > 0
        assert result["total_calls"] == 1

    def test_check_budget_over_limit(self):
        """Should return over_budget=True when over budget"""
        tracker = CostTracker()

        # Add many calls to exceed budget
        for _ in range(100):
            tracker.track_call("claude-sonnet-4", 1000, 1000, "claude-api")  # $0.018 each

        result = tracker.check_budget(budget_usd=0.01)

        assert result["over_budget"] is True
        assert result["spent_usd"] > 0.01
        assert result["remaining_usd"] < 0
        assert result["total_calls"] == 100

    def test_check_budget_returns_dict(self):
        """Should return dict with all expected keys"""
        tracker = CostTracker()

        tracker.track_call("claude-sonnet-4", 100, 50, "claude-api")

        result = tracker.check_budget(budget_usd=1.0)

        assert "budget_usd" in result
        assert "spent_usd" in result
        assert "remaining_usd" in result
        assert "percent_used" in result
        assert "over_budget" in result
        assert "total_calls" in result

    def test_export_cost_report(self, tmp_path):
        """Should export cost report to JSON"""
        tracker = CostTracker()
        output_file = tmp_path / "cost_report.json"

        tracker.track_call("claude-sonnet-4", 1000, 500, "claude-api")
        tracker.track_call("gpt-4-turbo", 500, 250, "openrouter-gpt4")

        tracker.export_cost_report(output_file)

        # Should create file
        assert output_file.exists()

        # Should be valid JSON
        data = json.loads(output_file.read_text())

        assert "summary" in data
        assert "detailed_calls" in data

        summary = data["summary"]
        assert summary["total_calls"] == 2
        assert summary["total_tokens_in"] == 1500
        assert summary["total_tokens_out"] == 750
        assert summary["total_cost_usd"] > 0

    def test_export_cost_report_creates_directory(self, tmp_path):
        """Should create parent directories if needed"""
        tracker = CostTracker()
        output_file = tmp_path / "nested" / "dir" / "cost_report.json"

        tracker.track_call("dryrun", 100, 50, "simulation")

        # Should not crash
        tracker.export_cost_report(output_file)

        assert output_file.exists()

    def test_call_history_includes_metadata(self):
        """Should store metadata with each call"""
        tracker = CostTracker()

        tracker.track_call(
            model_name="claude-sonnet-4",
            tokens_in=100,
            tokens_out=50,
            backend="claude-api",
            metadata={"market_id": "test-123", "category": "crypto"},
        )

        assert len(tracker.calls) == 1

        call = tracker.calls[0]
        assert isinstance(call, TokenUsage)
        assert call.model_name == "claude-sonnet-4"
        assert call.tokens_in == 100
        assert call.tokens_out == 50
        assert call.backend == "claude-api"
        assert call.metadata["market_id"] == "test-123"
        assert call.metadata["category"] == "crypto"

    def test_call_history_timestamp_format(self):
        """Should use ISO timestamp format"""
        tracker = CostTracker()

        tracker.track_call("dryrun", 100, 50, "simulation")

        call = tracker.calls[0]
        timestamp = call.timestamp

        # Should be valid ISO format
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_zero_tokens_handled_gracefully(self):
        """Should handle zero token counts"""
        tracker = CostTracker()

        cost = tracker.track_call(
            model_name="claude-sonnet-4",
            tokens_in=0,
            tokens_out=0,
            backend="claude-api",
        )

        assert cost == 0.0
        assert len(tracker.calls) == 1

    def test_session_summary_dataclass(self):
        """SessionSummary should be a proper dataclass"""
        summary = SessionSummary(
            session_start="2025-01-01T00:00:00Z",
            session_end="2025-01-01T01:00:00Z",
            total_calls=10,
            total_tokens_in=5000,
            total_tokens_out=2500,
            total_cost_usd=0.15,
            calls_by_backend={"claude-api": 10},
            calls_by_model={"claude-sonnet-4": 10},
            cost_by_backend={"claude-api": 0.15},
        )

        assert summary.total_calls == 10
        assert summary.total_tokens_in == 5000
        assert summary.total_cost_usd == 0.15
        assert summary.calls_by_backend["claude-api"] == 10
        assert summary.calls_by_model["claude-sonnet-4"] == 10
        assert summary.cost_by_backend["claude-api"] == 0.15

    def test_large_session_performance(self):
        """Should handle large number of calls efficiently"""
        tracker = CostTracker()

        # Track 1000 calls
        for i in range(1000):
            tracker.track_call(
                model_name="dryrun",
                tokens_in=100,
                tokens_out=50,
                backend="simulation",
            )

        summary = tracker.aggregate_session()

        assert summary.total_calls == 1000
        assert summary.total_tokens_in == 100000
        assert summary.total_tokens_out == 50000

    def test_export_includes_detailed_calls(self, tmp_path):
        """Exported report should include detailed call history"""
        tracker = CostTracker()
        output_file = tmp_path / "report.json"

        tracker.track_call("claude-sonnet-4", 100, 50, "claude-api")
        tracker.track_call("gpt-4-turbo", 200, 100, "openrouter-gpt4")

        tracker.export_cost_report(output_file)

        data = json.loads(output_file.read_text())

        assert len(data["detailed_calls"]) == 2
        assert data["detailed_calls"][0]["model_name"] == "claude-sonnet-4"
        assert data["detailed_calls"][1]["model_name"] == "gpt-4-turbo"

    def test_backend_breakdown_accuracy(self):
        """Backend cost breakdown should sum to total"""
        tracker = CostTracker()

        tracker.track_call("claude-sonnet-4", 1000, 500, "claude-api")
        tracker.track_call("gpt-4-turbo", 1000, 500, "openrouter-gpt4")
        tracker.track_call("dryrun", 1000, 500, "simulation")

        summary = tracker.aggregate_session()

        # Sum of backend costs should equal total cost
        backend_total = sum(summary.cost_by_backend.values())

        assert abs(backend_total - summary.total_cost_usd) < 0.0001

    def test_get_total_cost(self):
        """Should calculate total cost for session"""
        tracker = CostTracker()

        tracker.track_call("claude-sonnet-4", 1000, 500, "claude-api")
        tracker.track_call("claude-sonnet-4", 2000, 1000, "claude-api")

        total_cost = tracker.get_total_cost()

        assert total_cost > 0
        assert abs(total_cost - 0.0315) < 0.0001

    def test_get_total_tokens(self):
        """Should calculate total tokens for session"""
        tracker = CostTracker()

        tracker.track_call("claude-sonnet-4", 1000, 500, "claude-api")
        tracker.track_call("claude-sonnet-4", 2000, 1000, "claude-api")

        total_tokens = tracker.get_total_tokens()

        assert total_tokens == 4500  # (1000+500) + (2000+1000)

    def test_reset(self):
        """Should reset tracker for new session"""
        tracker = CostTracker()

        tracker.track_call("claude-sonnet-4", 1000, 500, "claude-api")
        assert len(tracker.calls) == 1

        tracker.reset()

        assert len(tracker.calls) == 0
        assert tracker.session_start is not None

    def test_aggregate_session_empty(self):
        """Should handle empty session"""
        tracker = CostTracker()

        summary = tracker.aggregate_session()

        assert summary.total_calls == 0
        assert summary.total_tokens_in == 0
        assert summary.total_tokens_out == 0
        assert summary.total_cost_usd == 0.0
        assert summary.calls_by_backend == {}
        assert summary.calls_by_model == {}
        assert summary.cost_by_backend == {}

    def test_token_usage_dataclass(self):
        """TokenUsage should be a proper dataclass"""
        usage = TokenUsage(
            timestamp="2025-01-01T00:00:00Z",
            model_name="claude-sonnet-4",
            backend="claude-api",
            tokens_in=100,
            tokens_out=50,
            cost_usd=0.001,
            metadata={"test": "value"},
        )

        assert usage.model_name == "claude-sonnet-4"
        assert usage.backend == "claude-api"
        assert usage.tokens_in == 100
        assert usage.tokens_out == 50
        assert usage.cost_usd == 0.001
        assert usage.metadata["test"] == "value"
