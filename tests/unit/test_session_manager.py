#!/usr/bin/env python3
"""
Unit tests for session_manager module

Tests the Agent Session Manager functionality for discovering,
creating, and managing agent sessions.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from ai_nexus import session_manager
from ai_nexus.session_manager import (
    SessionTemplate,
    SessionInfo,
    list_sessions,
    get_session_info,
    generate_conversation_id,
    create_session,
    suggest_sessions,
    BUILTIN_TEMPLATES,
)


@pytest.fixture
def temp_dirs(monkeypatch):
    """Create temporary directories for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        intercom_dir = temp_path / "intercom"
        coordination_dir = temp_path / "coordination"
        templates_dir = temp_path / "templates"

        intercom_dir.mkdir(parents=True)
        coordination_dir.mkdir(parents=True)
        templates_dir.mkdir(parents=True)

        # Override paths
        monkeypatch.setattr(session_manager, "INTERCOM_DIR", intercom_dir)
        monkeypatch.setattr(session_manager, "COORDINATION_DIR", coordination_dir)
        monkeypatch.setattr(session_manager, "TEMPLATES_DIR", templates_dir)
        monkeypatch.setattr(session_manager, "REPO_ROOT", temp_path)

        yield {
            "root": temp_path,
            "intercom": intercom_dir,
            "coordination": coordination_dir,
            "templates": templates_dir
        }


class TestSessionTemplate:
    """Tests for SessionTemplate dataclass"""

    def test_template_creation(self):
        """Test creating a session template"""
        template = SessionTemplate(
            name="test_template",
            description="A test template",
            default_goal="Test goal",
            suggested_agents=["chatgpt"],
            suggested_rounds=3,
            suggested_kernels=["test_kernel"]
        )

        assert template.name == "test_template"
        assert template.suggested_rounds == 3
        assert template.mode == "burst"  # default

    def test_template_to_dict(self):
        """Test template serialization"""
        template = SessionTemplate(
            name="test",
            description="Test",
            default_goal="Goal",
            suggested_agents=["chatgpt"],
            suggested_rounds=1,
            suggested_kernels=[]
        )

        data = template.to_dict()
        assert data["name"] == "test"
        assert "mode" in data

    def test_template_from_dict(self):
        """Test template deserialization"""
        data = {
            "name": "test",
            "description": "Test",
            "default_goal": "Goal",
            "suggested_agents": ["chatgpt"],
            "suggested_rounds": 1,
            "suggested_kernels": [],
            "mode": "continuous",
            "tags": ["tag1"]
        }

        template = SessionTemplate.from_dict(data)
        assert template.name == "test"
        assert template.mode == "continuous"


class TestBuiltinTemplates:
    """Tests for builtin templates"""

    def test_risk_analysis_template_exists(self):
        """Test risk_analysis template"""
        assert "risk_analysis" in BUILTIN_TEMPLATES
        template = BUILTIN_TEMPLATES["risk_analysis"]
        assert "risk" in template.tags
        assert "risk_model_v2" in template.suggested_kernels

    def test_alpha_optimization_template_exists(self):
        """Test alpha_optimization template"""
        assert "alpha_optimization" in BUILTIN_TEMPLATES
        template = BUILTIN_TEMPLATES["alpha_optimization"]
        assert "alpha" in template.tags

    def test_all_templates_have_required_fields(self):
        """Test all templates have required fields"""
        for name, template in BUILTIN_TEMPLATES.items():
            assert template.name == name
            assert template.description
            assert template.default_goal
            assert len(template.suggested_agents) > 0
            assert template.suggested_rounds >= 1
            assert template.mode in ["burst", "continuous"]


class TestConversationIdGeneration:
    """Tests for conversation ID generation"""

    def test_generate_without_topic(self):
        """Test generating ID without topic"""
        conv_id = generate_conversation_id()
        assert len(conv_id) > 0
        # Should be timestamp format: YYYYMMDD_HHMMSS
        parts = conv_id.split("_")
        assert len(parts) >= 2

    def test_generate_with_topic(self):
        """Test generating ID with topic"""
        conv_id = generate_conversation_id("Risk Analysis")
        assert "risk_analysis" in conv_id.lower()

    def test_sanitizes_topic(self):
        """Test topic sanitization"""
        conv_id = generate_conversation_id("Test & Special! Characters@#")
        # Should not contain special characters
        for char in "&!@#":
            assert char not in conv_id

    def test_truncates_long_topic(self):
        """Test long topic truncation"""
        long_topic = "A" * 100
        conv_id = generate_conversation_id(long_topic)
        # Topic part should be limited
        assert len(conv_id) < 100


