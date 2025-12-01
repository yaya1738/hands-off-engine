"""
Tests for Agent Session Ordering Protocol

Validates that session dependencies and ordering are enforced correctly.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch
import sys

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ai_nexus.spark_plug_types import CpuInstance, CpuConfig
from ai_nexus.tri_agent_session_runner import TriAgentSession
from scripts.autonomous_task_queue import AutonomousTaskQueue


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary test directory"""
    return tmp_path


@pytest.fixture
def mock_agent_providers():
    """Mock agent providers to avoid real LLM calls"""
    def fake_chatgpt(agent_id, prior_messages, session_goal):
        return {
            "content": f"Fake ChatGPT response for: {session_goal}",
            "model": "fake-gpt-4",
            "tokens": 50,
            "cost_usd": 0.001
        }

    def fake_claude(agent_id, prior_messages, session_goal):
        return {
            "content": f"Fake Claude response for: {session_goal}",
            "model": "fake-claude-3",
            "tokens": 60,
            "cost_usd": 0.002
        }

    return {
        "chatgpt": fake_chatgpt,
        "claude_cli": fake_claude
    }


def test_session_with_dependencies_serializes_correctly(temp_test_dir):
    """Test that session dependencies are preserved in JSON"""
    cpu = CpuInstance(
        cpu_id="test_session",
        mode="burst",
        previous_session_id="prev_session",
        depends_on=["dep1", "dep2"],
        session_order=3
    )
    
    # Serialize and deserialize
    json_data = cpu.to_json()
    cpu_restored = CpuInstance.from_json(json_data)
    
    # Verify fields are preserved
    assert cpu_restored.previous_session_id == "prev_session"
    assert cpu_restored.depends_on == ["dep1", "dep2"]
    assert cpu_restored.session_order == 3


def test_session_blocks_when_previous_session_incomplete(temp_test_dir, mock_agent_providers):
    """Test that a session blocks when previous session is not complete"""
    with patch('ai_nexus.tri_agent_session_runner.REPO_ROOT', temp_test_dir), \
         patch('ai_nexus.tri_agent_session_runner.AGENT_PROVIDERS', mock_agent_providers):
        
        # Create previous session that is not completed
        prev_session = TriAgentSession(
            conversation_id="previous_session",
            session_goal="Previous work"
        )
        prev_session.cpu.status = "running"  # Not completed
        prev_session._save_cpu_instance(prev_session.cpu)
        
        # Create dependent session
        dep_session = TriAgentSession(
            conversation_id="dependent_session",
            session_goal="Dependent work",
            previous_session_id="previous_session"
        )
        
        # Try to run - should be blocked
        dep_session.run_session(agents=["chatgpt"], rounds=1)
        
        # Verify session was blocked
        assert dep_session.cpu.status == "blocked"


def test_session_runs_when_previous_session_complete(temp_test_dir, mock_agent_providers):
    """Test that a session runs when previous session is complete"""
    with patch('ai_nexus.tri_agent_session_runner.REPO_ROOT', temp_test_dir), \
         patch('ai_nexus.tri_agent_session_runner.AGENT_PROVIDERS', mock_agent_providers):
        
        # Create previous session that is completed
        prev_session = TriAgentSession(
            conversation_id="previous_session",
            session_goal="Previous work"
        )
        prev_session.cpu.status = "stopped"  # Completed
        prev_session._save_cpu_instance(prev_session.cpu)
        
        # Create dependent session
        dep_session = TriAgentSession(
            conversation_id="dependent_session",
            session_goal="Dependent work",
            previous_session_id="previous_session"
        )
        
        # Try to run - should succeed
        dep_session.run_session(agents=["chatgpt"], rounds=1)
        
        # Verify session ran (not blocked)
        assert dep_session.cpu.status != "blocked"


def test_session_blocks_when_any_dependency_incomplete(temp_test_dir, mock_agent_providers):
    """Test that a session blocks when any dependency is incomplete"""
    with patch('ai_nexus.tri_agent_session_runner.REPO_ROOT', temp_test_dir), \
         patch('ai_nexus.tri_agent_session_runner.AGENT_PROVIDERS', mock_agent_providers):
        
        # Create first dependency - completed
        dep1 = TriAgentSession(conversation_id="dep1", session_goal="Dep 1")
        dep1.cpu.status = "stopped"
        dep1._save_cpu_instance(dep1.cpu)
        
        # Create second dependency - not completed
        dep2 = TriAgentSession(conversation_id="dep2", session_goal="Dep 2")
        dep2.cpu.status = "running"
        dep2._save_cpu_instance(dep2.cpu)
        
        # Create session that depends on both
        main_session = TriAgentSession(
            conversation_id="main_session",
            session_goal="Main work",
            depends_on=["dep1", "dep2"]
        )
        
        # Try to run - should be blocked
        main_session.run_session(agents=["chatgpt"], rounds=1)
        
        # Verify session was blocked
        assert main_session.cpu.status == "blocked"


