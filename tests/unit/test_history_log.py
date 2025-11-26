"""
Unit tests for ai_nexus/history_log.py

Tests the Spark Plug history logging system v0.1
"""

import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ai_nexus.history_log import (
    HistoryEvent,
    default_kernel_ids_for_event,
    log_history_event,
    log_kernel_history_event,
)


@pytest.fixture
def temp_history_file(tmp_path):
    """Fixture that provides a temporary history log file"""
    log_file = tmp_path / "test_events.jsonl"
    with patch("ai_nexus.history_log.HISTORY_LOG_PATH", log_file):
        yield log_file


class TestHistoryEvent:
    """Tests for HistoryEvent dataclass"""

    def test_history_event_creation(self):
        """Test creating a HistoryEvent"""
        event = HistoryEvent(
            event_id="test-123",
            ts=datetime.now(timezone.utc),
            kind="risk_decision",
            source="test_source",
            kernel_ids=["risk_model_v2"],
            summary="Test event",
            details={"test": "data"},
            importance=5,
            tags=["test"],
        )

        assert event.event_id == "test-123"
        assert event.kind == "risk_decision"
        assert event.source == "test_source"
        assert event.kernel_ids == ["risk_model_v2"]
        assert event.summary == "Test event"
        assert event.details == {"test": "data"}
        assert event.importance == 5
        assert event.tags == ["test"]


class TestDefaultKernelIds:
    """Tests for default_kernel_ids_for_event function"""

    def test_risk_decision_routing(self):
        """Test that risk_decision events route to correct kernels"""
        kernel_ids = default_kernel_ids_for_event("risk_decision", "risk_model_v2")
        assert kernel_ids == ["risk_model_v2", "trading_philosophy"]

    def test_decider_outcome_routing(self):
        """Test that decider_outcome events route to correct kernels"""
        kernel_ids = default_kernel_ids_for_event("decider_outcome", "ho_decider")
        assert kernel_ids == ["risk_model_v2", "alpha_polymarket_core", "trading_philosophy"]

    def test_system_health_routing(self):
        """Test that system_health events route to correct kernels"""
        kernel_ids = default_kernel_ids_for_event("system_health", "infra_healthcheck")
        assert kernel_ids == ["system_health"]

    def test_ai_coordination_routing(self):
        """Test that ai_coordination events route to correct kernels"""
        kernel_ids = default_kernel_ids_for_event("ai_coordination", "ai_runner.sparkplug")
        assert kernel_ids == ["ai_coordination", "system_health"]

    def test_unknown_kind_fallback(self):
        """Test that unknown event kinds fall back to trading_philosophy"""
        kernel_ids = default_kernel_ids_for_event("unknown_kind", "some_source")
        assert kernel_ids == ["trading_philosophy"]


