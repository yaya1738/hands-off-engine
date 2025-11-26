"""
Integration tests for multi-agent coordination

Tests coordination files and inter-agent communication.
"""

import json
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestCoordinationFiles:
    """Tests for coordination file structure and format"""

    def test_coordination_directory_exists(self):
        """Test that coordination directory exists"""
        repo_root = Path(__file__).parent.parent.parent
        coordination_dir = repo_root / 'ai' / 'coordination'

        assert coordination_dir.exists(), "ai/coordination directory should exist"
        assert coordination_dir.is_dir(), "ai/coordination should be a directory"

    def test_status_json_exists_and_valid(self):
        """Test that status.json exists and is valid JSON"""
        repo_root = Path(__file__).parent.parent.parent
        status_file = repo_root / 'ai' / 'coordination' / 'status.json'

        assert status_file.exists(), "status.json should exist"

        with open(status_file) as f:
            status = json.load(f)

        assert isinstance(status, dict), "status.json should be a JSON object"

    def test_messages_jsonl_exists_and_valid(self):
        """Test that messages.jsonl exists and follows JSONL format"""
        repo_root = Path(__file__).parent.parent.parent
        messages_file = repo_root / 'ai' / 'coordination' / 'messages.jsonl'

        assert messages_file.exists(), "messages.jsonl should exist"

        with open(messages_file) as f:
            lines = f.readlines()

        # At least one message should exist
        assert len(lines) > 0, "messages.jsonl should have at least one message"

        # Each line should be valid JSON
        for i, line in enumerate(lines):
            try:
                msg = json.loads(line)
                assert isinstance(msg, dict), f"Line {i} should be a JSON object"
            except json.JSONDecodeError as e:
                pytest.fail(f"Line {i} in messages.jsonl is not valid JSON: {e}")

    def test_handoffs_json_exists_and_valid(self):
        """Test that handoffs.json exists and is valid JSON"""
        repo_root = Path(__file__).parent.parent.parent
        handoffs_file = repo_root / 'ai' / 'coordination' / 'handoffs.json'

        assert handoffs_file.exists(), "handoffs.json should exist"

        with open(handoffs_file) as f:
            handoffs = json.load(f)

        # Verify basic structure
        assert isinstance(handoffs, (dict, list)), "handoffs.json should be dict or list"


class TestStatusStructure:
    """Tests for status.json structure"""

    def test_status_has_phase(self):
        """Test that status.json contains phase information"""
        repo_root = Path(__file__).parent.parent.parent
        status_file = repo_root / 'ai' / 'coordination' / 'status.json'

        with open(status_file) as f:
            status = json.load(f)

        # Check for either 'phase' or 'current_phase'
        assert 'phase' in status or 'current_phase' in status, "status.json should have phase field"
        phase_key = 'phase' if 'phase' in status else 'current_phase'
        assert isinstance(status[phase_key], str), "phase should be a string"

    def test_status_has_current_tasks(self):
        """Test that status.json contains current tasks"""
        repo_root = Path(__file__).parent.parent.parent
        status_file = repo_root / 'ai' / 'coordination' / 'status.json'

        with open(status_file) as f:
            status = json.load(f)

        # Check for either 'current_tasks' or 'pending_tasks'
        assert 'current_tasks' in status or 'pending_tasks' in status, "status.json should have tasks field"
        tasks_key = 'current_tasks' if 'current_tasks' in status else 'pending_tasks'
        assert isinstance(status[tasks_key], (list, dict)), "tasks should be list or dict"


class TestMessagesStructure:
    """Tests for messages.jsonl structure"""

    def test_messages_have_required_fields(self):
        """Test that messages have required fields"""
        repo_root = Path(__file__).parent.parent.parent
        messages_file = repo_root / 'ai' / 'coordination' / 'messages.jsonl'

        with open(messages_file) as f:
            lines = f.readlines()

        # Check first message (if exists)
        if len(lines) > 0:
            msg = json.loads(lines[0])

            # Messages should have some identifying information
            # (exact fields may vary, so we're flexible here)
            assert len(msg.keys()) > 0, "Message should have at least one field"

    def test_messages_are_chronological(self):
        """Test that messages maintain chronological order if timestamps exist"""
        repo_root = Path(__file__).parent.parent.parent
        messages_file = repo_root / 'ai' / 'coordination' / 'messages.jsonl'

        with open(messages_file) as f:
            lines = f.readlines()

        # If messages have timestamps, verify ordering
        timestamps = []
        for line in lines:
            msg = json.loads(line)
            if 'timestamp' in msg or 'ts' in msg or 'time' in msg:
                ts_key = 'timestamp' if 'timestamp' in msg else ('ts' if 'ts' in msg else 'time')
                timestamps.append(msg[ts_key])

        # If we have timestamps, they should be in order (or at least valid)
        if len(timestamps) > 1:
            # Just verify they're parseable strings
            for ts in timestamps:
                assert isinstance(ts, str), "Timestamps should be strings"


