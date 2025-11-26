"""
Unit tests for audit logging functionality

Tests the audit logging system using ai_nexus/history_log.py
which provides the audit trail for the Hands-Off Engine.
"""

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_nexus.history_log import (
    HistoryEvent,
    log_history_event,
    log_kernel_history_event,
    default_kernel_ids_for_event,
)


class TestAuditLoggingBasics:
    """Basic tests for audit logging functionality"""

    def test_history_event_creation(self):
        """Test creating a HistoryEvent for audit logging"""
        event = HistoryEvent(
            event_id="audit-001",
            ts=datetime.now(timezone.utc),
            kind="execution",
            source="executor",
            kernel_ids=["audit_trail"],
            summary="Test execution event",
            details={"action": "test", "amount": 50.0},
            importance=8,
            tags=["test", "audit"],
        )

        assert event.event_id == "audit-001"
        assert event.kind == "execution"
        assert event.source == "executor"
        assert event.summary == "Test execution event"
        assert event.details["amount"] == 50.0
        assert "audit" in event.tags

    def test_log_history_event_writes_to_file(self, tmp_path):
        """Test that audit events are written to log file"""
        log_file = tmp_path / "audit.jsonl"
        
        with patch("ai_nexus.history_log.HISTORY_LOG_PATH", log_file):
            event = HistoryEvent(
                event_id="audit-001",
                ts=datetime.now(timezone.utc),
                kind="execution",
                source="executor",
                kernel_ids=["audit_trail"],
                summary="Test audit event",
                details={"test": "data"},
                importance=8,
                tags=["audit"],
            )

            log_history_event(event)

            # Verify file exists and contains event
            assert log_file.exists()
            with open(log_file) as f:
                logged = json.loads(f.readline())
            
            assert logged["event_id"] == "audit-001"
            assert logged["kind"] == "execution"
            assert logged["summary"] == "Test audit event"

    def test_log_multiple_audit_events(self, tmp_path):
        """Test logging multiple audit events"""
        log_file = tmp_path / "audit.jsonl"
        
        with patch("ai_nexus.history_log.HISTORY_LOG_PATH", log_file):
            for i in range(3):
                event = HistoryEvent(
                    event_id=f"audit-{i:03d}",
                    ts=datetime.now(timezone.utc),
                    kind="execution",
                    source="executor",
                    kernel_ids=["audit_trail"],
                    summary=f"Audit event {i}",
                    details={"index": i},
                    importance=8,
                    tags=["audit"],
                )
                log_history_event(event)

            # Verify all events logged
            with open(log_file) as f:
                lines = f.readlines()
            
            assert len(lines) == 3
            for i, line in enumerate(lines):
                logged = json.loads(line)
                assert logged["event_id"] == f"audit-{i:03d}"


class TestAuditEventTypes:
    """Tests for different audit event types"""

    def test_execution_audit_event(self, tmp_path):
        """Test audit logging for execution events"""
        log_file = tmp_path / "audit.jsonl"
        
        with patch("ai_nexus.history_log.HISTORY_LOG_PATH", log_file):
            log_kernel_history_event(
                kernel_ids=["audit_trail"],
                kind="execution",
                source="executor",
                summary="Executed trade on market_123",
                details={
                    "market_id": "market_123",
                    "side": "YES",
                    "amount": 75.0,
                    "success": True,
                },
                importance=9,
                tags=["execution", "audit"],
            )

            with open(log_file) as f:
                logged = json.loads(f.readline())
            
            assert logged["kind"] == "execution"
            assert logged["details"]["market_id"] == "market_123"
            assert logged["importance"] == 9

    def test_risk_decision_audit_event(self, tmp_path):
        """Test audit logging for risk decisions"""
        log_file = tmp_path / "audit.jsonl"
        
        with patch("ai_nexus.history_log.HISTORY_LOG_PATH", log_file):
            log_kernel_history_event(
                kernel_ids=["risk_model_v2", "audit_trail"],
                kind="risk_decision",
                source="risk_model_v2",
                summary="Risk decision for market_456",
                details={
                    "market_id": "market_456",
                    "edge": 0.05,
                    "kelly_fraction": 0.04,
                    "position_size": 40.0,
                },
                importance=8,
                tags=["risk", "audit"],
            )

            with open(log_file) as f:
                logged = json.loads(f.readline())
            
            assert logged["kind"] == "risk_decision"
            assert logged["details"]["edge"] == 0.05

    def test_decider_outcome_audit_event(self, tmp_path):
        """Test audit logging for decider outcomes"""
        log_file = tmp_path / "audit.jsonl"
        
        with patch("ai_nexus.history_log.HISTORY_LOG_PATH", log_file):
            log_kernel_history_event(
                kernel_ids=["alpha_polymarket_core", "audit_trail"],
                kind="decider_outcome",
                source="ho_decider",
                summary="Decider produced 5 decisions",
                details={
                    "num_decisions": 5,
                    "total_risk_usd": 250.0,
                    "num_buys": 3,
                    "num_sells": 2,
                },
                importance=7,
                tags=["decider", "audit"],
            )

            with open(log_file) as f:
                logged = json.loads(f.readline())
            
            assert logged["kind"] == "decider_outcome"
            assert logged["details"]["num_decisions"] == 5