class TestLogHistoryEvent:
    """Tests for log_history_event function"""

    def test_creates_file_and_appends_line(self, temp_history_file):
        """Test that logging creates file and appends JSONL line"""
        event = HistoryEvent(
            event_id="test-001",
            ts=datetime.now(timezone.utc),
            kind="risk_decision",
            source="test_source",
            kernel_ids=["risk_model_v2"],
            summary="Test risk decision",
            details={"edge": 0.05},
            importance=8,
            tags=["test"],
        )

        log_history_event(event)

        # Check file exists
        assert temp_history_file.exists()

        # Read and verify content
        with open(temp_history_file) as f:
            lines = f.readlines()

        assert len(lines) == 1

        # Parse JSON
        event_data = json.loads(lines[0])
        assert event_data["event_id"] == "test-001"
        assert event_data["kind"] == "risk_decision"
        assert event_data["source"] == "test_source"
        assert event_data["kernel_ids"] == ["risk_model_v2"]
        assert event_data["summary"] == "Test risk decision"
        assert event_data["details"]["edge"] == 0.05
        assert event_data["importance"] == 8
        assert event_data["tags"] == ["test"]

    def test_generates_event_id_and_ts(self, temp_history_file):
        """Test that event_id and ts are auto-generated if not provided"""
        event = HistoryEvent(
            event_id="",  # Empty - should be auto-generated
            ts=None,  # None - should be auto-generated
            kind="test_event",
            source="test_source",
            kernel_ids=["test_kernel"],
            summary="Test summary",
            details={},
            importance=5,
            tags=[],
        )

        log_history_event(event)

        # Read and verify
        with open(temp_history_file) as f:
            event_data = json.loads(f.readline())

        # Should have auto-generated UUID
        assert event_data["event_id"]
        assert len(event_data["event_id"]) > 0

        # Should have ISO timestamp
        assert event_data["ts"]
        parsed_ts = datetime.fromisoformat(event_data["ts"].replace("Z", "+00:00"))
        assert isinstance(parsed_ts, datetime)

    def test_appends_multiple_events(self, temp_history_file):
        """Test that multiple events are appended as separate lines"""
        event1 = HistoryEvent(
            event_id="test-001",
            ts=datetime.now(timezone.utc),
            kind="risk_decision",
            source="test",
            kernel_ids=["risk_model_v2"],
            summary="Event 1",
            details={},
            importance=5,
            tags=[],
        )

        event2 = HistoryEvent(
            event_id="test-002",
            ts=datetime.now(timezone.utc),
            kind="decider_outcome",
            source="test",
            kernel_ids=["alpha_polymarket_core"],
            summary="Event 2",
            details={},
            importance=6,
            tags=[],
        )

        log_history_event(event1)
        log_history_event(event2)

        # Read and verify
        with open(temp_history_file) as f:
            lines = f.readlines()

        assert len(lines) == 2

        event1_data = json.loads(lines[0])
        event2_data = json.loads(lines[1])

        assert event1_data["event_id"] == "test-001"
        assert event2_data["event_id"] == "test-002"

    def test_validates_required_fields(self, temp_history_file, capsys):
        """Test that logging validates required fields"""
        # Empty kernel_ids
        event = HistoryEvent(
            event_id="test-001",
            ts=datetime.now(timezone.utc),
            kind="risk_decision",
            source="test",
            kernel_ids=[],  # Empty!
            summary="Test",
            details={},
            importance=5,
            tags=[],
        )

        log_history_event(event)

        # Should print warning and not write
        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        assert "empty kernel_ids" in captured.out
        assert not temp_history_file.exists()

    def test_handles_errors_gracefully(self, temp_history_file, capsys):
        """Test that logging errors don't raise exceptions"""
        # Create an event with non-serializable details
        class NonSerializable:
            pass

        event = HistoryEvent(
            event_id="test-001",
            ts=datetime.now(timezone.utc),
            kind="risk_decision",
            source="test",
            kernel_ids=["risk_model_v2"],
            summary="Test",
            details={"bad": NonSerializable()},  # Can't serialize this
            importance=5,
            tags=[],
        )

        # Should not raise - just print error
        log_history_event(event)

        captured = capsys.readouterr()
        assert "ERROR" in captured.out


