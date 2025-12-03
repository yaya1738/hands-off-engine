"""
Unit tests for Spark Plug History Bridge

Tests the unified history loader that reads from both:
  - ai/history/events.jsonl (new format)
  - ai/history/user_events.jsonl (legacy format)
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from ai_nexus import spark_plug_history


@pytest.fixture
def temp_history_dirs(monkeypatch):
    """Create temporary directories for history testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        history_dir = temp_path / "history"
        history_dir.mkdir()

        new_history_file = history_dir / "events.jsonl"
        legacy_history_file = history_dir / "user_events.jsonl"

        # Override paths in spark_plug_history module
        monkeypatch.setattr(spark_plug_history, "REPO_ROOT", temp_path)
        monkeypatch.setattr(spark_plug_history, "NEW_HISTORY_FILE", new_history_file)
        monkeypatch.setattr(spark_plug_history, "LEGACY_HISTORY_FILE", legacy_history_file)

        yield {
            "history_dir": history_dir,
            "new_file": new_history_file,
            "legacy_file": legacy_history_file
        }


class TestLoadFromNewFormat:
    """Test loading from new events.jsonl format"""

    def test_load_new_format_no_file(self, temp_history_dirs):
        """Test loading when new format file doesn't exist"""
        events = spark_plug_history.load_from_new_format("risk_model_v2")
        assert events == []

    def test_load_new_format_basic(self, temp_history_dirs):
        """Test loading basic events from new format"""
        # Create sample events
        events_data = [
            {
                "event_id": "evt-001",
                "ts": "2025-11-26T10:00:00Z",
                "kind": "risk_decision",
                "source": "risk_model_v2",
                "kernel_ids": ["risk_model_v2", "trading_philosophy"],
                "summary": "Kelly fraction updated to 0.20",
                "details": {"kelly": 0.20},
                "importance": 8,
                "tags": ["risk", "kelly"]
            },
            {
                "event_id": "evt-002",
                "ts": "2025-11-26T11:00:00Z",
                "kind": "decider_outcome",
                "source": "ho_decider",
                "kernel_ids": ["alpha_polymarket_core"],
                "summary": "Decider produced 3 decisions",
                "details": {"num_decisions": 3},
                "importance": 7,
                "tags": ["decider"]
            },
            {
                "event_id": "evt-003",
                "ts": "2025-11-26T12:00:00Z",
                "kind": "risk_decision",
                "source": "risk_model_v2",
                "kernel_ids": ["risk_model_v2"],
                "summary": "Position cap increased",
                "details": {"cap": 5000},
                "importance": 6,
                "tags": ["risk", "caps"]
            }
        ]

        # Write to file
        with open(temp_history_dirs["new_file"], 'w') as f:
            for event in events_data:
                f.write(json.dumps(event) + '\n')

        # Load events for risk_model_v2
        loaded = spark_plug_history.load_from_new_format("risk_model_v2")

        # Should get 2 events (evt-001 and evt-003)
        assert len(loaded) == 2
        assert loaded[0]["event_id"] == "evt-003"  # Newest first
        assert loaded[1]["event_id"] == "evt-001"

    def test_load_new_format_with_importance_filter(self, temp_history_dirs):
        """Test importance filtering"""
        events_data = [
            {
                "event_id": "evt-high",
                "ts": "2025-11-26T10:00:00Z",
                "kind": "risk_decision",
                "source": "risk_model_v2",
                "kernel_ids": ["risk_model_v2"],
                "summary": "High importance event",
                "details": {},
                "importance": 9,
                "tags": []
            },
            {
                "event_id": "evt-low",
                "ts": "2025-11-26T11:00:00Z",
                "kind": "observation",
                "source": "monitoring",
                "kernel_ids": ["risk_model_v2"],
                "summary": "Low importance event",
                "details": {},
                "importance": 3,
                "tags": []
            }
        ]

        with open(temp_history_dirs["new_file"], 'w') as f:
            for event in events_data:
                f.write(json.dumps(event) + '\n')

        # Load with min_importance=6
        loaded = spark_plug_history.load_from_new_format(
            "risk_model_v2",
            min_importance=6
        )

        # Should only get high importance event
        assert len(loaded) == 1
        assert loaded[0]["event_id"] == "evt-high"

    def test_load_new_format_with_max_events(self, temp_history_dirs):
        """Test max_events limiting"""
        events_data = [
            {
                "event_id": f"evt-{i:03d}",
                "ts": f"2025-11-26T{i:02d}:00:00Z",
                "kind": "observation",
                "source": "test",
                "kernel_ids": ["test_kernel"],
                "summary": f"Event {i}",
                "details": {},
                "importance": 5,
                "tags": []
            }
            for i in range(10)
        ]

        with open(temp_history_dirs["new_file"], 'w') as f:
            for event in events_data:
                f.write(json.dumps(event) + '\n')

        # Load with max_events=3
        loaded = spark_plug_history.load_from_new_format(
            "test_kernel",
            max_events=3
        )

        assert len(loaded) == 3
        # Should be newest 3
        assert loaded[0]["event_id"] == "evt-009"
        assert loaded[1]["event_id"] == "evt-008"
        assert loaded[2]["event_id"] == "evt-007"

    def test_load_new_format_malformed_lines(self, temp_history_dirs):
        """Test handling of malformed JSON lines"""
        with open(temp_history_dirs["new_file"], 'w') as f:
            f.write('{"valid": "event", "event_id": "evt-001", "ts": "2025-11-26T10:00:00Z", "kernel_ids": ["test"], "summary": "Test", "details": {}}\n')
            f.write('{invalid json\n')  # Malformed
            f.write('{"valid": "event2", "event_id": "evt-002", "ts": "2025-11-26T11:00:00Z", "kernel_ids": ["test"], "summary": "Test2", "details": {}}\n')

        loaded = spark_plug_history.load_from_new_format("test")

        # Should skip malformed line and return 2 valid events
        assert len(loaded) == 2