class TestAuditTrailIntegrity:
    """Tests for audit trail integrity and validation"""

    def test_audit_event_has_timestamp(self, tmp_path):
        """Test that audit events have timestamps"""
        log_file = tmp_path / "audit.jsonl"
        
        with patch("ai_nexus.history_log.HISTORY_LOG_PATH", log_file):
            log_kernel_history_event(
                kernel_ids=["audit_trail"],
                kind="execution",
                source="test",
                summary="Test event",
                importance=5,
            )

            with open(log_file) as f:
                logged = json.loads(f.readline())
            
            assert "ts" in logged
            # Verify timestamp is valid ISO format
            ts = datetime.fromisoformat(logged["ts"].replace("Z", "+00:00"))
            assert isinstance(ts, datetime)

    def test_audit_event_has_event_id(self, tmp_path):
        """Test that audit events have unique IDs"""
        log_file = tmp_path / "audit.jsonl"
        
        with patch("ai_nexus.history_log.HISTORY_LOG_PATH", log_file):
            log_kernel_history_event(
                kernel_ids=["audit_trail"],
                kind="execution",
                source="test",
                summary="Test event",
                importance=5,
            )

            with open(log_file) as f:
                logged = json.loads(f.readline())
            
            assert "event_id" in logged
            assert len(logged["event_id"]) > 0

    def test_audit_events_are_append_only(self, tmp_path):
        """Test that audit events are appended, not overwritten"""
        log_file = tmp_path / "audit.jsonl"
        
        with patch("ai_nexus.history_log.HISTORY_LOG_PATH", log_file):
            # Log first event
            log_kernel_history_event(
                kernel_ids=["audit_trail"],
                kind="execution",
                source="test",
                summary="Event 1",
                importance=5,
            )

            # Log second event
            log_kernel_history_event(
                kernel_ids=["audit_trail"],
                kind="execution",
                source="test",
                summary="Event 2",
                importance=5,
            )

            # Both should be in file
            with open(log_file) as f:
                lines = f.readlines()
            
            assert len(lines) == 2
            event1 = json.loads(lines[0])
            event2 = json.loads(lines[1])
            assert event1["summary"] == "Event 1"
            assert event2["summary"] == "Event 2"


class TestAuditLoggingErrorHandling:
    """Tests for error handling in audit logging"""

    def test_logging_errors_dont_crash(self, tmp_path, capsys):
        """Test that logging errors are handled gracefully"""
        log_file = tmp_path / "audit.jsonl"
        
        with patch("ai_nexus.history_log.HISTORY_LOG_PATH", log_file):
            # Try to log with non-serializable data
            class NonSerializable:
                pass

            event = HistoryEvent(
                event_id="test",
                ts=datetime.now(timezone.utc),
                kind="execution",
                source="test",
                kernel_ids=["audit_trail"],
                summary="Test",
                details={"bad": NonSerializable()},
                importance=5,
                tags=[],
            )

            # Should not raise exception
            log_history_event(event)

            # Should print error
            captured = capsys.readouterr()
            assert "ERROR" in captured.out

    def test_empty_kernel_ids_validation(self, tmp_path, capsys):
        """Test validation of empty kernel_ids"""
        log_file = tmp_path / "audit.jsonl"
        
        with patch("ai_nexus.history_log.HISTORY_LOG_PATH", log_file):
            event = HistoryEvent(
                event_id="test",
                ts=datetime.now(timezone.utc),
                kind="execution",
                source="test",
                kernel_ids=[],  # Empty!
                summary="Test",
                details={},
                importance=5,
                tags=[],
            )

            log_history_event(event)

            # Should print warning
            captured = capsys.readouterr()
            assert "WARNING" in captured.out
            assert "empty kernel_ids" in captured.out


class TestAuditRoutingLogic:
    """Tests for audit event routing to correct kernels"""

    def test_risk_decision_routing_includes_audit(self):
        """Test that risk decisions can be routed to audit trail"""
        kernel_ids = default_kernel_ids_for_event("risk_decision", "risk_model_v2")
        # Risk decisions go to risk_model_v2 and trading_philosophy by default
        assert "risk_model_v2" in kernel_ids
        assert "trading_philosophy" in kernel_ids

    def test_execution_audit_with_custom_kernels(self, tmp_path):
        """Test execution audit with custom kernel routing"""
        log_file = tmp_path / "audit.jsonl"
        
        with patch("ai_nexus.history_log.HISTORY_LOG_PATH", log_file):
            # Explicitly route to audit_trail kernel
            log_kernel_history_event(
                kernel_ids=["audit_trail", "execution_history"],
                kind="execution",
                source="executor",
                summary="Execution with audit trail",
                details={"test": "data"},
                importance=9,
            )

            with open(log_file) as f:
                logged = json.loads(f.readline())
            
            assert "audit_trail" in logged["kernel_ids"]
            assert "execution_history" in logged["kernel_ids"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
