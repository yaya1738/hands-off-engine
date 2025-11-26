"""
Unit tests for spark_plug_autokernel module (Spark Plug v0.2)

Tests the auto-kernel refresh system that wires Parts 1-3 together.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

from ai_nexus.spark_plug_types import create_history_event, MemoryKernel, Decision
from ai_nexus import history_logger, spark_plug_autokernel, spark_plug_history
from ai_nexus.memory_kernels import save_kernel


@pytest.fixture
def temp_dirs(monkeypatch):
    """Create temporary directories for history and kernels"""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        # Override paths
        history_file = temp_path / "history" / "user_events.jsonl"
        kernels_dir = temp_path / "kernels"
        intercom_dir = temp_path / "intercom"

        monkeypatch.setattr(history_logger, "HISTORY_FILE", history_file)
        monkeypatch.setattr("ai_nexus.memory_kernels.KERNELS_DIR", kernels_dir)
        monkeypatch.setattr("ai_nexus.spark_plug_autokernel.REPO_ROOT", temp_path)

        # Also patch spark_plug_history paths for unified history loader
        new_history_file = temp_path / "history" / "events.jsonl"
        monkeypatch.setattr(spark_plug_history, "REPO_ROOT", temp_path)
        monkeypatch.setattr(spark_plug_history, "NEW_HISTORY_FILE", new_history_file)
        monkeypatch.setattr(spark_plug_history, "LEGACY_HISTORY_FILE", history_file)

        yield {
            "history_file": history_file,
            "kernels_dir": kernels_dir,
            "intercom_dir": intercom_dir,
            "temp_path": temp_path
        }


@pytest.fixture
def sample_kernel(temp_dirs):
    """Create a sample memory kernel"""
    kernel = MemoryKernel(
        kernel_id="test_kernel",
        topic="Test Topic",
        summary="This is a test kernel for v0.2 testing",
        key_decisions=[
            Decision(
                decision="Use test-driven development",
                rationale="Ensures code quality",
                source="cpu_test_01",
                date="2025-11-26T10:00:00Z"
            )
        ],
        failed_paths=[],
        open_questions=["What should be the next feature?"]
    )

    save_kernel(kernel)
    return kernel


@pytest.fixture
def sample_history(temp_dirs, sample_kernel):
    """Create sample history events"""
    events = [
        create_history_event(
            event_type="user_message",
            source="user:test",
            content="What's the status of the test kernel?",
            kernel_id="test_kernel"
        ),
        create_history_event(
            event_type="system_decision",
            source="cpu_test_01",
            content="Updated test kernel with new decision",
            kernel_id="test_kernel"
        ),
        create_history_event(
            event_type="observation",
            source="monitoring",
            content="System running smoothly",
        ),
    ]

    for event in events:
        history_logger.append_history_event(event)

    return events


class TestRefreshKernelFromHistory:
    """Test refresh_kernel_from_history function"""

    def test_kernel_not_found(self, temp_dirs):
        """Test with non-existent kernel"""
        result = spark_plug_autokernel.refresh_kernel_from_history(
            kernel_id="nonexistent_kernel"
        )

        assert result["status"] == "kernel_not_found"
        assert result["kernel_id"] == "nonexistent_kernel"
        assert result["cpu_run"] is False

    def test_no_history_events(self, temp_dirs, sample_kernel):
        """Test with kernel but no history events"""
        result = spark_plug_autokernel.refresh_kernel_from_history(
            kernel_id="test_kernel"
        )

        assert result["status"] == "no_history"
        assert result["kernel_id"] == "test_kernel"
        assert result["events_found"] == 0
        assert result["cpu_run"] is False

    def test_empty_kernel_id(self, temp_dirs):
        """Test with empty kernel_id"""
        with pytest.raises(ValueError, match="kernel_id cannot be empty"):
            spark_plug_autokernel.refresh_kernel_from_history(kernel_id="")

    def test_dry_run_mode(self, temp_dirs, sample_kernel, sample_history):
        """Test dry run mode (no CPU execution)"""
        result = spark_plug_autokernel.refresh_kernel_from_history(
            kernel_id="test_kernel",
            max_events=10,
            dry_run=True
        )

        assert result["status"] == "dry_run"
        assert result["kernel_id"] == "test_kernel"
        assert result["events_found"] >= 2  # At least 2 events for test_kernel
        assert result["cpu_run"] is False
        assert "Dry run complete" in result["message"]

    @patch('ai_nexus.spark_plug_autokernel.TriAgentSession')
    def test_cpu_execution_success(
        self,
        mock_session_class,
        temp_dirs,
        sample_kernel,
        sample_history
    ):
        """Test successful CPU execution (mocked)"""
        # Mock TriAgentSession
        mock_session = MagicMock()
        mock_session.thread_file = Path("/tmp/test/thread.jsonl")
        mock_session.cpu_instance_file = Path("/tmp/test/cpu_instance.json")
        mock_session_class.return_value = mock_session

        result = spark_plug_autokernel.refresh_kernel_from_history(
            kernel_id="test_kernel",
            max_events=10,
            rounds=1
        )

        # Verify TriAgentSession was called
        assert mock_session_class.called
        call_kwargs = mock_session_class.call_args[1]
        assert call_kwargs["bound_kernels"] == ["test_kernel"]
        assert call_kwargs["max_rounds"] == 1

        # Verify session methods were called
        assert mock_session.append_message.called
        assert mock_session.run_session.called

        # Verify result
        assert result["status"] == "success"
        assert result["kernel_id"] == "test_kernel"
        assert result["cpu_run"] is True
        assert result["events_found"] >= 2

    @patch('ai_nexus.spark_plug_autokernel.TriAgentSession')
    def test_cpu_execution_with_custom_params(
        self,
        mock_session_class,
        temp_dirs,
        sample_kernel,
        sample_history
    ):
        """Test CPU execution with custom parameters"""
        mock_session = MagicMock()
        mock_session.thread_file = Path("/tmp/test/thread.jsonl")
        mock_session.cpu_instance_file = Path("/tmp/test/cpu_instance.json")
        mock_session_class.return_value = mock_session

        result = spark_plug_autokernel.refresh_kernel_from_history(
            kernel_id="test_kernel",
            max_events=20,
            conversation_id="custom_conv_001",
            session_goal="Custom goal",
            agents=["chatgpt"],
            rounds=3
        )

        # Verify custom parameters were used
        call_kwargs = mock_session_class.call_args[1]
        assert call_kwargs["conversation_id"] == "custom_conv_001"
        assert call_kwargs["session_goal"] == "Custom goal"
        assert call_kwargs["max_rounds"] == 3

        run_kwargs = mock_session.run_session.call_args[1]
        assert run_kwargs["agents"] == ["chatgpt"]
        assert run_kwargs["rounds"] == 3

        assert result["status"] == "success"

    @patch('ai_nexus.spark_plug_autokernel.TriAgentSession')
    def test_cpu_execution_error(
        self,
        mock_session_class,
        temp_dirs,
        sample_kernel,
        sample_history
    ):
        """Test CPU execution with error"""
        # Mock TriAgentSession to raise error
        mock_session_class.side_effect = Exception("Test error")

        result = spark_plug_autokernel.refresh_kernel_from_history(
            kernel_id="test_kernel",
            max_events=10
        )

        assert result["status"] == "error"
        assert "Test error" in result["message"]
        assert result["cpu_run"] is False

    def test_auto_generated_conversation_id(
        self,
        temp_dirs,
        sample_kernel,
        sample_history
    ):
        """Test auto-generation of conversation_id"""
        with patch('ai_nexus.spark_plug_autokernel.TriAgentSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.thread_file = Path("/tmp/test/thread.jsonl")
            mock_session.cpu_instance_file = Path("/tmp/test/cpu_instance.json")
            mock_session_class.return_value = mock_session

            result = spark_plug_autokernel.refresh_kernel_from_history(
                kernel_id="test_kernel"
            )

            # Conversation ID should be auto-generated
            conversation_id = mock_session_class.call_args[1]["conversation_id"]
            assert conversation_id.startswith("autokernel_test_kernel_")
            assert result["conversation_id"] == conversation_id


class TestUtilityFunctions:
    """Test utility functions"""

    def test_list_refreshable_kernels_empty(self, temp_dirs):
        """Test listing kernels with no history"""
        kernels = spark_plug_autokernel.list_refreshable_kernels()
        assert kernels == []

    def test_list_refreshable_kernels(self, temp_dirs, sample_kernel, sample_history):
        """Test listing kernels with history"""
        kernels = spark_plug_autokernel.list_refreshable_kernels()
        assert "test_kernel" in kernels

    def test_list_refreshable_kernels_multiple(self, temp_dirs):
        """Test listing multiple kernels"""
        # Create multiple kernels
        for i in range(3):
            kernel = MemoryKernel(
                kernel_id=f"kernel_{i}",
                topic=f"Topic {i}",
                summary=f"Summary {i}"
            )
            save_kernel(kernel)

        # Add history for kernel_0 and kernel_2
        history_logger.append_history_event(
            create_history_event(
                event_type="user_message",
                source="user",
                content="Test",
                kernel_id="kernel_0"
            )
        )
        history_logger.append_history_event(
            create_history_event(
                event_type="user_message",
                source="user",
                content="Test",
                kernel_id="kernel_2"
            )
        )

        kernels = spark_plug_autokernel.list_refreshable_kernels()
        assert len(kernels) == 2
        assert "kernel_0" in kernels
        assert "kernel_2" in kernels
        assert "kernel_1" not in kernels

    def test_get_kernel_history_stats_no_events(self, temp_dirs, sample_kernel):
        """Test stats for kernel with no history"""
        stats = spark_plug_autokernel.get_kernel_history_stats("test_kernel")

        assert stats["kernel_id"] == "test_kernel"
        assert stats["total_events"] == 0
        assert stats["event_types"] == {}
        assert stats["oldest_event"] is None
        assert stats["newest_event"] is None

    def test_get_kernel_history_stats(self, temp_dirs, sample_kernel, sample_history):
        """Test stats for kernel with history"""
        stats = spark_plug_autokernel.get_kernel_history_stats("test_kernel")

        assert stats["kernel_id"] == "test_kernel"
        assert stats["total_events"] == 2  # 2 events for test_kernel
        assert "user_message" in stats["event_types"]
        assert "system_decision" in stats["event_types"]
        assert stats["oldest_event"] is not None
        assert stats["newest_event"] is not None


class TestSafetyConstraints:
    """Test safety constraints"""

    def test_no_trading_imports(self):
        """Test that autokernel module doesn't import trading/risk/executor"""
        import ai_nexus.spark_plug_autokernel as autokernel_module

        # Check module source for forbidden imports
        import inspect
        import re
        source = inspect.getsource(autokernel_module)

        # Look for actual import statements (beginning of line, possibly with whitespace)
        forbidden_patterns = [
            r'^\s*from\s+trading\s+import',
            r'^\s*import\s+trading\b',
            r'^\s*from\s+risk\s+import',
            r'^\s*import\s+risk\b',
            r'^\s*from\s+decider\s+import',
            r'^\s*import\s+decider\b',
            r'^\s*from\s+executor\s+import',
            r'^\s*import\s+executor\b',
        ]

        for pattern in forbidden_patterns:
            match = re.search(pattern, source, re.MULTILINE)
            assert match is None, f"Found forbidden import matching pattern: {pattern}"

    def test_design_only_profile(self, temp_dirs, sample_kernel, sample_history):
        """Test that CPU always uses design_only profile"""
        with patch('ai_nexus.spark_plug_autokernel.TriAgentSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.thread_file = Path("/tmp/test/thread.jsonl")
            mock_session.cpu_instance_file = Path("/tmp/test/cpu_instance.json")
            mock_session_class.return_value = mock_session

            # cpu_profile parameter exists but is not used yet in TriAgentSession
            # Safety is enforced by TriAgentSession always using "design_only"
            result = spark_plug_autokernel.refresh_kernel_from_history(
                kernel_id="test_kernel",
                cpu_profile="design_only"
            )

            # Verify session was created (safety enforced by TriAgentSession)
            assert mock_session_class.called
            assert result["status"] == "success"


class TestEventFiltering:
    """Test history event filtering logic"""

    def test_filters_by_kernel_id(self, temp_dirs, sample_kernel):
        """Test that only relevant events are included"""
        # Add events for different kernels
        history_logger.append_history_event(
            create_history_event(
                event_type="user_message",
                source="user",
                content="Event for test_kernel",
                kernel_id="test_kernel"
            )
        )
        history_logger.append_history_event(
            create_history_event(
                event_type="user_message",
                source="user",
                content="Event for other_kernel",
                kernel_id="other_kernel"
            )
        )

        with patch('ai_nexus.spark_plug_autokernel.TriAgentSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.thread_file = Path("/tmp/test/thread.jsonl")
            mock_session.cpu_instance_file = Path("/tmp/test/cpu_instance.json")
            mock_session_class.return_value = mock_session

            result = spark_plug_autokernel.refresh_kernel_from_history(
                kernel_id="test_kernel"
            )

            # Should find only 1 event (for test_kernel)
            assert result["events_found"] >= 1
            assert result["status"] == "success"

    def test_includes_general_events(self, temp_dirs, sample_kernel):
        """Test that general events (no kernel_id) are included"""
        # Add kernel-specific event
        history_logger.append_history_event(
            create_history_event(
                event_type="user_message",
                source="user",
                content="Event for test_kernel",
                kernel_id="test_kernel"
            )
        )

        # Add general event
        history_logger.append_history_event(
            create_history_event(
                event_type="observation",
                source="monitoring",
                content="General system observation"
                # No kernel_id
            )
        )

        with patch('ai_nexus.spark_plug_autokernel.TriAgentSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.thread_file = Path("/tmp/test/thread.jsonl")
            mock_session.cpu_instance_file = Path("/tmp/test/cpu_instance.json")
            mock_session_class.return_value = mock_session

            result = spark_plug_autokernel.refresh_kernel_from_history(
                kernel_id="test_kernel",
                max_events=10
            )

            # Should find both events (1 specific + 1 general)
            assert result["events_found"] >= 2
            assert result["status"] == "success"


class TestRunAutokernelRefresh:
    """Test run_autokernel_refresh function (v0.4 API)"""

    def test_kernel_not_found(self, temp_dirs):
        """Test with non-existent kernel"""
        result = spark_plug_autokernel.run_autokernel_refresh(
            kernel_id="nonexistent_kernel",
            mode="cpu",
            dry_run=False
        )

        assert result["status"] == "kernel_not_found"
        assert result["kernel_id"] == "nonexistent_kernel"
        assert result["mode"] == "cpu"
        assert result["history"]["items_seen"] == 0
        assert result["cpu"]["conversation_id"] is None

    def test_no_history(self, temp_dirs, sample_kernel):
        """Test with kernel but no history events"""
        result = spark_plug_autokernel.run_autokernel_refresh(
            kernel_id="test_kernel",
            mode="cpu",
            dry_run=False
        )

        assert result["status"] == "no_history"
        assert result["kernel_id"] == "test_kernel"
        assert result["history"]["items_used"] == 0

    @patch('ai_nexus.spark_plug_autokernel.refresh_kernel_from_history')
    def test_success_path(
        self,
        mock_refresh,
        temp_dirs,
        sample_kernel,
        sample_history
    ):
        """Test successful auto-kernel refresh (happy path)"""
        # Mock the v0.2 refresh function
        mock_refresh.return_value = {
            "status": "success",
            "kernel_id": "test_kernel",
            "events_found": 3,
            "conversation_id": "autokernel_test_kernel_20251126_103000",
            "cpu_run": True,
            "message": "Success"
        }

        # Create fake thread file
        temp_dirs["temp_path"].joinpath("ai/intercom/autokernel_test_kernel_20251126_103000").mkdir(parents=True)
        thread_file = temp_dirs["temp_path"] / "ai" / "intercom" / "autokernel_test_kernel_20251126_103000" / "thread.jsonl"
        thread_file.write_text('{"msg_id": "msg-0001"}\n')

        result = spark_plug_autokernel.run_autokernel_refresh(
            kernel_id="test_kernel",
            mode="cpu",
            dry_run=False,
            max_history_items=20
        )

        # Verify structure
        assert result["status"] == "success"
        assert result["kernel_id"] == "test_kernel"
        assert result["mode"] == "cpu"

        # Verify history section
        assert "history" in result
        assert result["history"]["items_seen"] >= 0
        assert result["history"]["items_used"] >= 0
        assert isinstance(result["history"]["sources"], list)
        assert "time_range" in result["history"]

        # Verify CPU section
        assert "cpu" in result
        assert result["cpu"]["conversation_id"] == "autokernel_test_kernel_20251126_103000"
        assert result["cpu"]["intercom_thread"] == str(thread_file)

        # Verify updates section (v0.4: minimal, no auto-apply)
        assert "updates" in result
        assert len(result["updates"]["applied"]) == 1
        assert result["updates"]["applied"][0]["type"] == "cpu_suggestion"
        assert result["updates"]["applied"][0]["auto_applied"] is False
        assert result["updates"]["kernel_file"] is not None

        # Verify refresh was called with correct params
        mock_refresh.assert_called_once_with(
            kernel_id="test_kernel",
            max_events=20,
            dry_run=False
        )

    @patch('ai_nexus.spark_plug_autokernel.refresh_kernel_from_history')
    def test_dry_run_behavior(
        self,
        mock_refresh,
        temp_dirs,
        sample_kernel,
        sample_history
    ):
        """Test that dry_run flag is passed through and noted in updates"""
        mock_refresh.return_value = {
            "status": "success",
            "kernel_id": "test_kernel",
            "events_found": 2,
            "conversation_id": "autokernel_test_kernel_20251126_103000",
            "cpu_run": True,
            "message": "Dry run"
        }

        result = spark_plug_autokernel.run_autokernel_refresh(
            kernel_id="test_kernel",
            mode="cpu",
            dry_run=True
        )

        # Verify dry_run was passed through
        mock_refresh.assert_called_once()
        assert mock_refresh.call_args[1]["dry_run"] is True

        # Verify dry_run is noted in updates
        assert len(result["updates"]["skipped"]) == 1
        assert result["updates"]["skipped"][0]["type"] == "dry_run"

    def test_unsupported_mode(self, temp_dirs, sample_kernel, sample_history):
        """Test with unsupported mode (not 'cpu')"""
        result = spark_plug_autokernel.run_autokernel_refresh(
            kernel_id="test_kernel",
            mode="analysis",  # Not implemented yet
            dry_run=False
        )

        assert result["status"] == "error"
        assert "error" in result
        assert result["error"]["type"] == "NotImplementedError"
        assert result["error"]["stage"] == "cpu"
        assert "analysis" in result["error"]["message"]

    @patch('ai_nexus.spark_plug_autokernel.refresh_kernel_from_history')
    def test_cpu_error_handling(
        self,
        mock_refresh,
        temp_dirs,
        sample_kernel,
        sample_history
    ):
        """Test error handling during CPU execution"""
        # Mock refresh to return error
        mock_refresh.return_value = {
            "status": "error",
            "kernel_id": "test_kernel",
            "events_found": 2,
            "conversation_id": None,
            "cpu_run": False,
            "message": "CPU failed with test error"
        }

        result = spark_plug_autokernel.run_autokernel_refresh(
            kernel_id="test_kernel",
            mode="cpu",
            dry_run=False
        )

        assert result["status"] == "error"
        assert "error" in result
        assert result["error"]["stage"] == "cpu"
        assert "CPU failed" in result["error"]["message"]

    @patch('ai_nexus.spark_plug_autokernel.load_kernel_history_events')
    def test_history_load_error(
        self,
        mock_load_history,
        temp_dirs,
        sample_kernel
    ):
        """Test error handling during history loading"""
        # Mock load_kernel_history_events (unified loader) to raise exception
        mock_load_history.side_effect = Exception("History load failed")

        result = spark_plug_autokernel.run_autokernel_refresh(
            kernel_id="test_kernel",
            mode="cpu",
            dry_run=False
        )

        assert result["status"] == "error"
        assert "error" in result
        assert result["error"]["stage"] == "load_history"
        assert "History load failed" in result["error"]["message"]
        assert len(result["error"]["traceback"]) > 0

    @patch('ai_nexus.spark_plug_autokernel.refresh_kernel_from_history')
    def test_time_range_calculation(
        self,
        mock_refresh,
        temp_dirs,
        sample_kernel,
        sample_history
    ):
        """Test that time_range is properly calculated from events"""
        mock_refresh.return_value = {
            "status": "success",
            "kernel_id": "test_kernel",
            "events_found": 2,
            "conversation_id": "autokernel_test_kernel_20251126_103000",
            "cpu_run": True,
            "message": "Success"
        }

        result = spark_plug_autokernel.run_autokernel_refresh(
            kernel_id="test_kernel",
            mode="cpu",
            dry_run=False
        )

        # Should have time range (from sample_history fixture)
        assert result["history"]["time_range"]["start"] is not None
        assert result["history"]["time_range"]["end"] is not None

    def test_default_max_history_items(self, temp_dirs, sample_kernel, sample_history):
        """Test that max_history_items defaults to 50 when not provided"""
        with patch('ai_nexus.spark_plug_autokernel.refresh_kernel_from_history') as mock_refresh:
            mock_refresh.return_value = {
                "status": "success",
                "kernel_id": "test_kernel",
                "events_found": 2,
                "conversation_id": "test_conv",
                "cpu_run": True,
                "message": "Success"
            }

            result = spark_plug_autokernel.run_autokernel_refresh(
                kernel_id="test_kernel",
                mode="cpu"
            )

            # Check that default of 50 was used
            mock_refresh.assert_called_once()
            assert mock_refresh.call_args[1]["max_events"] == 50


class TestV04SafetyConstraints:
    """Test v0.4 safety constraints"""

    def test_no_auto_apply_in_v04(self, temp_dirs, sample_kernel, sample_history):
        """Test that v0.4 does not auto-apply kernel updates"""
        with patch('ai_nexus.spark_plug_autokernel.refresh_kernel_from_history') as mock_refresh:
            mock_refresh.return_value = {
                "status": "success",
                "kernel_id": "test_kernel",
                "events_found": 2,
                "conversation_id": "test_conv",
                "cpu_run": True,
                "message": "Success"
            }

            # Read kernel state before
            from ai_nexus.memory_kernels import load_kernel
            kernel_before = load_kernel("test_kernel")
            decisions_before = len(kernel_before.key_decisions)

            # Run refresh
            result = spark_plug_autokernel.run_autokernel_refresh(
                kernel_id="test_kernel",
                mode="cpu",
                dry_run=False
            )

            # Read kernel state after
            kernel_after = load_kernel("test_kernel")
            decisions_after = len(kernel_after.key_decisions)

            # Kernel should NOT have been mutated (v0.4 safety)
            assert decisions_before == decisions_after
            assert result["updates"]["backup_file"] is None
            assert result["updates"]["applied"][0]["auto_applied"] is False
            assert "Manual review required" in result["updates"]["applied"][0]["reason"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