class TestListSessions:
    """Tests for list_sessions function"""

    def test_empty_intercom_dir(self, temp_dirs):
        """Test with empty intercom directory"""
        sessions = list_sessions()
        assert sessions == []

    def test_list_single_session(self, temp_dirs):
        """Test listing a single session"""
        session_dir = temp_dirs["intercom"] / "test_session"
        session_dir.mkdir()

        # Create metadata
        metadata = {
            "conversation_id": "test_session",
            "status": "active",
            "created": "2025-11-27T12:00:00Z",
            "goal": "Test goal",
            "participants": ["chatgpt"],
            "rounds_completed": 1
        }
        with open(session_dir / "metadata.json", "w") as f:
            json.dump(metadata, f)

        (session_dir / "thread.jsonl").touch()

        sessions = list_sessions()
        assert len(sessions) == 1
        assert sessions[0].conversation_id == "test_session"

    def test_list_multiple_sessions(self, temp_dirs):
        """Test listing multiple sessions"""
        for i in range(3):
            session_dir = temp_dirs["intercom"] / f"session_{i}"
            session_dir.mkdir()
            metadata = {
                "conversation_id": f"session_{i}",
                "status": "active",
                "created": f"2025-11-27T1{i}:00:00Z"
            }
            with open(session_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)
            (session_dir / "thread.jsonl").touch()

        sessions = list_sessions()
        assert len(sessions) == 3

    def test_excludes_archived_by_default(self, temp_dirs):
        """Test that archived sessions are excluded by default"""
        # Create regular session
        regular_dir = temp_dirs["intercom"] / "regular_session"
        regular_dir.mkdir()
        with open(regular_dir / "metadata.json", "w") as f:
            json.dump({"conversation_id": "regular_session"}, f)

        # Create archived session
        archived_dir = temp_dirs["intercom"] / "archived_old_session"
        archived_dir.mkdir()
        with open(archived_dir / "metadata.json", "w") as f:
            json.dump({"conversation_id": "archived_old_session"}, f)

        sessions = list_sessions(include_archived=False)
        assert len(sessions) == 1
        assert sessions[0].conversation_id == "regular_session"

    def test_includes_archived_when_requested(self, temp_dirs):
        """Test that archived sessions are included when requested"""
        # Create regular session
        regular_dir = temp_dirs["intercom"] / "regular_session"
        regular_dir.mkdir()
        with open(regular_dir / "metadata.json", "w") as f:
            json.dump({"conversation_id": "regular_session"}, f)

        # Create archived session
        archived_dir = temp_dirs["intercom"] / "archived_old_session"
        archived_dir.mkdir()
        with open(archived_dir / "metadata.json", "w") as f:
            json.dump({"conversation_id": "archived_old_session"}, f)

        sessions = list_sessions(include_archived=True)
        assert len(sessions) == 2


class TestGetSessionInfo:
    """Tests for get_session_info function"""

    def test_session_not_found(self, temp_dirs):
        """Test getting info for non-existent session"""
        info = get_session_info("nonexistent")
        assert info is None

    def test_get_session_info(self, temp_dirs):
        """Test getting session info"""
        session_dir = temp_dirs["intercom"] / "test_session"
        session_dir.mkdir()

        metadata = {
            "conversation_id": "test_session",
            "status": "active",
            "created": "2025-11-27T12:00:00Z",
            "goal": "Test goal",
            "participants": ["chatgpt", "claude_cli"],
            "rounds_completed": 3
        }
        with open(session_dir / "metadata.json", "w") as f:
            json.dump(metadata, f)

        # Create thread with messages
        with open(session_dir / "thread.jsonl", "w") as f:
            f.write('{"msg_id": "msg-001"}\n')
            f.write('{"msg_id": "msg-002"}\n')

        info = get_session_info("test_session")

        assert info is not None
        assert info.conversation_id == "test_session"
        assert info.status == "active"
        assert info.goal == "Test goal"
        assert info.message_count == 2
        assert info.rounds_completed == 3
        assert "chatgpt" in info.participants

    def test_get_session_info_with_cpu_instance(self, temp_dirs):
        """Test getting session info with CPU instance"""
        session_dir = temp_dirs["intercom"] / "cpu_session"
        session_dir.mkdir()

        with open(session_dir / "metadata.json", "w") as f:
            json.dump({"conversation_id": "cpu_session"}, f)

        cpu_instance = {
            "mode": "continuous",
            "bound_kernels": ["risk_model_v2", "system_health"]
        }
        with open(session_dir / "cpu_instance.json", "w") as f:
            json.dump(cpu_instance, f)

        (session_dir / "thread.jsonl").touch()

        info = get_session_info("cpu_session")

        assert info.cpu_mode == "continuous"
        assert len(info.bound_kernels) == 2
        assert "risk_model_v2" in info.bound_kernels