def test_session_runs_when_all_dependencies_complete(temp_test_dir, mock_agent_providers):
    """Test that a session runs when all dependencies are complete"""
    with patch('ai_nexus.tri_agent_session_runner.REPO_ROOT', temp_test_dir), \
         patch('ai_nexus.tri_agent_session_runner.AGENT_PROVIDERS', mock_agent_providers):
        
        # Create dependencies - both completed
        dep1 = TriAgentSession(conversation_id="dep1", session_goal="Dep 1")
        dep1.cpu.status = "stopped"
        dep1._save_cpu_instance(dep1.cpu)
        
        dep2 = TriAgentSession(conversation_id="dep2", session_goal="Dep 2")
        dep2.cpu.status = "stopped"
        dep2._save_cpu_instance(dep2.cpu)
        
        # Create session that depends on both
        main_session = TriAgentSession(
            conversation_id="main_session",
            session_goal="Main work",
            depends_on=["dep1", "dep2"]
        )
        
        # Try to run - should succeed
        main_session.run_session(agents=["chatgpt"], rounds=1)
        
        # Verify session ran (not blocked)
        assert main_session.cpu.status != "blocked"


def test_task_queue_respects_previous_task(temp_test_dir):
    """Test that task queue respects previous_task_id dependency"""
    queue = AutonomousTaskQueue(temp_test_dir)
    
    # Add first task
    task1_id = queue.add_task(
        title="Task 1",
        description="First task",
        priority="high"
    )
    
    # Add second task that depends on first
    task2_id = queue.add_task(
        title="Task 2",
        description="Second task",
        priority="high",
        metadata={'previous_task_id': task1_id}
    )
    
    # Get next task - should be task 1
    next_task = queue.get_next_task()
    assert next_task['id'] == task1_id
    
    # Complete task 1
    queue.complete_task(task1_id, "completed")
    
    # Now get next task - should be task 2
    next_task = queue.get_next_task()
    assert next_task['id'] == task2_id


def test_task_queue_blocks_when_previous_task_incomplete(temp_test_dir):
    """Test that task queue blocks dependent tasks"""
    queue = AutonomousTaskQueue(temp_test_dir)
    
    # Add first task
    task1_id = queue.add_task(
        title="Task 1",
        description="First task",
        priority="normal"
    )
    
    # Add second task that depends on first
    task2_id = queue.add_task(
        title="Task 2",
        description="Second task",
        priority="critical",  # Higher priority but still blocked
        metadata={'previous_task_id': task1_id}
    )
    
    # Get next task - should be task 1 (task 2 is blocked despite higher priority)
    next_task = queue.get_next_task()
    assert next_task['id'] == task1_id


def test_task_queue_respects_task_order(temp_test_dir):
    """Test that task queue respects task_order field"""
    queue = AutonomousTaskQueue(temp_test_dir)
    
    # Add tasks in reverse order
    task3_id = queue.add_task(
        title="Task 3",
        description="Third task",
        priority="high",
        metadata={'task_order': 3}
    )
    
    task1_id = queue.add_task(
        title="Task 1",
        description="First task",
        priority="normal",  # Lower priority
        metadata={'task_order': 1}
    )
    
    task2_id = queue.add_task(
        title="Task 2",
        description="Second task",
        priority="high",
        metadata={'task_order': 2}
    )
    
    # Get next task - should be task 1 (lowest order)
    next_task = queue.get_next_task()
    assert next_task['id'] == task1_id
    
    # Complete task 1
    queue.complete_task(task1_id, "completed")
    
    # Get next task - should be task 2 (next order)
    next_task = queue.get_next_task()
    assert next_task['id'] == task2_id


def test_session_order_blocks_when_earlier_incomplete(temp_test_dir, mock_agent_providers):
    """Test that session_order blocks when earlier sessions are incomplete"""
    with patch('ai_nexus.tri_agent_session_runner.REPO_ROOT', temp_test_dir), \
         patch('ai_nexus.tri_agent_session_runner.AGENT_PROVIDERS', mock_agent_providers):
        
        # Create session with order 1 - not completed
        session1 = TriAgentSession(
            conversation_id="session_order_1",
            session_goal="First session",
            session_order=1
        )
        session1.cpu.status = "running"
        session1._save_cpu_instance(session1.cpu)
        
        # Create session with order 2
        session2 = TriAgentSession(
            conversation_id="session_order_2",
            session_goal="Second session",
            session_order=2
        )
        
        # Try to run session 2 - should be blocked
        session2.run_session(agents=["chatgpt"], rounds=1)
        
        # Verify session was blocked
        assert session2.cpu.status == "blocked"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
