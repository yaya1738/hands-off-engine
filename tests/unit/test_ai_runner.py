"""
Unit tests for AI-Runner (v0.4) with Spark Plug integration

Tests task processing, especially sparkplug_autokernel_refresh task type.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import ai_runner


@pytest.fixture
def temp_task_dirs(monkeypatch):
    """Create temporary directories for tasks and results"""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        tasks_dir = temp_path / "tasks"
        results_dir = temp_path / "results"
        processed_dir = tasks_dir / "processed"
        config_dir = temp_path / "config"

        tasks_dir.mkdir()
        results_dir.mkdir()
        processed_dir.mkdir()
        config_dir.mkdir()

        # Override paths in ai_runner module
        monkeypatch.setattr(ai_runner, "TASKS_DIR", tasks_dir)
        monkeypatch.setattr(ai_runner, "RESULTS_DIR", results_dir)
        monkeypatch.setattr(ai_runner, "PROCESSED_DIR", processed_dir)
        monkeypatch.setattr(ai_runner, "CONFIG_DIR", config_dir)
        monkeypatch.setattr(ai_runner, "SPARKPLUG_CONFIG", config_dir / "sparkplug_kernels.json")

        yield {
            "tasks_dir": tasks_dir,
            "results_dir": results_dir,
            "processed_dir": processed_dir,
            "config_dir": config_dir,
            "temp_path": temp_path
        }


@pytest.fixture
def sample_sparkplug_config(temp_task_dirs):
    """Create a sample Spark Plug config file"""
    config = {
        "version": 1,
        "kernels": [
            {
                "kernel_id": "kernel_1",
                "mode": "cpu",
                "enabled": True,
                "notes": "Test kernel 1"
            },
            {
                "kernel_id": "kernel_2",
                "mode": "cpu",
                "enabled": True,
                "notes": "Test kernel 2"
            },
            {
                "kernel_id": "kernel_3",
                "mode": "cpu",
                "enabled": False,
                "notes": "Disabled kernel"
            }
        ]
    }

    config_file = temp_task_dirs["config_dir"] / "sparkplug_kernels.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    return config_file


class TestProcessSparkplugAutokernelRefresh:
    """Test process_sparkplug_autokernel_refresh function"""

    @patch('ai_runner.run_autokernel_refresh')
    def test_config_mode_success(
        self,
        mock_run_refresh,
        temp_task_dirs,
        sample_sparkplug_config
    ):
        """Test config-driven mode with successful refreshes"""
        # Mock run_autokernel_refresh to return success
        mock_run_refresh.side_effect = [
            {
                "status": "success",
                "kernel_id": "kernel_1",
                "history": {"items_seen": 10, "items_used": 5},
                "cpu": {"conversation_id": "conv_1"}
            },
            {
                "status": "success",
                "kernel_id": "kernel_2",
                "history": {"items_seen": 8, "items_used": 3},
                "cpu": {"conversation_id": "conv_2"}
            }
        ]

        # Create task
        task = {
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": "test_task_001",
            "mode": "config"
        }

        # Process task
        result = ai_runner.process_sparkplug_autokernel_refresh(task)

        # Verify result structure
        assert result["status"] == "success"
        assert result["task_type"] == "sparkplug_autokernel_refresh"
        assert result["task_id"] == "test_task_001"
        assert "run_at" in result

        # Verify summary
        assert result["summary"]["total_kernels"] == 2  # Only enabled kernels
        assert result["summary"]["success"] == 2
        assert result["summary"]["errors"] == 0

        # Verify kernels list
        assert len(result["kernels"]) == 2
        assert result["kernels"][0]["kernel_id"] == "kernel_1"
        assert result["kernels"][1]["kernel_id"] == "kernel_2"

        # Verify run_autokernel_refresh was called correctly
        assert mock_run_refresh.call_count == 2

    @patch('ai_runner.run_autokernel_refresh')
    def test_explicit_mode_success(
        self,
        mock_run_refresh,
        temp_task_dirs
    ):
        """Test explicit kernel list mode"""
        mock_run_refresh.return_value = {
            "status": "success",
            "kernel_id": "custom_kernel",
            "history": {"items_seen": 5, "items_used": 2},
            "cpu": {"conversation_id": "conv_custom"}
        }

        # Create task with explicit kernel list
        task = {
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": "test_task_002",
            "mode": "explicit",
            "kernels": [
                {"kernel_id": "custom_kernel", "mode": "cpu"}
            ],
            "dry_run": True
        }

        result = ai_runner.process_sparkplug_autokernel_refresh(task)

        assert result["status"] == "success"
        assert result["summary"]["total_kernels"] == 1
        assert result["kernels"][0]["kernel_id"] == "custom_kernel"

        # Verify dry_run was passed through
        mock_run_refresh.assert_called_once_with(
            kernel_id="custom_kernel",
            mode="cpu",
            dry_run=True
        )

    @patch('ai_runner.run_autokernel_refresh')
    def test_mixed_status_results(
        self,
        mock_run_refresh,
        temp_task_dirs,
        sample_sparkplug_config
    ):
        """Test handling mixed success/error/no_history results"""
        mock_run_refresh.side_effect = [
            {"status": "success", "kernel_id": "kernel_1"},
            {"status": "no_history", "kernel_id": "kernel_2"},
        ]

        task = {
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": "test_task_003",
            "mode": "config"
        }

        result = ai_runner.process_sparkplug_autokernel_refresh(task)

        assert result["status"] == "success"
        assert result["summary"]["total_kernels"] == 2
        assert result["summary"]["success"] == 1
        assert result["summary"]["no_history"] == 1
        assert result["summary"]["errors"] == 0

    @patch('ai_runner.run_autokernel_refresh')
    def test_kernel_error_does_not_abort_task(
        self,
        mock_run_refresh,
        temp_task_dirs,
        sample_sparkplug_config
    ):
        """Test that single kernel error doesn't abort entire task"""
        mock_run_refresh.side_effect = [
            {"status": "error", "kernel_id": "kernel_1", "error": {"message": "Test error"}},
            {"status": "success", "kernel_id": "kernel_2"},
        ]

        task = {
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": "test_task_004",
            "mode": "config"
        }

        result = ai_runner.process_sparkplug_autokernel_refresh(task)

        # Task should succeed even with kernel error
        assert result["status"] == "success"
        assert result["summary"]["errors"] == 1
        assert result["summary"]["success"] == 1
        assert len(result["kernels"]) == 2

    def test_config_not_found(self, temp_task_dirs):
        """Test error when config file doesn't exist"""
        task = {
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": "test_task_005",
            "mode": "config"
        }

        result = ai_runner.process_sparkplug_autokernel_refresh(task)

        assert result["status"] == "error"
        assert "error" in result
        assert result["error"]["type"] == "ConfigNotFound"
        assert "stage" in result["error"]

    def test_invalid_mode(self, temp_task_dirs):
        """Test error with invalid mode"""
        task = {
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": "test_task_006",
            "mode": "invalid_mode"
        }

        result = ai_runner.process_sparkplug_autokernel_refresh(task)

        assert result["status"] == "error"
        assert result["error"]["type"] == "InvalidMode"

    @patch('ai_runner.run_autokernel_refresh')
    def test_exception_during_kernel_processing(
        self,
        mock_run_refresh,
        temp_task_dirs,
        sample_sparkplug_config
    ):
        """Test handling of unexpected exceptions"""
        # First call succeeds, second raises exception
        mock_run_refresh.side_effect = [
            {"status": "success", "kernel_id": "kernel_1"},
            Exception("Unexpected error")
        ]

        task = {
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": "test_task_007",
            "mode": "config"
        }

        result = ai_runner.process_sparkplug_autokernel_refresh(task)

        # Should handle exception gracefully
        assert result["status"] == "success"
        assert result["summary"]["success"] == 1
        assert result["summary"]["errors"] == 1
        assert len(result["kernels"]) == 2
        assert result["kernels"][1]["result"]["status"] == "error"

    @patch('ai_runner.run_autokernel_refresh')
    def test_empty_kernel_list(self, mock_run_refresh, temp_task_dirs):
        """Test with empty kernel list"""
        task = {
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": "test_task_008",
            "mode": "explicit",
            "kernels": []
        }

        result = ai_runner.process_sparkplug_autokernel_refresh(task)

        assert result["status"] == "success"
        assert result["summary"]["total_kernels"] == 0
        assert len(result["kernels"]) == 0
        mock_run_refresh.assert_not_called()