class TestCreateSession:
    """Tests for create_session function"""

    def test_create_basic_session(self, temp_dirs):
        """Test creating a basic session"""
        result = create_session(goal="Test goal")

        assert result["status"] == "created"
        assert "conversation_id" in result
        assert result["goal"] == "Test goal"
        assert "chatgpt" in result["agents"]
        assert "claude_cli" in result["agents"]

        # Verify files created
        session_dir = Path(result["session_dir"])
        assert session_dir.exists()
        assert (session_dir / "metadata.json").exists()
        assert (session_dir / "cpu_instance.json").exists()
        assert (session_dir / "thread.jsonl").exists()

    def test_create_session_with_custom_id(self, temp_dirs):
        """Test creating session with custom ID"""
        result = create_session(
            goal="Test goal",
            conversation_id="my_custom_id"
        )

        assert result["conversation_id"] == "my_custom_id"

    def test_create_session_with_template(self, temp_dirs):
        """Test creating session from template"""
        result = create_session(
            goal="",
            template="risk_analysis"
        )

        assert result["goal"] == "Review current risk model and propose improvements"
        assert "risk_model_v2" in result["bound_kernels"]
        assert result["rounds"] == 2

    def test_create_continuous_session(self, temp_dirs):
        """Test creating continuous mode session"""
        result = create_session(
            goal="Deep analysis",
            mode="continuous",
            max_steps=10,
            max_duration_seconds=600
        )

        assert result["mode"] == "continuous"
        assert result["max_steps"] == 10

    def test_create_session_with_kernels(self, temp_dirs):
        """Test creating session with bound kernels"""
        result = create_session(
            goal="Test",
            kernels=["kernel1", "kernel2"]
        )

        assert result["bound_kernels"] == ["kernel1", "kernel2"]

    def test_run_command_generated(self, temp_dirs):
        """Test that run command is generated"""
        result = create_session(goal="Test")

        assert "run_command" in result
        assert "tri_agent_session_runner" in result["run_command"]
        assert "--session-goal" in result["run_command"]


class TestSuggestSessions:
    """Tests for suggest_sessions function"""

    def test_suggest_with_empty_kernels(self, temp_dirs):
        """Test suggestions with no kernels"""
        with patch("ai_nexus.session_manager.list_kernels", return_value=[]):
            suggestions = suggest_sessions()

        # Should have default suggestions
        assert len(suggestions) >= 1

    def test_suggest_from_pending_tasks(self, temp_dirs):
        """Test suggestions from pending coordination tasks"""
        # Create status.json with pending task
        status = {
            "pending_tasks": [
                {
                    "id": "task-1",
                    "description": "Important task",
                    "status": "pending",
                    "priority": "high"
                }
            ]
        }
        with open(temp_dirs["coordination"] / "status.json", "w") as f:
            json.dump(status, f)

        with patch("ai_nexus.session_manager.list_kernels", return_value=[]):
            suggestions = suggest_sessions()

        # Should include task-based suggestion
        task_suggestions = [s for s in suggestions if "task-1" in str(s.get("task_id", ""))]
        assert len(task_suggestions) >= 1

    def test_suggest_from_kernel_questions(self, temp_dirs):
        """Test suggestions from kernel open questions"""
        mock_kernel = MagicMock()
        mock_kernel.open_questions = ["Question 1?", "Question 2?"]
        mock_kernel.topic = "Risk Management"

        with patch("ai_nexus.session_manager.list_kernels", return_value=["risk_model"]):
            with patch("ai_nexus.session_manager.load_kernel", return_value=mock_kernel):
                suggestions = suggest_sessions()

        # Should include kernel-based suggestion
        kernel_suggestions = [s for s in suggestions if s.get("kernels")]
        assert len(kernel_suggestions) >= 1


class TestSessionInfo:
    """Tests for SessionInfo dataclass"""

    def test_session_info_to_dict(self):
        """Test SessionInfo serialization"""
        info = SessionInfo(
            conversation_id="test",
            status="active",
            created="2025-11-27T12:00:00Z",
            goal="Test goal",
            rounds_completed=2,
            participants=["chatgpt"],
            message_count=5,
            cpu_mode="burst",
            bound_kernels=["kernel1"],
            intercom_path="/path/to/thread.jsonl"
        )

        data = info.to_dict()
        assert data["conversation_id"] == "test"
        assert data["message_count"] == 5
        assert "intercom_path" in data


class TestIntegration:
    """Integration tests for session management workflow"""

    def test_create_and_list_session(self, temp_dirs):
        """Test creating a session and listing it"""
        # Create session
        result = create_session(
            goal="Integration test",
            conversation_id="integration_test"
        )

        assert result["status"] == "created"

        # List sessions
        sessions = list_sessions()

        assert len(sessions) == 1
        assert sessions[0].conversation_id == "integration_test"
        assert sessions[0].goal == "Integration test"

    def test_create_and_get_info(self, temp_dirs):
        """Test creating a session and getting its info"""
        # Create session
        result = create_session(
            goal="Get info test",
            agents=["chatgpt"],
            kernels=["test_kernel"],
            mode="continuous"
        )

        # Get info
        info = get_session_info(result["conversation_id"])

        assert info is not None
        assert info.goal == "Get info test"
        assert info.cpu_mode == "continuous"
        assert "test_kernel" in info.bound_kernels
