#!/usr/bin/env python3
"""
Test suite for enhanced handoff system

Tests:
- Handoff creation with validation
- State transitions
- Timeout detection
- Retry logic
- Metrics calculation
- Agent capability matching
- Dependency resolution
"""

import json
import time
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import tempfile
import shutil

# Add parent to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from ai.coordination.handoff_manager import HandoffManager, HandoffStatus, HandoffPriority, HandoffTask, Handoff


class TestHandoffSystem(unittest.TestCase):
    """Test enhanced handoff system"""
    
    def setUp(self):
        """Set up test environment with temp directory"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.coord_dir = self.test_dir / "ai" / "coordination"
        self.coord_dir.mkdir(parents=True, exist_ok=True)
        
        # Monkey patch paths for testing
        import ai.coordination.handoff_manager as hm
        hm.COORD_DIR = self.coord_dir
        hm.HANDOFF_FILE = self.coord_dir / "handoffs.json"
        hm.HANDOFF_LOG = self.coord_dir / "handoff_history.jsonl"
        hm.HANDOFF_METRICS = self.coord_dir / "handoff_metrics.json"
        
        self.manager = HandoffManager()
        self.manager.handoff_file = hm.HANDOFF_FILE
        self.manager.handoff_log = hm.HANDOFF_LOG
        self.manager.metrics_file = hm.HANDOFF_METRICS
    
    def tearDown(self):
        """Clean up test directory"""
        shutil.rmtree(self.test_dir)
    
    def test_create_valid_handoff(self):
        """Test creating a valid handoff"""
        result = self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="copilot",
            task={
                "type": "code_review",
                "description": "Review trading module",
                "requirements": ["code_review"]
            },
            priority="high"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("handoff_id", result)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["priority"], "high")
    
    def test_create_invalid_agent(self):
        """Test creating handoff with invalid target agent"""
        result = self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="unknown-agent",
            task={
                "type": "code_review",
                "description": "Test"
            }
        )
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("Unknown target agent", result["error"])
    
    def test_capability_mismatch(self):
        """Test handoff with capability mismatch"""
        result = self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="chatgpt",  # chatgpt can't do code_review
            task={
                "type": "code_review",
                "description": "Review code",
                "requirements": ["code_review"]
            }
        )
        
        self.assertFalse(result["success"])
        self.assertIn("cannot accept", result["error"])
    
    def test_handoff_lifecycle(self):
        """Test complete handoff lifecycle"""
        # Create
        result = self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="copilot",
            task={
                "type": "code_review",
                "description": "Review code",
                "requirements": ["code_review"]
            }
        )
        handoff_id = result["handoff_id"]
        
        # Accept
        result = self.manager.accept_handoff(handoff_id, "copilot")
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "accepted")
        
        # Start
        result = self.manager.start_handoff(handoff_id, "copilot")
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "in_progress")
        
        # Complete
        result = self.manager.complete_handoff(handoff_id, "copilot", {"status": "done"})
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "completed")
    
    def test_handoff_failure_and_retry(self):
        """Test handoff failure with retry"""
        # Create
        result = self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="copilot",
            task={
                "type": "code_review",
                "description": "Review code",
                "requirements": ["code_review"]
            }
        )
        handoff_id = result["handoff_id"]
        
        # Accept and start
        self.manager.accept_handoff(handoff_id, "copilot")
        self.manager.start_handoff(handoff_id, "copilot")
        
        # Fail with retry
        result = self.manager.fail_handoff(handoff_id, "copilot", "Test error", retry=True)
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "pending")  # Back to pending for retry
        self.assertEqual(result["retry_count"], 1)
    
    def test_handoff_max_retries(self):
        """Test handoff fails permanently after max retries"""
        # Create
        result = self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="copilot",
            task={
                "type": "code_review",
                "description": "Review code",
                "requirements": ["code_review"]
            }
        )
        handoff_id = result["handoff_id"]
        
        # Fail multiple times
        for i in range(3):
            self.manager.accept_handoff(handoff_id, "copilot")
            self.manager.start_handoff(handoff_id, "copilot")
            self.manager.fail_handoff(handoff_id, "copilot", "Error", retry=True)
        
        # Final failure
        self.manager.accept_handoff(handoff_id, "copilot")
        self.manager.start_handoff(handoff_id, "copilot")
        result = self.manager.fail_handoff(handoff_id, "copilot", "Final error", retry=True)
        
        self.assertEqual(result["status"], "failed")  # Permanently failed
    
    def test_handoff_cancellation(self):
        """Test handoff cancellation"""
        # Create
        result = self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="copilot",
            task={
                "type": "code_review",
                "description": "Review code",
                "requirements": ["code_review"]
            }
        )
        handoff_id = result["handoff_id"]
        
        # Cancel
        result = self.manager.cancel_handoff(handoff_id, "claude-code", "No longer needed")
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "cancelled")
    
    def test_get_pending_handoffs(self):
        """Test getting pending handoffs"""
        # Create multiple handoffs
        self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="copilot",
            task={"type": "code_review", "description": "Review 1", "requirements": ["code_review"]}
        )
        
        self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="chatgpt",
            task={"type": "research", "description": "Research 1", "requirements": ["research"]}
        )
        
        # Get all pending
        all_pending = self.manager.get_pending_handoffs()
        self.assertEqual(len(all_pending), 2)
        
        # Get copilot's pending
        copilot_pending = self.manager.get_pending_handoffs("copilot")
        self.assertEqual(len(copilot_pending), 1)
        self.assertEqual(copilot_pending[0]["to_agent"], "copilot")
    
    def test_dependency_resolution(self):
        """Test dependency checking"""
        # Create first handoff
        result1 = self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="chatgpt",
            task={"type": "research", "description": "Research", "requirements": ["research"]}
        )
        dep_id = result1["handoff_id"]
        
        # Try to create dependent handoff (should fail - dependency not complete)
        result2 = self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="copilot",
            task={"type": "code_review", "description": "Review", "requirements": ["code_review"]},
            dependencies=[dep_id]
        )
        
        self.assertFalse(result2["success"])
        self.assertIn("dependencies", result2["error"].lower())
        
        # Complete dependency
        self.manager.accept_handoff(dep_id, "chatgpt")
        self.manager.start_handoff(dep_id, "chatgpt")
        self.manager.complete_handoff(dep_id, "chatgpt")
        
        # Now dependent handoff should succeed
        result3 = self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="copilot",
            task={"type": "code_review", "description": "Review", "requirements": ["code_review"]},
            dependencies=[dep_id]
        )
        
        self.assertTrue(result3["success"])
    
    def test_timeout_detection(self):
        """Test timeout detection"""
        # Create handoff with short timeout
        result = self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="copilot",
            task={"type": "code_review", "description": "Review", "requirements": ["code_review"]},
            timeout_minutes=0  # Instant timeout for testing
        )
        handoff_id = result["handoff_id"]
        
        # Check for timeouts
        timed_out = self.manager.check_timeouts()
        
        self.assertEqual(len(timed_out), 1)
        self.assertEqual(timed_out[0]["id"], handoff_id)
        self.assertEqual(timed_out[0]["status"], "timeout")
    
    def test_metrics_calculation(self):
        """Test metrics calculation"""
        # Create and complete some handoffs
        for i in range(5):
            result = self.manager.create_handoff(
                from_agent="claude-code",
                to_agent="copilot",
                task={"type": "code_review", "description": f"Review {i}", "requirements": ["code_review"]}
            )
            handoff_id = result["handoff_id"]
            
            # Complete 4 out of 5
            if i < 4:
                self.manager.accept_handoff(handoff_id, "copilot")
                self.manager.start_handoff(handoff_id, "copilot")
                self.manager.complete_handoff(handoff_id, "copilot")
        
        # Get metrics
        metrics = self.manager.get_metrics()
        
        self.assertEqual(metrics["total_handoffs"], 5)
        self.assertEqual(metrics["by_status"]["completed"], 4)
        self.assertEqual(metrics["by_status"]["pending"], 1)
        self.assertEqual(metrics["completion_rate"], 0.80)  # 4/5 = 80%
    
    def test_priority_ordering(self):
        """Test that pending handoffs are ordered by priority"""
        # Create handoffs with different priorities
        self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="copilot",
            task={"type": "code_review", "description": "Low", "requirements": ["code_review"]},
            priority="low"
        )
        
        self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="copilot",
            task={"type": "code_review", "description": "Critical", "requirements": ["code_review"]},
            priority="critical"
        )
        
        self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="copilot",
            task={"type": "code_review", "description": "Normal", "requirements": ["code_review"]},
            priority="normal"
        )
        
        # Get pending
        pending = self.manager.get_pending_handoffs("copilot")
        
        # Should be ordered: critical, normal, low
        self.assertEqual(pending[0]["priority"], "critical")
        self.assertEqual(pending[1]["priority"], "normal")
        self.assertEqual(pending[2]["priority"], "low")
    
    def test_notes_tracking(self):
        """Test that notes are tracked on handoffs"""
        # Create handoff
        result = self.manager.create_handoff(
            from_agent="claude-code",
            to_agent="copilot",
            task={"type": "code_review", "description": "Review", "requirements": ["code_review"]}
        )
        handoff_id = result["handoff_id"]
        
        # Accept (adds note)
        self.manager.accept_handoff(handoff_id, "copilot")
        
        # Get handoff and check notes
        handoff = self.manager._get_handoff(handoff_id)
        self.assertGreater(len(handoff.notes), 0)
        self.assertEqual(handoff.notes[0]["author"], "copilot")
        self.assertIn("Accepted", handoff.notes[0]["message"])


class TestHandoffHealthMonitor(unittest.TestCase):
    """Test handoff health monitoring"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.coord_dir = self.test_dir / "ai" / "coordination"
        self.coord_dir.mkdir(parents=True, exist_ok=True)
        
        # Monkey patch
        import ai.coordination.handoff_manager as hm
        hm.COORD_DIR = self.coord_dir
        hm.HANDOFF_FILE = self.coord_dir / "handoffs.json"
        hm.HANDOFF_LOG = self.coord_dir / "handoff_history.jsonl"
        hm.HANDOFF_METRICS = self.coord_dir / "handoff_metrics.json"
        
        self.manager = HandoffManager()
        self.manager.handoff_file = hm.HANDOFF_FILE
        self.manager.handoff_log = hm.HANDOFF_LOG
        self.manager.metrics_file = hm.HANDOFF_METRICS
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
    
    def test_health_check_with_good_metrics(self):
        """Test health check with healthy metrics"""
        # Create mostly successful handoffs
        for i in range(10):
            result = self.manager.create_handoff(
                from_agent="claude-code",
                to_agent="copilot",
                task={"type": "code_review", "description": f"Review {i}", "requirements": ["code_review"]}
            )
            handoff_id = result["handoff_id"]
            
            # Complete 9 out of 10
            if i < 9:
                self.manager.accept_handoff(handoff_id, "copilot")
                self.manager.start_handoff(handoff_id, "copilot")
                self.manager.complete_handoff(handoff_id, "copilot")
        
        # Check metrics
        metrics = self.manager.get_metrics()
        
        # Should be healthy (90% completion rate)
        self.assertGreaterEqual(metrics["completion_rate"], 0.70)


def run_tests():
    """Run all tests"""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
