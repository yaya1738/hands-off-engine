#!/usr/bin/env python3
"""
Unit tests for audit logging system
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "audit"))

from audit_logger import AuditLogger, AuditEvent


class TestAuditLogger(unittest.TestCase):
    """Test suite for AuditLogger"""

    def setUp(self):
        """Create temporary directory for test logs"""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = AuditLogger(log_dir=self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_log_event(self):
        """Test logging an event"""
        event = self.logger.log_event(
            component="test.component",
            action="test_action",
            metadata={"key": "value"},
            cost=10.0,
            revenue=20.0
        )

        self.assertIsInstance(event, AuditEvent)
        self.assertEqual(event.component, "test.component")
        self.assertEqual(event.action, "test_action")
        self.assertEqual(event.cost, 10.0)
        self.assertEqual(event.revenue, 20.0)

    def test_get_all_sessions(self):
        """Test getting all session IDs"""
        # Create events in different sessions
        session1 = self.logger.session_id
        self.logger.log_event("comp1", "action1")
        
        # Create a new logger with a different session
        logger2 = AuditLogger(log_dir=self.temp_dir)
        session2 = logger2.session_id
        logger2.log_event("comp2", "action2")

        # Get all sessions
        sessions = self.logger.get_all_sessions()
        
        self.assertEqual(len(sessions), 2)
        self.assertIn(session1, sessions)
        self.assertIn(session2, sessions)

    def test_get_session_summary(self):
        """Test getting session summary"""
        # Log some events
        self.logger.log_event(
            component="test.component",
            action="action1",
            cost=10.0,
            revenue=30.0
        )
        self.logger.log_event(
            component="test.component",
            action="action2",
            cost=5.0,
            revenue=15.0
        )

        # Get summary
        summary = self.logger.get_session_summary()
        
        self.assertEqual(summary["session_id"], self.logger.session_id)
        self.assertEqual(summary["total_events"], 2)
        self.assertEqual(summary["total_cost"], 15.0)
        self.assertEqual(summary["total_revenue"], 45.0)
        self.assertEqual(summary["net_profit"], 30.0)

    def test_get_events_by_session(self):
        """Test filtering events by session"""
        # Log event in current session
        self.logger.log_event("comp1", "action1")
        
        # Create new session and log event
        logger2 = AuditLogger(log_dir=self.temp_dir)
        logger2.log_event("comp2", "action2")

        # Get events for first session only
        events = self.logger.get_events(session_id=self.logger.session_id)
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].component, "comp1")

    def test_component_stats(self):
        """Test component statistics in session summary"""
        # Log events for different components
        self.logger.log_event("comp1", "action1", cost=10.0)
        self.logger.log_event("comp1", "action2", revenue=20.0)
        self.logger.log_event("comp2", "action3", cost=5.0, error="test error")

        # Get summary
        summary = self.logger.get_session_summary()
        
        self.assertIn("comp1", summary["component_stats"])
        self.assertIn("comp2", summary["component_stats"])
        
        comp1_stats = summary["component_stats"]["comp1"]
        self.assertEqual(comp1_stats["event_count"], 2)
        self.assertEqual(comp1_stats["cost"], 10.0)
        self.assertEqual(comp1_stats["revenue"], 20.0)
        self.assertEqual(comp1_stats["errors"], 0)
        
        comp2_stats = summary["component_stats"]["comp2"]
        self.assertEqual(comp2_stats["errors"], 1)


if __name__ == "__main__":
    unittest.main()