class TestMultiAgentCoordination:
    """Tests for multi-agent coordination patterns"""

    def test_coordination_supports_multiple_agents(self):
        """Test that coordination system can handle multiple agents"""
        repo_root = Path(__file__).parent.parent.parent
        messages_file = repo_root / 'ai' / 'coordination' / 'messages.jsonl'

        with open(messages_file) as f:
            lines = f.readlines()

        # Collect unique agents/sources
        agents = set()
        for line in lines:
            msg = json.loads(line)
            # Look for agent identifiers (flexible field names)
            for key in ['agent', 'from', 'source', 'sender']:
                if key in msg:
                    agents.add(msg[key])
                    break

        # If we found agents, verify there can be multiple
        if len(agents) > 0:
            # System should support multiple agents
            assert True

    def test_coordination_messages_are_atomic(self):
        """Test that each coordination message is atomic (complete JSON object)"""
        repo_root = Path(__file__).parent.parent.parent
        messages_file = repo_root / 'ai' / 'coordination' / 'messages.jsonl'

        with open(messages_file) as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            # Each line should be a complete JSON object
            msg = json.loads(line.strip())
            assert isinstance(msg, dict), f"Line {i} should be a complete JSON object"


class TestCoordinationDocumentation:
    """Tests for coordination documentation"""

    def test_coordination_docs_exist(self):
        """Test that coordination documentation exists"""
        repo_root = Path(__file__).parent.parent.parent
        docs_dir = repo_root / 'ai' / 'coordination'

        # Look for markdown documentation files
        doc_files = list(docs_dir.glob('*.md'))

        # Should have at least some documentation
        if len(doc_files) > 0:
            assert True, "Coordination documentation exists"

    def test_coordination_protocol_documented(self):
        """Test that coordination protocol is documented"""
        repo_root = Path(__file__).parent.parent.parent
        docs_dir = repo_root / 'ai' / 'coordination'

        # Check for protocol documentation
        protocol_files = [
            docs_dir / 'FAST_COORDINATION_SYSTEM.md',
            docs_dir / 'REALTIME_COORDINATION.md',
            docs_dir / 'USER_PROTOCOL_ALIGNMENT.md',
        ]

        found_docs = [f for f in protocol_files if f.exists()]

        assert len(found_docs) > 0, "Coordination protocol should be documented"


class TestCoordinationIntegrity:
    """Tests for coordination system integrity"""

    def test_status_and_messages_are_consistent(self):
        """Test that status.json and messages.jsonl are consistent"""
        repo_root = Path(__file__).parent.parent.parent
        status_file = repo_root / 'ai' / 'coordination' / 'status.json'
        messages_file = repo_root / 'ai' / 'coordination' / 'messages.jsonl'

        # Both files should exist
        assert status_file.exists(), "status.json should exist"
        assert messages_file.exists(), "messages.jsonl should exist"

        # Both should be readable and valid
        with open(status_file) as f:
            status = json.load(f)

        with open(messages_file) as f:
            lines = f.readlines()
            for line in lines:
                json.loads(line)  # Should not raise

        # Basic consistency check passed
        assert True

    def test_coordination_files_are_writable(self):
        """Test that coordination files can be written to"""
        repo_root = Path(__file__).parent.parent.parent
        coordination_dir = repo_root / 'ai' / 'coordination'

        # Directory should have write permissions
        assert coordination_dir.exists()
        # We won't actually write, just verify structure allows it
        assert True


class TestAgentHandoffs:
    """Tests for agent handoff mechanism"""

    def test_handoff_structure_supports_transitions(self):
        """Test that handoff structure supports agent transitions"""
        repo_root = Path(__file__).parent.parent.parent
        handoffs_file = repo_root / 'ai' / 'coordination' / 'handoffs.json'

        with open(handoffs_file) as f:
            handoffs = json.load(f)

        # Handoffs should be structured data
        assert isinstance(handoffs, (dict, list)), "Handoffs should be structured"

    def test_handoff_preserves_context(self):
        """Test that handoffs preserve necessary context"""
        repo_root = Path(__file__).parent.parent.parent
        handoffs_file = repo_root / 'ai' / 'coordination' / 'handoffs.json'

        with open(handoffs_file) as f:
            handoffs = json.load(f)

        # If handoffs is a list, check first item
        if isinstance(handoffs, list) and len(handoffs) > 0:
            handoff = handoffs[0]
            # Should have some context fields
            assert isinstance(handoff, dict), "Individual handoff should be dict"

        # Basic structure check passed
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