class TestTaskDispatcher:
    """Test process_task function"""

    @patch('ai_runner.process_sparkplug_autokernel_refresh')
    def test_dispatch_sparkplug_task(
        self,
        mock_process_sparkplug,
        temp_task_dirs
    ):
        """Test dispatching sparkplug_autokernel_refresh task"""
        mock_process_sparkplug.return_value = {
            "status": "success",
            "task_type": "sparkplug_autokernel_refresh"
        }

        # Create task file
        task = {
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": "test_dispatch_001",
            "mode": "config"
        }
        task_file = temp_task_dirs["tasks_dir"] / "test_task.json"
        with open(task_file, 'w') as f:
            json.dump(task, f)

        # Process task
        result = ai_runner.process_task(task_file)

        assert result["status"] == "success"
        mock_process_sparkplug.assert_called_once()

    def test_dispatch_unsupported_task_type(self, temp_task_dirs):
        """Test dispatching unsupported task type"""
        task = {
            "task_type": "unsupported_task_type",
            "task_id": "test_dispatch_002"
        }
        task_file = temp_task_dirs["tasks_dir"] / "test_task.json"
        with open(task_file, 'w') as f:
            json.dump(task, f)

        result = ai_runner.process_task(task_file)

        assert result["status"] == "error"
        assert result["error"]["type"] == "UnsupportedTaskType"

    def test_dispatch_invalid_json(self, temp_task_dirs):
        """Test dispatching invalid JSON file"""
        task_file = temp_task_dirs["tasks_dir"] / "invalid.json"
        task_file.write_text("{invalid json")

        result = ai_runner.process_task(task_file)

        assert result["status"] == "error"
        assert result["error"]["type"] == "InvalidTaskFile"