class TestLogKernelHistoryEvent:
    """Tests for log_kernel_history_event convenience function"""

    def test_uses_default_kernel_ids(self, temp_history_file):
        """Test that kernel_ids are auto-derived when not provided"""
        log_kernel_history_event(
            kernel_ids=None,  # Should auto-derive
            kind="risk_decision",
            source="risk_model_v2",
            summary="Test risk decision",
            details={"edge": 0.05},
            importance=8,
            tags=["test"],
        )

        # Read and verify
        with open(temp_history_file) as f:
            event_data = json.loads(f.readline())

        # Should have auto-derived kernel_ids for risk_decision
        assert event_data["kernel_ids"] == ["risk_model_v2", "trading_philosophy"]

    def test_uses_provided_kernel_ids(self, temp_history_file):
        """Test that explicit kernel_ids are used when provided"""
        log_kernel_history_event(
            kernel_ids=["custom_kernel"],
            kind="risk_decision",
            source="test",
            summary="Test",
            importance=5,
        )

        with open(temp_history_file) as f:
            event_data = json.loads(f.readline())

        # Should use provided kernel_ids, not default
        assert event_data["kernel_ids"] == ["custom_kernel"]

    def test_fills_defaults(self, temp_history_file):
        """Test that default values are filled correctly"""
        log_kernel_history_event(
            kernel_ids=["test_kernel"],
            kind="test_event",
            source="test_source",
            summary="Test summary",
            # details, importance, tags, ts not provided - should use defaults
        )

        with open(temp_history_file) as f:
            event_data = json.loads(f.readline())

        assert event_data["details"] == {}
        assert event_data["importance"] == 5  # default
        assert event_data["tags"] == []
        assert event_data["ts"]  # Should be auto-generated

    def test_handles_errors_gracefully(self, temp_history_file, capsys):
        """Test that errors in convenience function don't raise"""
        # Force an error by providing invalid data
        log_kernel_history_event(
            kernel_ids=None,
            kind="",  # Empty kind - will fail validation
            source="test",
            summary="Test",
        )

        # Should not raise
        captured = capsys.readouterr()
        # May print warning or error, but shouldn't crash


class TestIntegrationWithDecider:
    """Integration tests for history logging from decider"""

    @pytest.mark.skip(reason="Integration test - requires full import setup")
    @patch("ai_nexus.history_log.log_kernel_history_event")
    def test_decider_logs_risk_decisions(self, mock_log):
        """Test that decider logs risk decisions for each market"""
        from decider.ho_decider import Decider

        decider = Decider(bankroll=1000.0)

        alpha_signals = [
            {
                "market_id": "test-market-1",
                "market_name": "Test Market 1",
                "edge": 0.05,
                "current_odds": 0.5,
                "side": "YES",
                "model_confidence": 0.7,
            }
        ]

        actions = decider.plan_actions(alpha_signals)

        # Should have logged both individual risk decision and aggregate outcome
        assert mock_log.call_count == 2

        # Check first call (risk decision)
        first_call = mock_log.call_args_list[0]
        assert first_call[1]["kind"] == "risk_decision"
        assert first_call[1]["source"] == "risk_model_v2"
        assert "risk_model_v2" in first_call[1]["kernel_ids"]
        assert "trading_philosophy" in first_call[1]["kernel_ids"]

        # Check second call (decider outcome)
        second_call = mock_log.call_args_list[1]
        assert second_call[1]["kind"] == "decider_outcome"
        assert second_call[1]["source"] == "ho_decider"
        assert "alpha_polymarket_core" in second_call[1]["kernel_ids"]


class TestIntegrationWithAIRunner:
    """Integration tests for history logging from AI runner"""

    @pytest.mark.skip(reason="Integration test - requires ai_runner module setup")
    @patch("ai_runner.log_kernel_history_event")  # Patch where it's imported
    @patch("ai_nexus.spark_plug_autokernel.run_autokernel_refresh")
    def test_ai_runner_logs_coordination_events(self, mock_refresh, mock_log):
        """Test that AI runner logs coordination events"""
        from ai_runner import process_sparkplug_autokernel_refresh

        # Mock the autokernel refresh to return success
        mock_refresh.return_value = {
            "status": "success",
            "kernel_id": "risk_model_v2",
        }

        task = {
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": "test-task-123",
            "mode": "explicit",
            "kernels": [{"kernel_id": "risk_model_v2", "mode": "cpu"}],
            "dry_run": True,
        }

        result = process_sparkplug_autokernel_refresh(task)

        # Should have logged AI coordination event
        mock_log.assert_called_once()

        call_args = mock_log.call_args[1]
        assert call_args["kind"] == "ai_coordination"
        assert call_args["source"] == "ai_runner.sparkplug"
        assert "ai_coordination" in call_args["kernel_ids"]
        assert "system_health" in call_args["kernel_ids"]
        assert "test-task-123" in call_args["summary"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
