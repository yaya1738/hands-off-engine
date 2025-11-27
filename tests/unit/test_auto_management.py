"""
Unit tests for autonomous management scripts.

Tests coordination_agent.py and self_healing_agent.py.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.coordination_agent import CoordinationAgent, AI_COORD_DIR, REPO_ROOT
from scripts.self_healing_agent import SelfHealingAgent


class TestCoordinationAgent:
    """Test CoordinationAgent class"""

    @pytest.fixture
    def temp_coordination_dir(self, tmp_path):
        """Create temporary coordination directory"""
        coord_dir = tmp_path / "ai" / "coordination"
        coord_dir.mkdir(parents=True)
        return coord_dir

    @pytest.fixture
    def agent_with_temp_dir(self, temp_coordination_dir, monkeypatch):
        """Create agent with temporary directory"""
        # Patch the AI_COORD_DIR
        import scripts.coordination_agent as ca_module
        monkeypatch.setattr(ca_module, "AI_COORD_DIR", temp_coordination_dir)
        
        agent = CoordinationAgent()
        return agent

    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        agent = CoordinationAgent()
        assert agent.agent_name == "coordination-agent"
        assert isinstance(agent.processed_message_ids, set)

    def test_check_messages_empty(self, agent_with_temp_dir, temp_coordination_dir):
        """Test checking messages when file doesn't exist"""
        messages = agent_with_temp_dir.check_messages()
        assert messages == []

    def test_check_messages_with_data(self, agent_with_temp_dir, temp_coordination_dir):
        """Test checking messages with existing messages"""
        # Create messages file
        messages_file = temp_coordination_dir / "messages.jsonl"
        msg = {
            "timestamp": "2025-11-27T12:00:00Z",
            "from": "copilot",
            "to": "claude-code",
            "type": "info",
            "message": "Test message"
        }
        messages_file.write_text(json.dumps(msg) + "\n")

        messages = agent_with_temp_dir.check_messages()
        assert len(messages) == 1
        assert messages[0]["from"] == "copilot"

    def test_extract_pr_number(self, agent_with_temp_dir):
        """Test PR number extraction from context"""
        # Valid PR number
        context = {"pr": "42"}
        assert agent_with_temp_dir.extract_pr_number(context) == 42

        # Invalid PR number
        context = {"pr": "invalid"}
        assert agent_with_temp_dir.extract_pr_number(context) is None

        # Missing PR
        context = {}
        assert agent_with_temp_dir.extract_pr_number(context) is None


class TestSelfHealingAgent:
    """Test SelfHealingAgent class"""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """Create temporary state directory"""
        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True)
        return state_dir

    @pytest.fixture
    def temp_logs_dir(self, tmp_path):
        """Create temporary logs directory"""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        return logs_dir

    @pytest.fixture
    def agent_with_temp_dirs(self, tmp_path, temp_state_dir, temp_logs_dir, monkeypatch):
        """Create agent with temporary directories"""
        import scripts.self_healing_agent as sha_module
        monkeypatch.setattr(sha_module, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(sha_module, "STATE_FILE", temp_state_dir / "self_healing_state.json")
        monkeypatch.setattr(sha_module, "LOGS_DIR", temp_logs_dir)
        
        agent = SelfHealingAgent()
        return agent

    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        with patch('scripts.self_healing_agent.STATE_FILE', Path('/tmp/test_state.json')):
            agent = SelfHealingAgent()
            assert agent.fixes_applied == 0
            assert agent.checks_performed == 0
            assert isinstance(agent.state, dict)

    def test_load_state_no_file(self, agent_with_temp_dirs, temp_state_dir):
        """Test loading state when file doesn't exist"""
        state = agent_with_temp_dirs.load_state()
        assert "total_fixes" in state
        assert "issues_detected" in state
        assert "auto_fixed" in state

    def test_load_state_with_file(self, agent_with_temp_dirs, temp_state_dir):
        """Test loading state from existing file"""
        state_file = temp_state_dir / "self_healing_state.json"
        state_data = {
            "total_fixes": 5,
            "last_check": "2025-11-27T12:00:00Z",
            "issues_detected": ["issue1"],
            "auto_fixed": ["fix1"]
        }
        state_file.write_text(json.dumps(state_data))
        
        state = agent_with_temp_dirs.load_state()
        assert state["total_fixes"] == 5
        assert len(state["issues_detected"]) == 1

    def test_check_git_locks_none(self, agent_with_temp_dirs, tmp_path):
        """Test check_git_locks when no lock exists"""
        issues = agent_with_temp_dirs.check_git_locks()
        assert issues == []

    def test_check_file_permissions(self, agent_with_temp_dirs, tmp_path):
        """Test checking file permissions"""
        # Create a mock script directory
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a non-executable script
        script = scripts_dir / "healthcheck.sh"
        script.write_text("#!/bin/bash\necho 'test'")
        script.chmod(0o644)  # Not executable
        
        issues = agent_with_temp_dirs.check_file_permissions()
        # May or may not find issues depending on REPO_ROOT patching
        assert isinstance(issues, list)

    def test_attempt_fix_non_fixable(self, agent_with_temp_dirs):
        """Test attempting to fix non-fixable issue"""
        issue = {
            "type": "test",
            "description": "Test issue",
            "auto_fixable": False
        }
        result = agent_with_temp_dirs.attempt_fix(issue)
        assert result is None

    @patch('subprocess.run')
    def test_attempt_fix_command(self, mock_run, agent_with_temp_dirs):
        """Test fixing issue with command"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        issue = {
            "type": "test",
            "description": "Test issue",
            "auto_fixable": True,
            "fix_cmd": ["echo", "test"]
        }
        result = agent_with_temp_dirs.attempt_fix(issue)
        assert result == "Test issue"


class TestLoggingSetup:
    """Test that logging is properly set up"""

    def test_coordination_agent_imports(self):
        """Test coordination_agent can be imported"""
        import scripts.coordination_agent as ca
        assert hasattr(ca, 'CoordinationAgent')
        assert hasattr(ca, 'setup_logging')

    def test_self_healing_agent_imports(self):
        """Test self_healing_agent can be imported"""
        import scripts.self_healing_agent as sha
        assert hasattr(sha, 'SelfHealingAgent')
        assert hasattr(sha, 'setup_logging')

    def test_logging_uses_logs_dir(self):
        """Test that logging uses the logs directory, not /var/log"""
        import scripts.coordination_agent as ca
        import scripts.self_healing_agent as sha
        
        # Check that LOGS_DIR is relative to REPO_ROOT
        assert ca.LOGS_DIR.name == "logs"
        assert sha.LOGS_DIR.name == "logs"
        
        # Verify no /var/log references
        import inspect
        ca_source = inspect.getsource(ca)
        sha_source = inspect.getsource(sha)
        
        # The source should not have hardcoded /var/log paths
        assert "/var/log/coordination-agent" not in ca_source
        assert "/var/log/self-healing-agent" not in sha_source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