class TestResultWriting:
    """Test write_result and move_task_to_processed functions"""

    def test_write_result(self, temp_task_dirs):
        """Test writing result to ai/results/"""
        result = {
            "status": "success",
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": "test_result_001"
        }
        task_file = temp_task_dirs["tasks_dir"] / "test_task.json"
        task_file.touch()

        result_path = ai_runner.write_result(result, task_file)

        # Verify result file was created
        assert result_path.exists()
        assert result_path.parent == temp_task_dirs["results_dir"]

        # Verify content
        with open(result_path) as f:
            saved_result = json.load(f)
        assert saved_result["status"] == "success"
        assert saved_result["task_id"] == "test_result_001"

    def test_move_task_to_processed(self, temp_task_dirs):
        """Test moving task file to processed directory"""
        task_file = temp_task_dirs["tasks_dir"] / "test_task.json"
        task_file.write_text('{"task_id": "test"}')

        new_path = ai_runner.move_task_to_processed(task_file)

        # Verify file was moved
        assert not task_file.exists()
        assert new_path.exists()
        assert new_path.parent == temp_task_dirs["processed_dir"]

    def test_move_task_with_duplicate_name(self, temp_task_dirs):
        """Test moving task when file with same name already exists"""
        task_file = temp_task_dirs["tasks_dir"] / "test_task.json"
        task_file.write_text('{"task_id": "test"}')

        # Create existing file in processed
        existing = temp_task_dirs["processed_dir"] / "test_task.json"
        existing.write_text('{"task_id": "old"}')

        new_path = ai_runner.move_task_to_processed(task_file)

        # Should create file with timestamp suffix
        assert new_path.exists()
        assert new_path.name != "test_task.json"
        assert "test_task_" in new_path.name


class TestIntegration:
    """Integration tests for end-to-end task processing"""

    @patch('ai_runner.run_autokernel_refresh')
    def test_end_to_end_config_mode(
        self,
        mock_run_refresh,
        temp_task_dirs,
        sample_sparkplug_config
    ):
        """Test complete flow from task file to result file"""
        mock_run_refresh.side_effect = [
            {"status": "success", "kernel_id": "kernel_1"},
            {"status": "success", "kernel_id": "kernel_2"},
        ]

        # Create task file
        task = {
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": "integration_test_001",
            "mode": "config"
        }
        task_file = temp_task_dirs["tasks_dir"] / "integration_test.json"
        with open(task_file, 'w') as f:
            json.dump(task, f)

        # Process task
        result = ai_runner.process_task(task_file)

        # Write result
        result_path = ai_runner.write_result(result, task_file)

        # Move task to processed
        processed_path = ai_runner.move_task_to_processed(task_file)

        # Verify result file exists
        assert result_path.exists()
        with open(result_path) as f:
            saved_result = json.load(f)
        assert saved_result["status"] == "success"
        assert saved_result["summary"]["total_kernels"] == 2

        # Verify task was moved
        assert not task_file.exists()
        assert processed_path.exists()


class TestSafetyConstraints:
    """Test v0.4 safety constraints"""

    def test_no_trading_imports(self):
        """Test that ai_runner doesn't import trading/risk/executor"""
        import inspect
        import re

        source = inspect.getsource(ai_runner)

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
