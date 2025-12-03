"""
Unit tests for history_logger module (Part 3: User Expansion)

Tests append-only history logging system.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from ai_nexus.spark_plug_types import HistoryEvent, create_history_event
from ai_nexus import history_logger


@pytest.fixture
def temp_history_dir(monkeypatch):
    """Create temporary directory for history file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override HISTORY_FILE path
        temp_history_file = Path(tmpdir) / "user_events.jsonl"
        monkeypatch.setattr(history_logger, "HISTORY_FILE", temp_history_file)
        yield temp_history_file


class TestHistoryLogger:
    """Test history logging functions"""

    def test_append_history_event(self, temp_history_dir):
        """Test appending a history event"""
        event = create_history_event(
            event_type="user_message",
            source="user:test",
            content="Test message"
        )

        history_logger.append_history_event(event)

        # File should exist
        assert temp_history_dir.exists()

        # Read and verify
        with open(temp_history_dir) as f:
            lines = f.readlines()

        assert len(lines) == 1

        parsed = json.loads(lines[0])
        assert parsed["event_type"] == "user_message"
        assert parsed["content"] == "Test message"

    def test_append_multiple_events(self, temp_history_dir):
        """Test appending multiple events"""
        events = [
            create_history_event(
                event_type="user_message",
                source="user:test",
                content=f"Message {i}"
            )
            for i in range(5)
        ]

        for event in events:
            history_logger.append_history_event(event)

        # Should have 5 lines
        with open(temp_history_dir) as f:
            lines = f.readlines()

        assert len(lines) == 5

    def test_load_history_events_empty(self, temp_history_dir):
        """Test loading from empty history"""
        events = history_logger.load_history_events()
        assert events == []

    def test_load_history_events(self, temp_history_dir):
        """Test loading history events"""
        # Append 3 events
        for i in range(3):
            event = create_history_event(
                event_type="observation",
                source="test",
                content=f"Event {i}"
            )
            history_logger.append_history_event(event)

        # Load all
        events = history_logger.load_history_events()

        assert len(events) == 3
        # Should be in reverse order (newest first)
        assert "Event 2" in events[0].content
        assert "Event 1" in events[1].content
        assert "Event 0" in events[2].content

    def test_load_history_events_with_limit(self, temp_history_dir):
        """Test loading with limit"""
        # Append 10 events
        for i in range(10):
            event = create_history_event(
                event_type="observation",
                source="test",
                content=f"Event {i}"
            )
            history_logger.append_history_event(event)

        # Load only last 5
        events = history_logger.load_history_events(limit=5)

        assert len(events) == 5
        # Should be most recent
        assert "Event 9" in events[0].content
        assert "Event 5" in events[4].content

    def test_load_history_events_with_offset(self, temp_history_dir):
        """Test loading with offset"""
        # Append 10 events
        for i in range(10):
            event = create_history_event(
                event_type="observation",
                source="test",
                content=f"Event {i}"
            )
            history_logger.append_history_event(event)

        # Skip first 3, get next 5
        events = history_logger.load_history_events(offset=3, limit=5)

        assert len(events) == 5
        # Should skip 3 newest (9, 8, 7) and get (6, 5, 4, 3, 2)
        assert "Event 6" in events[0].content
        assert "Event 2" in events[4].content

    def test_load_history_events_by_type(self, temp_history_dir):
        """Test filtering by event type"""
        # Append mixed event types
        for i in range(5):
            event = create_history_event(
                event_type="user_message",
                source="user:test",
                content=f"User message {i}"
            )
            history_logger.append_history_event(event)

        for i in range(3):
            event = create_history_event(
                event_type="system_decision",
                source="cpu_test",
                content=f"System decision {i}"
            )
            history_logger.append_history_event(event)

        # Load only user messages
        user_events = history_logger.load_history_events(event_type="user_message")
        assert len(user_events) == 5
        assert all(e.event_type == "user_message" for e in user_events)

        # Load only system decisions
        system_events = history_logger.load_history_events(event_type="system_decision")
        assert len(system_events) == 3
        assert all(e.event_type == "system_decision" for e in system_events)

    def test_count_history_events(self, temp_history_dir):
        """Test counting events"""
        # Start with 0
        assert history_logger.count_history_events() == 0

        # Add 7 events
        for i in range(7):
            event = create_history_event(
                event_type="observation",
                source="test",
                content=f"Event {i}"
            )
            history_logger.append_history_event(event)

        assert history_logger.count_history_events() == 7

    def test_count_history_events_by_type(self, temp_history_dir):
        """Test counting by event type"""
        # Add mixed types
        for i in range(4):
            history_logger.append_history_event(
                create_history_event(
                    event_type="user_message",
                    source="user",
                    content="Message"
                )
            )

        for i in range(6):
            history_logger.append_history_event(
                create_history_event(
                    event_type="system_decision",
                    source="cpu",
                    content="Decision"
                )
            )

        assert history_logger.count_history_events() == 10
        assert history_logger.count_history_events(event_type="user_message") == 4
        assert history_logger.count_history_events(event_type="system_decision") == 6

    def test_get_event_types(self, temp_history_dir):
        """Test getting all event types"""
        # Start empty
        assert history_logger.get_event_types() == []

        # Add various types
        types_to_add = ["user_message", "system_decision", "observation"]
        for event_type in types_to_add:
            history_logger.append_history_event(
                create_history_event(
                    event_type=event_type,
                    source="test",
                    content="Test"
                )
            )

        event_types = history_logger.get_event_types()
        assert len(event_types) == 3
        assert "user_message" in event_types
        assert "system_decision" in event_types
        assert "observation" in event_types

    def test_get_history_stats(self, temp_history_dir):
        """Test getting history statistics"""
        # Empty stats
        stats = history_logger.get_history_stats()
        assert stats["total_events"] == 0
        assert stats["oldest_timestamp"] is None
        assert stats["newest_timestamp"] is None

        # Add some events
        event1 = create_history_event(
            event_type="user_message",
            source="user",
            content="First"
        )
        event1.timestamp = "2025-11-26T10:00:00Z"
        history_logger.append_history_event(event1)

        event2 = create_history_event(
            event_type="system_decision",
            source="cpu",
            content="Second"
        )
        event2.timestamp = "2025-11-26T10:05:00Z"
        history_logger.append_history_event(event2)

        stats = history_logger.get_history_stats()
        assert stats["total_events"] == 2
        assert stats["event_types"]["user_message"] == 1
        assert stats["event_types"]["system_decision"] == 1
        assert stats["oldest_timestamp"] == "2025-11-26T10:00:00Z"
        assert stats["newest_timestamp"] == "2025-11-26T10:05:00Z"

    def test_clear_history(self, temp_history_dir):
        """Test clearing history"""
        # Add events
        for i in range(5):
            history_logger.append_history_event(
                create_history_event(
                    event_type="observation",
                    source="test",
                    content=f"Event {i}"
                )
            )

        assert history_logger.count_history_events() == 5

        # Clear with confirm
        history_logger.clear_history(confirm=True)

        # Should be empty
        assert not temp_history_dir.exists()
        assert history_logger.count_history_events() == 0

    def test_clear_history_requires_confirm(self, temp_history_dir):
        """Test that clear_history requires confirmation"""
        # Add event
        history_logger.append_history_event(
            create_history_event(
                event_type="observation",
                source="test",
                content="Test"
            )
        )

        # Should raise error without confirm
        with pytest.raises(ValueError, match="Must pass confirm=True"):
            history_logger.clear_history(confirm=False)

        # Event should still exist
        assert history_logger.count_history_events() == 1

    def test_malformed_jsonl_handling(self, temp_history_dir):
        """Test handling of malformed JSONL lines"""
        # Write good event
        good_event = create_history_event(
            event_type="observation",
            source="test",
            content="Good"
        )
        history_logger.append_history_event(good_event)

        # Manually append malformed line
        with open(temp_history_dir, 'a') as f:
            f.write("This is not valid JSON\n")

        # Write another good event
        good_event2 = create_history_event(
            event_type="observation",
            source="test",
            content="Good 2"
        )
        history_logger.append_history_event(good_event2)

        # Load should skip malformed line
        events = history_logger.load_history_events()
        assert len(events) == 2
        assert "Good 2" in events[0].content
        assert "Good" in events[1].content

    def test_directory_creation(self, temp_history_dir):
        """Test that append creates directory if needed"""
        # Ensure parent doesn't exist
        if temp_history_dir.parent.exists():
            temp_history_dir.parent.rmdir()

        # Append should create it
        event = create_history_event(
            event_type="observation",
            source="test",
            content="Test"
        )
        history_logger.append_history_event(event)

        assert temp_history_dir.parent.exists()
        assert temp_history_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