class TestLoadFromLegacyFormat:
    """Test loading from legacy user_events.jsonl format"""

    def test_load_legacy_format_no_file(self, temp_history_dirs):
        """Test loading when legacy format file doesn't exist"""
        events = spark_plug_history.load_from_legacy_format("risk_model_v2")
        assert events == []

    def test_load_legacy_format_basic(self, temp_history_dirs):
        """Test loading basic events from legacy format"""
        legacy_events = [
            {
                "event_id": "leg-001",
                "timestamp": "2025-11-26T10:00:00Z",
                "event_type": "user_message",
                "source": "user:yair",
                "content": "What is the current Kelly fraction?",
                "context": {"kernel_id": "risk_model_v2"}
            },
            {
                "event_id": "leg-002",
                "timestamp": "2025-11-26T11:00:00Z",
                "event_type": "system_decision",
                "source": "cpu_risk_01",
                "content": "Updated Kelly to 0.15",
                "context": {"kernel_id": "trading_philosophy"}
            },
            {
                "event_id": "leg-003",
                "timestamp": "2025-11-26T12:00:00Z",
                "event_type": "observation",
                "source": "monitoring",
                "content": "System healthy",
                "context": {}  # No kernel_id (general event)
            }
        ]

        with open(temp_history_dirs["legacy_file"], 'w') as f:
            for event in legacy_events:
                f.write(json.dumps(event) + '\n')

        # Load events for risk_model_v2
        loaded = spark_plug_history.load_from_legacy_format("risk_model_v2")

        # Should only get leg-001 (strict filtering - no general events)
        assert len(loaded) == 1

        # Check normalization
        assert loaded[0]["event_id"] == "leg-001"  # Only risk_model_v2 event
        assert loaded[0]["kind"] == "user_message"
        assert loaded[0]["summary"] == "What is the current Kelly fraction?"
        assert loaded[0]["importance"] is None

    def test_normalize_legacy_event(self, temp_history_dirs):
        """Test normalization of legacy event format"""
        legacy_event = {
            "event_id": "leg-001",
            "timestamp": "2025-11-26T10:00:00Z",
            "event_type": "user_message",
            "source": "user:yair",
            "content": "Test content",
            "context": {
                "kernel_id": "risk_model_v2",
                "extra_field": "extra_value"
            }
        }

        normalized = spark_plug_history.normalize_legacy_event(legacy_event)

        assert normalized["event_id"] == "leg-001"
        assert normalized["ts"] == "2025-11-26T10:00:00Z"
        assert normalized["kind"] == "user_message"
        assert normalized["source"] == "user:yair"
        assert normalized["kernel_ids"] == ["risk_model_v2"]
        assert normalized["summary"] == "Test content"
        assert normalized["details"]["kernel_id"] == "risk_model_v2"
        assert normalized["details"]["extra_field"] == "extra_value"
        assert normalized["importance"] is None
        assert normalized["tags"] == []


