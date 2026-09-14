#!/usr/bin/env python3
"""
Tests for Session Ordering System

Validates that agent sessions follow instructions from previous sessions
and execute in the correct order.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# Import the session ordering manager
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_nexus.session_ordering import SessionOrderingManager, SessionDependency


class TestSessionOrderingManager:
    """Test the SessionOrderingManager class"""
    
    @pytest.fixture
    def temp_ordering_file(self):
        """Create a temporary ordering file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = Path(f.name)
        yield temp_path
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
    
    @pytest.fixture
    def manager(self, temp_ordering_file):
        """Create a SessionOrderingManager with temporary file"""
        return SessionOrderingManager(ordering_file=temp_ordering_file)
    
    def test_register_session_no_dependencies(self, manager):
        """Test registering a session with no dependencies"""
        result = manager.register_session("session_001", depends_on=[])
        assert result is True
        
        status = manager.get_session_status("session_001")
        assert status is not None
        assert status["session_id"] == "session_001"
        assert status["status"] == "pending"
        assert status["depends_on"] == []
    
    def test_register_session_with_dependencies(self, manager):
        """Test registering sessions with dependencies"""
        # Register first session
        manager.register_session("session_001")
        
        # Register second session that depends on first
        result = manager.register_session("session_002", depends_on=["session_001"])
        assert result is True
        
        status = manager.get_session_status("session_002")
        assert status["depends_on"] == ["session_001"]
    
    def test_circular_dependency_detection(self, manager):
        """Test that circular dependencies are detected and rejected"""
        # Register sessions in a circular pattern
        manager.register_session("session_a", depends_on=["session_c"])
        manager.register_session("session_b", depends_on=["session_a"])
        
        # This should fail due to circular dependency
        result = manager.register_session("session_c", depends_on=["session_b"])
        assert result is False
    
    def test_can_start_session_no_dependencies(self, manager):
        """Test that sessions with no dependencies can start immediately"""
        manager.register_session("session_001")
        
        can_start, reason = manager.can_start_session("session_001")
        assert can_start is True
        assert reason is None
    
    def test_cannot_start_session_with_incomplete_dependencies(self, manager):
        """Test that sessions cannot start if dependencies are incomplete"""
        manager.register_session("session_001")
        manager.register_session("session_002", depends_on=["session_001"])
        
        # session_002 should not be able to start yet
        can_start, reason = manager.can_start_session("session_002")
        assert can_start is False
        assert "session_001" in reason
        assert "pending" in reason.lower()
    
    def test_can_start_session_after_dependencies_complete(self, manager):
        """Test that sessions can start after all dependencies complete"""
        manager.register_session("session_001")
        manager.register_session("session_002", depends_on=["session_001"])
        
        # Complete session_001
        manager.start_session("session_001")
        manager.complete_session("session_001", success=True)
        
        # Now session_002 should be able to start
        can_start, reason = manager.can_start_session("session_002")
        assert can_start is True
        assert reason is None
    
    def test_start_session_success(self, manager):
        """Test successfully starting a session"""
        manager.register_session("session_001")
        
        result = manager.start_session("session_001")
        assert result is True
        
        status = manager.get_session_status("session_001")
        assert status["status"] == "running"
        assert status["started_at"] is not None
    
    def test_start_session_fails_with_incomplete_dependencies(self, manager):
        """Test that starting a session fails if dependencies are incomplete"""
        manager.register_session("session_001")
        manager.register_session("session_002", depends_on=["session_001"])
        
        result = manager.start_session("session_002")
        assert result is False
        
        status = manager.get_session_status("session_002")
        assert status["status"] == "pending"
    
    def test_complete_session(self, manager):
        """Test completing a session"""
        manager.register_session("session_001")
        manager.start_session("session_001")
        manager.complete_session("session_001", success=True)
        
        status = manager.get_session_status("session_001")
        assert status["status"] == "completed"
        assert status["completed_at"] is not None
    
    def test_complete_session_failure(self, manager):
        """Test completing a session with failure"""
        manager.register_session("session_001")
        manager.start_session("session_001")
        manager.complete_session("session_001", success=False)
        
        status = manager.get_session_status("session_001")
        assert status["status"] == "failed"
    
    def test_get_ready_sessions(self, manager):
        """Test getting list of sessions ready to start"""
        # Register sessions with dependencies
        manager.register_session("session_001")
        manager.register_session("session_002", depends_on=["session_001"])
        manager.register_session("session_003")
        
        # Only session_001 and session_003 should be ready
        ready = manager.get_ready_sessions()
        assert "session_001" in ready
        assert "session_003" in ready
        assert "session_002" not in ready
        
        # Complete session_001
        manager.start_session("session_001")
        manager.complete_session("session_001")
        
        # Now session_002 should also be ready
        ready = manager.get_ready_sessions()
        assert "session_002" in ready
    
    def test_session_dependency_chain(self, manager):
        """Test a chain of dependent sessions"""
        # Create chain: 001 -> 002 -> 003
        manager.register_session("session_001")
        manager.register_session("session_002", depends_on=["session_001"])
        manager.register_session("session_003", depends_on=["session_002"])
        
        # Only session_001 should be ready
        ready = manager.get_ready_sessions()
        assert ready == ["session_001"]
        
        # Complete session_001
        manager.start_session("session_001")
        manager.complete_session("session_001")
        
        # Now session_002 should be ready
        ready = manager.get_ready_sessions()
        assert ready == ["session_002"]
        
        # Complete session_002
        manager.start_session("session_002")
        manager.complete_session("session_002")
        
        # Now session_003 should be ready
        ready = manager.get_ready_sessions()
        assert ready == ["session_003"]
    
    def test_multiple_dependencies(self, manager):
        """Test session with multiple dependencies"""
        # Create sessions
        manager.register_session("session_001")
        manager.register_session("session_002")
        manager.register_session("session_003", depends_on=["session_001", "session_002"])
        
        # session_003 should not be ready
        can_start, _ = manager.can_start_session("session_003")
        assert can_start is False
        
        # Complete only session_001
        manager.start_session("session_001")
        manager.complete_session("session_001")
        
        # session_003 still should not be ready
        can_start, _ = manager.can_start_session("session_003")
        assert can_start is False
        
        # Complete session_002
        manager.start_session("session_002")
        manager.complete_session("session_002")
        
        # Now session_003 should be ready
        can_start, _ = manager.can_start_session("session_003")
        assert can_start is True
    
    def test_persistence(self, manager, temp_ordering_file):
        """Test that session ordering persists across manager instances"""
        # Register sessions
        manager.register_session("session_001")
        manager.register_session("session_002", depends_on=["session_001"])
        
        # Create new manager instance with same file
        new_manager = SessionOrderingManager(ordering_file=temp_ordering_file)
        
        # Should be able to retrieve session status
        status = new_manager.get_session_status("session_002")
        assert status is not None
        assert status["depends_on"] == ["session_001"]


class TestAutonomousTaskQueueIntegration:
    """Test integration with autonomous task queue"""
    
    def test_task_queue_respects_dependencies(self):
        """Test that task queue respects session dependencies"""
        # This test would verify the autonomous_task_queue.py integration
        # For now, this is a placeholder for integration testing
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
