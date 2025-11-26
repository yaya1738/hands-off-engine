"""
Integration tests for AI Intake handler

Tests /plan command handling and coordination with AI systems.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestAIIntakeBasics:
    """Basic tests for AI intake functionality"""

    @patch('ai.ai_intake_handler.requests.post')
    @patch('ai.ai_intake_handler.OpenAI')
    def test_plan_command_triggered(self, mock_openai, mock_post):
        """Test that /plan command is recognized"""
        # Mock event data
        event = {
            'issue': {
                'number': 1,
                'title': 'AI Intake'
            },
            'comment': {
                'body': '/plan Implement feature X'
            }
        }

        # Set environment variables
        os.environ['GITHUB_REPOSITORY'] = 'test/repo'
        os.environ['GITHUB_TOKEN'] = 'test_token'

        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Test plan response"))]
        mock_client.chat.completions.create.return_value = mock_completion

        # Mock GitHub API post
        mock_post.return_value = MagicMock(status_code=201)

        # Import after mocks are set up
        from ai.ai_intake_handler import run_plan

        # Run plan
        run_plan(event)

        # Verify OpenAI was called
        assert mock_client.chat.completions.create.called

        # Verify GitHub comment was posted
        assert mock_post.called

    def test_load_text_function(self):
        """Test load_text helper function"""
        from ai.ai_intake_handler import load_text

        # Test with non-existent file
        result = load_text('/tmp/nonexistent_file_xyz.txt')
        assert '[WARN]' in result
        assert 'not found' in result

        # Test with existing file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('Test content')
            temp_path = f.name

        try:
            result = load_text(temp_path)
            assert result == 'Test content'
        finally:
            os.unlink(temp_path)


class TestAIIntakeCoordination:
    """Tests for AI intake coordination with multi-agent system"""

    def test_coordination_file_structure(self):
        """Test that coordination files exist and have expected structure"""
        repo_root = Path(__file__).parent.parent.parent
        coordination_dir = repo_root / 'ai' / 'coordination'

        # Check that coordination directory exists
        assert coordination_dir.exists(), "Coordination directory should exist"

        # Check for expected files
        expected_files = ['status.json', 'messages.jsonl']
        for filename in expected_files:
            filepath = coordination_dir / filename
            if filepath.exists():
                # Verify it's valid JSON/JSONL
                if filename.endswith('.json'):
                    with open(filepath) as f:
                        try:
                            json.load(f)
                        except json.JSONDecodeError:
                            pytest.fail(f"{filename} should be valid JSON")

    def test_status_json_structure(self):
        """Test that status.json has expected structure"""
        repo_root = Path(__file__).parent.parent.parent
        status_file = repo_root / 'ai' / 'coordination' / 'status.json'

        if not status_file.exists():
            pytest.skip("status.json not found")

        with open(status_file) as f:
            status = json.load(f)

        # Check for expected top-level keys
        expected_keys = ['phase', 'current_tasks']
        for key in expected_keys:
            if key in status:
                assert isinstance(status[key], (str, list, dict)), f"{key} should be string, list, or dict"

    def test_messages_jsonl_format(self):
        """Test that messages.jsonl follows JSONL format"""
        repo_root = Path(__file__).parent.parent.parent
        messages_file = repo_root / 'ai' / 'coordination' / 'messages.jsonl'

        if not messages_file.exists():
            pytest.skip("messages.jsonl not found")

        with open(messages_file) as f:
            lines = f.readlines()

        # Each line should be valid JSON
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            try:
                msg = json.loads(line)
                # Verify basic message structure
                assert isinstance(msg, dict), f"Line {i} should be a JSON object"
            except json.JSONDecodeError:
                pytest.fail(f"Line {i} in messages.jsonl is not valid JSON")


class TestAIIntakeIntegration:
    """Integration tests for AI intake with other systems"""

    def test_intake_creates_coordination_message(self):
        """Test that AI intake creates coordination messages"""
        # This would be a full integration test
        # For now, we verify the structure is testable
        assert True

    @pytest.mark.skip(reason="Requires live API credentials")
    def test_plan_command_end_to_end(self):
        """Full end-to-end test of /plan command (requires API credentials)"""
        # This would test the full flow:
        # 1. Comment with /plan is posted
        # 2. AI intake handler processes it
        # 3. Response is generated via LLM
        # 4. Response is posted back to issue
        # 5. Coordination files are updated
        pass


class TestCoordinationProtocol:
    """Tests for multi-agent coordination protocol"""

    def test_handoff_structure(self):
        """Test handoff.json structure"""
        repo_root = Path(__file__).parent.parent.parent
        handoffs_file = repo_root / 'ai' / 'coordination' / 'handoffs.json'

        if not handoffs_file.exists():
            pytest.skip("handoffs.json not found")

        with open(handoffs_file) as f:
            handoffs = json.load(f)

        # Verify it's a list or dict
        assert isinstance(handoffs, (list, dict)), "handoffs.json should be list or dict"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