class TestUnifiedLoader:
    """Test the unified load_kernel_history_events function"""

    def test_prefers_new_format(self, temp_history_dirs):
        """Test that new format is preferred over legacy"""
        # Create both files
        new_event = {
            "event_id": "new-001",
            "ts": "2025-11-26T10:00:00Z",
            "kind": "risk_decision",
            "source": "risk_model_v2",
            "kernel_ids": ["risk_model_v2"],
            "summary": "New format event",
            "details": {},
            "importance": 8,
            "tags": []
        }

        legacy_event = {
            "event_id": "leg-001",
            "timestamp": "2025-11-26T11:00:00Z",
            "event_type": "user_message",
            "source": "user",
            "content": "Legacy format event",
            "context": {"kernel_id": "risk_model_v2"}
        }

        with open(temp_history_dirs["new_file"], 'w') as f:
            f.write(json.dumps(new_event) + '\n')

        with open(temp_history_dirs["legacy_file"], 'w') as f:
            f.write(json.dumps(legacy_event) + '\n')

        # Load events
        loaded = spark_plug_history.load_kernel_history_events("risk_model_v2")

        # Should get new format event only
        assert len(loaded) == 1
        assert loaded[0]["event_id"] == "new-001"

    def test_falls_back_to_legacy(self, temp_history_dirs):
        """Test fallback to legacy format when new format is empty"""
        # Only create legacy file
        legacy_event = {
            "event_id": "leg-001",
            "timestamp": "2025-11-26T10:00:00Z",
            "event_type": "system_decision",
            "source": "cpu",
            "content": "Legacy event",
            "context": {"kernel_id": "risk_model_v2"}
        }

        with open(temp_history_dirs["legacy_file"], 'w') as f:
            f.write(json.dumps(legacy_event) + '\n')

        # Load events
        loaded = spark_plug_history.load_kernel_history_events("risk_model_v2")

        # Should get legacy event
        assert len(loaded) == 1
        assert loaded[0]["event_id"] == "leg-001"
        assert loaded[0]["kind"] == "system_decision"

    def test_returns_empty_list_when_no_files(self, temp_history_dirs):
        """Test that empty list is returned when no history files exist"""
        loaded = spark_plug_history.load_kernel_history_events("risk_model_v2")
        assert loaded == []

    def test_with_max_events_param(self, temp_history_dirs):
        """Test max_events parameter"""
        events = [
            {
                "event_id": f"evt-{i}",
                "ts": f"2025-11-26T{i:02d}:00:00Z",
                "kind": "observation",
                "source": "test",
                "kernel_ids": ["test_kernel"],
                "summary": f"Event {i}",
                "details": {},
                "importance": 5,
                "tags": []
            }
            for i in range(10)
        ]

        with open(temp_history_dirs["new_file"], 'w') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')

        loaded = spark_plug_history.load_kernel_history_events(
            "test_kernel",
            max_events=5
        )

        assert len(loaded) == 5


class TestGetHistoryStats:
    """Test get_history_stats function"""

    def test_stats_with_new_format_only(self, temp_history_dirs):
        """Test stats when only new format has events"""
        new_event = {
            "event_id": "new-001",
            "ts": "2025-11-26T10:00:00Z",
            "kind": "risk_decision",
            "source": "risk_model_v2",
            "kernel_ids": ["risk_model_v2"],
            "summary": "Test",
            "details": {},
            "importance": 8,
            "tags": []
        }

        with open(temp_history_dirs["new_file"], 'w') as f:
            f.write(json.dumps(new_event) + '\n')

        stats = spark_plug_history.get_history_stats("risk_model_v2")

        assert stats["new_format_events"] == 1
        assert stats["legacy_format_events"] == 0
        assert stats["total_events"] == 1
        assert stats["using_format"] == "new"

    def test_stats_with_legacy_format_only(self, temp_history_dirs):
        """Test stats when only legacy format has events"""
        legacy_event = {
            "event_id": "leg-001",
            "timestamp": "2025-11-26T10:00:00Z",
            "event_type": "user_message",
            "source": "user",
            "content": "Test",
            "context": {"kernel_id": "risk_model_v2"}
        }

        with open(temp_history_dirs["legacy_file"], 'w') as f:
            f.write(json.dumps(legacy_event) + '\n')

        stats = spark_plug_history.get_history_stats("risk_model_v2")

        assert stats["new_format_events"] == 0
        assert stats["legacy_format_events"] == 1
        assert stats["total_events"] == 1
        assert stats["using_format"] == "legacy"

    def test_stats_with_no_events(self, temp_history_dirs):
        """Test stats when no events exist"""
        stats = spark_plug_history.get_history_stats("risk_model_v2")

        assert stats["new_format_events"] == 0
        assert stats["legacy_format_events"] == 0
        assert stats["total_events"] == 0
        assert stats["using_format"] == "none"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
