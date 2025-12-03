"""
Unit tests for HistoryEvent (Part 3: User Expansion)

Tests the HistoryEvent data model from spark_plug_types.py
"""

import json
import pytest
from datetime import datetime

from ai_nexus.spark_plug_types import HistoryEvent, create_history_event


class TestHistoryEvent:
    """Test HistoryEvent data model"""

    def test_create_history_event_basic(self):
        """Test creating a basic HistoryEvent"""
        event = HistoryEvent(
            event_id="evt_001",
            timestamp="2025-11-26T10:00:00Z",
            event_type="user_message",
            source="user:froggy",
            content="What's the current Kelly fraction?"
        )

        assert event.event_id == "evt_001"
        assert event.timestamp == "2025-11-26T10:00:00Z"
        assert event.event_type == "user_message"
        assert event.source == "user:froggy"
        assert event.content == "What's the current Kelly fraction?"
        assert event.context == {}

    def test_create_history_event_with_context(self):
        """Test creating HistoryEvent with context metadata"""
        event = HistoryEvent(
            event_id="evt_002",
            timestamp="2025-11-26T10:01:00Z",
            event_type="system_decision",
            source="cpu_risk_01",
            content="Updated Kelly fraction to 0.15",
            context={
                "kernel_id": "risk_model_v2",
                "decision_id": "dec_001",
                "confidence": 0.85
            }
        )

        assert event.context["kernel_id"] == "risk_model_v2"
        assert event.context["decision_id"] == "dec_001"
        assert event.context["confidence"] == 0.85

    def test_create_history_event_helper(self):
        """Test create_history_event helper function"""
        event = create_history_event(
            event_type="user_message",
            source="user:froggy",
            content="Test message",
            kernel_id="test_kernel"
        )

        # Should auto-generate event_id and timestamp
        assert event.event_id.startswith("evt_")
        assert "T" in event.timestamp  # ISO 8601 format
        assert event.event_type == "user_message"
        assert event.source == "user:froggy"
        assert event.content == "Test message"
        assert event.context["kernel_id"] == "test_kernel"

    def test_create_history_event_with_custom_id(self):
        """Test create_history_event with custom event_id"""
        event = create_history_event(
            event_type="observation",
            source="manual",
            content="System is running smoothly",
            event_id="custom_001"
        )

        assert event.event_id == "custom_001"

    def test_to_dict(self):
        """Test converting HistoryEvent to dict"""
        event = HistoryEvent(
            event_id="evt_003",
            timestamp="2025-11-26T10:02:00Z",
            event_type="trade_outcome",
            source="executor_01",
            content="Trade executed successfully",
            context={"pnl": 125.50, "market": "polymarket"}
        )

        event_dict = event.to_dict()

        assert event_dict["event_id"] == "evt_003"
        assert event_dict["event_type"] == "trade_outcome"
        assert event_dict["source"] == "executor_01"
        assert event_dict["content"] == "Trade executed successfully"
        assert event_dict["context"]["pnl"] == 125.50

    def test_from_dict(self):
        """Test creating HistoryEvent from dict"""
        data = {
            "event_id": "evt_004",
            "timestamp": "2025-11-26T10:03:00Z",
            "event_type": "model_update",
            "source": "training_pipeline",
            "content": "Model retrained with new data",
            "context": {"accuracy": 0.92, "dataset_size": 1000}
        }

        event = HistoryEvent.from_dict(data)

        assert event.event_id == "evt_004"
        assert event.event_type == "model_update"
        assert event.context["accuracy"] == 0.92

    def test_to_jsonl_line(self):
        """Test converting HistoryEvent to JSONL line"""
        event = HistoryEvent(
            event_id="evt_005",
            timestamp="2025-11-26T10:04:00Z",
            event_type="cpu_conclusion",
            source="cpu_coordination_01",
            content="Consensus reached on strategy",
            context={"agents": ["chatgpt", "claude", "copilot"]}
        )

        jsonl_line = event.to_jsonl_line()

        # Should be valid JSON
        parsed = json.loads(jsonl_line)
        assert parsed["event_id"] == "evt_005"
        assert parsed["event_type"] == "cpu_conclusion"
        assert "agents" in parsed["context"]

    def test_from_jsonl_line(self):
        """Test parsing HistoryEvent from JSONL line"""
        jsonl_line = '{"event_id": "evt_006", "timestamp": "2025-11-26T10:05:00Z", "event_type": "manual_override", "source": "user:admin", "content": "Manual adjustment", "context": {"reason": "emergency"}}'

        event = HistoryEvent.from_jsonl_line(jsonl_line)

        assert event.event_id == "evt_006"
        assert event.event_type == "manual_override"
        assert event.source == "user:admin"
        assert event.context["reason"] == "emergency"

    def test_roundtrip_jsonl(self):
        """Test JSONL serialization roundtrip"""
        original = HistoryEvent(
            event_id="evt_007",
            timestamp="2025-11-26T10:06:00Z",
            event_type="observation",
            source="monitoring",
            content="All systems operational",
            context={"uptime": 99.9, "alerts": 0}
        )

        # Convert to JSONL and back
        jsonl_line = original.to_jsonl_line()
        restored = HistoryEvent.from_jsonl_line(jsonl_line)

        # Should match original
        assert restored.event_id == original.event_id
        assert restored.timestamp == original.timestamp
        assert restored.event_type == original.event_type
        assert restored.source == original.source
        assert restored.content == original.content
        assert restored.context == original.context

    def test_all_event_types(self):
        """Test all valid event types"""
        valid_types = [
            "user_message",
            "system_decision",
            "trade_outcome",
            "model_update",
            "manual_override",
            "cpu_conclusion",
            "observation",
            "other"
        ]

        for event_type in valid_types:
            event = create_history_event(
                event_type=event_type,
                source="test",
                content=f"Test {event_type}"
            )
            assert event.event_type == event_type

    def test_empty_context(self):
        """Test HistoryEvent with empty context"""
        event = HistoryEvent(
            event_id="evt_008",
            timestamp="2025-11-26T10:07:00Z",
            event_type="other",
            source="test",
            content="No context"
        )

        assert event.context == {}

    def test_complex_context(self):
        """Test HistoryEvent with complex nested context"""
        event = HistoryEvent(
            event_id="evt_009",
            timestamp="2025-11-26T10:08:00Z",
            event_type="system_decision",
            source="cpu_alpha_01",
            content="Multi-factor decision",
            context={
                "factors": ["momentum", "volatility", "sentiment"],
                "weights": {"momentum": 0.4, "volatility": 0.3, "sentiment": 0.3},
                "metadata": {
                    "model_version": "v2.1",
                    "confidence": 0.88
                }
            }
        )

        assert len(event.context["factors"]) == 3
        assert event.context["weights"]["momentum"] == 0.4
        assert event.context["metadata"]["model_version"] == "v2.1"

        # Should survive roundtrip
        jsonl_line = event.to_jsonl_line()
        restored = HistoryEvent.from_jsonl_line(jsonl_line)
        assert restored.context == event.context


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
