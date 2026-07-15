#!/usr/bin/env python3
"""
Integration tests for AI Runner (Batch 15)

Tests cover:
- Task loading (normal + malformed)
- Task execution for all supported types
- Health checks and gating
- Error handling
- Result writing
- Task archiving
- DRYRUN safety
- CLI invocation
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ai import ho_ai_runner


class TestTaskLoading(unittest.TestCase):
    """Test task loading functionality"""

    def test_load_tasks_empty_directory(self):
        """Test loading from empty task directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tasks = ho_ai_runner.load_tasks(tmpdir)
            self.assertEqual(len(tasks), 0)

    def test_load_tasks_nonexistent_directory(self):
        """Test loading from nonexistent directory"""
        tasks = ho_ai_runner.load_tasks("/nonexistent/path")
        self.assertEqual(len(tasks), 0)

    def test_load_valid_task(self):
        """Test loading a valid task"""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_file = Path(tmpdir) / "task1.json"
            task_data = {
                "id": "task-001",
                "type": "health-check",
                "payload": {}
            }
            with open(task_file, 'w') as f:
                json.dump(task_data, f)

            tasks = ho_ai_runner.load_tasks(tmpdir)
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0]["id"], "task-001")
            self.assertEqual(tasks[0]["type"], "health-check")
            self.assertIn("_file_path", tasks[0])

    def test_load_malformed_json(self):
        """Test handling of malformed JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_file = Path(tmpdir) / "bad.json"
            with open(task_file, 'w') as f:
                f.write("{invalid json")

            tasks = ho_ai_runner.load_tasks(tmpdir)
            self.assertEqual(len(tasks), 0)

    def test_load_missing_required_fields(self):
        """Test handling of tasks missing required fields"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Missing 'type' field
            task_file = Path(tmpdir) / "incomplete.json"
            task_data = {"id": "task-001"}
            with open(task_file, 'w') as f:
                json.dump(task_data, f)

            tasks = ho_ai_runner.load_tasks(tmpdir)
            self.assertEqual(len(tasks), 0)

    def test_load_not_json_object(self):
        """Test handling of JSON that's not an object"""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_file = Path(tmpdir) / "array.json"
            with open(task_file, 'w') as f:
                json.dump(["not", "an", "object"], f)

            tasks = ho_ai_runner.load_tasks(tmpdir)
            self.assertEqual(len(tasks), 0)

    def test_load_tasks_ordered_by_age(self):
        """Test that tasks are loaded oldest first"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create tasks with different timestamps
            task1 = Path(tmpdir) / "task1.json"
            task2 = Path(tmpdir) / "task2.json"
            task3 = Path(tmpdir) / "task3.json"

            for i, task_file in enumerate([task1, task2, task3], 1):
                task_data = {
                    "id": f"task-{i:03d}",
                    "type": "health-check",
                    "payload": {}
                }
                with open(task_file, 'w') as f:
                    json.dump(task_data, f)

                # Set modification time to simulate age
                # (newer files have higher timestamps)
                os.utime(task_file, (1000 + i, 1000 + i))

            tasks = ho_ai_runner.load_tasks(tmpdir)
            self.assertEqual(len(tasks), 3)
            # Should be ordered oldest to newest
            self.assertEqual(tasks[0]["id"], "task-001")
            self.assertEqual(tasks[1]["id"], "task-002")
            self.assertEqual(tasks[2]["id"], "task-003")


class TestHealthCheckTask(unittest.TestCase):
    """Test health-check task execution"""

    def test_health_check_success(self):
        """Test health-check task with valid health file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create health file
            health_data = {
                "status": "ok",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "components": {}
            }
            health_file = Path(tmpdir) / "hands_off_health.json"
            with open(health_file, 'w') as f:
                json.dump(health_data, f)

            # Run task
            task = {"id": "hc-001", "type": "health-check", "payload": {}}
            result = ho_ai_runner.run_task(task, tmpdir)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["id"], "hc-001")
            self.assertEqual(result["result"], health_data)
            self.assertEqual(result["errors"], [])

    def test_health_check_missing_file(self):
        """Test health-check task with missing health file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            task = {"id": "hc-002", "type": "health-check", "payload": {}}
            result = ho_ai_runner.run_task(task, tmpdir)

            self.assertEqual(result["status"], "error")
            self.assertEqual(result["id"], "hc-002")
            self.assertEqual(len(result["errors"]), 1)
            self.assertIn("Health file not found", result["errors"][0])


class TestLatestSummaryTask(unittest.TestCase):
    """Test latest-summary task execution"""

    def test_latest_summary_success(self):
        """Test latest-summary task with valid summary file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create summary file
            summary_data = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "market_count": 42,
                "total_exposure": 1000.0
            }
            summary_file = Path(tmpdir) / "hands_off_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary_data, f)

            # Run task
            task = {"id": "ls-001", "type": "latest-summary", "payload": {}}
            result = ho_ai_runner.run_task(task, tmpdir)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["id"], "ls-001")
            self.assertEqual(result["result"], summary_data)
            self.assertEqual(result["errors"], [])

    def test_latest_summary_missing_file(self):
        """Test latest-summary task with missing summary file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            task = {"id": "ls-002", "type": "latest-summary", "payload": {}}
            result = ho_ai_runner.run_task(task, tmpdir)

            self.assertEqual(result["status"], "error")
            self.assertEqual(result["id"], "ls-002")
            self.assertEqual(len(result["errors"]), 1)
            self.assertIn("Summary file not found", result["errors"][0])


class TestGenerateHistoryReportTask(unittest.TestCase):
    """Test generate-history-report task execution"""

    def test_generate_history_report_available(self):
        """Test history report with missing module"""
        with tempfile.TemporaryDirectory() as tmpdir:
            task = {"id": "hr-001", "type": "generate-history-report", "payload": {}}
            result = ho_ai_runner.run_task(task, tmpdir)

            self.assertEqual(result["id"], "hr-001")
            self.assertIn(result["status"], ["ok", "error"])
            self.assertIsNotNone(result["errors"])

    def test_generate_history_report_with_mock(self):
        """Test history report with mocked module"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the import
            mock_module = mock.MagicMock()
            mock_summary = {
                "snapshot_count": 5,
                "date_range": "2025-11-01 to 2025-11-05",
                "metrics": {}
            }
            mock_module.summarize_history.return_value = mock_summary

            with mock.patch.dict('sys.modules', {'reports.ho_history_report': mock_module}):
                task = {"id": "hr-002", "type": "generate-history-report", "payload": {}}
                result = ho_ai_runner.run_task(task, tmpdir)

                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["id"], "hr-002")
                self.assertEqual(result["result"], mock_summary)


class TestRunAutoloopTask(unittest.TestCase):
    """Test run-autoloop task execution with health gating"""

    def test_autoloop_health_not_ok(self):
        """Test autoloop skips when health != ok"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create health file with non-ok status
            health_data = {
                "status": "degraded",
                "components": {}
            }
            health_file = Path(tmpdir) / "hands_off_health.json"
            with open(health_file, 'w') as f:
                json.dump(health_data, f)

            task = {"id": "al-001", "type": "run-autoloop", "payload": {}}
            result = ho_ai_runner.run_task(task, tmpdir)

            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["id"], "al-001")
            self.assertIn("Health check failed", result["result"]["reason"])

    def test_autoloop_missing_health_file(self):
        """Test autoloop skips when health file missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            task = {"id": "al-002", "type": "run-autoloop", "payload": {}}
            result = ho_ai_runner.run_task(task, tmpdir)

            self.assertEqual(result["status"], "skipped")
            self.assertIn("Health check failed", result["result"]["reason"])

    def test_autoloop_polymarket_not_fresh(self):
        """Test autoloop skips when polymarket data is stale"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create health file with stale polymarket data
            old_time = datetime.utcnow() - timedelta(minutes=10)
            health_data = {
                "status": "ok",
                "components": {
                    "polymarket_fetch": {
                        "status": "ok",
                        "last_update": old_time.isoformat() + "Z"
                    }
                }
            }
            health_file = Path(tmpdir) / "hands_off_health.json"
            with open(health_file, 'w') as f:
                json.dump(health_data, f)

            task = {"id": "al-003", "type": "run-autoloop", "payload": {}}
            result = ho_ai_runner.run_task(task, tmpdir)

            self.assertEqual(result["status"], "skipped")
            self.assertIn("not fresh", result["result"]["reason"])

    def test_autoloop_available(self):
        """Test autoloop with missing module"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create health file with fresh data
            fresh_time = datetime.utcnow() - timedelta(minutes=2)
            health_data = {
                "status": "ok",
                "components": {
                    "polymarket_fetch": {
                        "status": "ok",
                        "last_update": fresh_time.isoformat() + "Z"
                    }
                }
            }
            health_file = Path(tmpdir) / "hands_off_health.json"
            with open(health_file, 'w') as f:
                json.dump(health_data, f)

            task = {"id": "al-004", "type": "run-autoloop", "payload": {}}
            result = ho_ai_runner.run_task(task, tmpdir)

            # Should handle ImportError gracefully
            self.assertEqual(result["id"], task["id"])
            self.assertIn(result["status"], ["ok", "error", "skipped"])
            self.assertIsNotNone(result["errors"])

    def test_autoloop_with_fresh_health_and_mock(self):
        """Test autoloop executes when health is OK and data is fresh"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create health file with fresh data
            fresh_time = datetime.utcnow() - timedelta(minutes=2)
            health_data = {
                "status": "ok",
                "components": {
                    "polymarket_fetch": {
                        "status": "ok",
                        "last_update": fresh_time.isoformat() + "Z"
                    }
                }
            }
            health_file = Path(tmpdir) / "hands_off_health.json"
            with open(health_file, 'w') as f:
                json.dump(health_data, f)

            # Mock the autoloop module
            mock_module = mock.MagicMock()
            mock_result = {
                "executed": True,
                "mode": "DRYRUN",
                "markets_analyzed": 10
            }
            mock_module.run_all.return_value = mock_result

            with mock.patch.dict('sys.modules', {'scheduler.ho_autoloop': mock_module}):
                task = {"id": "al-005", "type": "run-autoloop", "payload": {}}
                result = ho_ai_runner.run_task(task, tmpdir)

                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["id"], "al-005")
                self.assertEqual(result["result"], mock_result)
                # Verify run_all was called with correct parameters
                mock_module.run_all.assert_called_once()


class TestUnknownTaskType(unittest.TestCase):
    """Test handling of unknown task types"""

    def test_unknown_task_type(self):
        """Test that unknown task types return error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            task = {"id": "unknown-001", "type": "unknown-type", "payload": {}}
            result = ho_ai_runner.run_task(task, tmpdir)

            self.assertEqual(result["status"], "error")
            self.assertEqual(result["id"], "unknown-001")
            self.assertEqual(len(result["errors"]), 1)
            self.assertIn("unknown task type", result["errors"][0])


class TestResultWriting(unittest.TestCase):
    """Test result writing functionality"""

    def test_write_result(self):
        """Test writing result to file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = os.path.join(tmpdir, "results")
            result = {
                "id": "task-001",
                "status": "ok",
                "result": {"data": "test"},
                "errors": []
            }

            result_path = ho_ai_runner.write_result(result, results_dir)

            # Check file exists
            self.assertTrue(os.path.exists(result_path))

            # Check content
            with open(result_path, 'r') as f:
                written_result = json.load(f)

            self.assertEqual(written_result["id"], "task-001")
            self.assertEqual(written_result["status"], "ok")
            self.assertIn("timestamp", written_result)

    def test_write_result_creates_directory(self):
        """Test that write_result creates results directory if needed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = os.path.join(tmpdir, "nonexistent", "results")
            result = {
                "id": "task-002",
                "status": "ok",
                "result": {},
                "errors": []
            }

            result_path = ho_ai_runner.write_result(result, results_dir)

            self.assertTrue(os.path.exists(result_path))
            self.assertTrue(os.path.isdir(results_dir))


class TestTaskArchiving(unittest.TestCase):
    """Test task archiving functionality"""

    def test_move_to_processed(self):
        """Test moving task to processed directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create task file
            tasks_dir = os.path.join(tmpdir, "tasks")
            os.makedirs(tasks_dir)
            task_file = os.path.join(tasks_dir, "task1.json")
            with open(task_file, 'w') as f:
                json.dump({"id": "task-001", "type": "health-check"}, f)

            # Move to processed
            processed_dir = os.path.join(tmpdir, "processed")
            archived_path = ho_ai_runner.move_to_processed(task_file, processed_dir)

            # Check original is gone
            self.assertFalse(os.path.exists(task_file))

            # Check archived file exists
            self.assertTrue(os.path.exists(archived_path))

    def test_move_to_processed_with_duplicate(self):
        """Test moving task when file with same name already exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create task file
            tasks_dir = os.path.join(tmpdir, "tasks")
            os.makedirs(tasks_dir)
            task_file = os.path.join(tasks_dir, "task1.json")
            with open(task_file, 'w') as f:
                json.dump({"id": "task-001"}, f)

            # Create duplicate in processed
            processed_dir = os.path.join(tmpdir, "processed")
            os.makedirs(processed_dir)
            existing_file = os.path.join(processed_dir, "task1.json")
            with open(existing_file, 'w') as f:
                json.dump({"id": "old-task"}, f)

            # Move to processed
            archived_path = ho_ai_runner.move_to_processed(task_file, processed_dir)

            # Check both files exist with different names
            self.assertTrue(os.path.exists(existing_file))
            self.assertTrue(os.path.exists(archived_path))
            self.assertNotEqual(archived_path, existing_file)


class TestRunnerIntegration(unittest.TestCase):
    """Integration tests for full runner execution"""

    def test_empty_task_list(self):
        """Test runner with no tasks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ai_dir = os.path.join(tmpdir, "ai")
            state_dir = os.path.join(tmpdir, "state")

            # Create directories
            os.makedirs(os.path.join(ai_dir, "tasks"))
            os.makedirs(state_dir)

            stats = ho_ai_runner.run_ai_runner(state_dir, ai_dir)

            self.assertEqual(stats["total_tasks"], 0)
            self.assertEqual(stats["executed"], 0)
            self.assertEqual(stats["ok"], 0)
            self.assertEqual(stats["skipped"], 0)
            self.assertEqual(stats["errored"], 0)

    def test_runner_with_multiple_tasks(self):
        """Test runner with multiple tasks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ai_dir = os.path.join(tmpdir, "ai")
            state_dir = os.path.join(tmpdir, "state")

            # Create directories
            tasks_dir = os.path.join(ai_dir, "tasks")
            os.makedirs(tasks_dir)
            os.makedirs(state_dir)

            # Create health file
            health_data = {"status": "ok", "components": {}}
            with open(os.path.join(state_dir, "hands_off_health.json"), 'w') as f:
                json.dump(health_data, f)

            # Create summary file
            summary_data = {"timestamp": datetime.utcnow().isoformat() + "Z"}
            with open(os.path.join(state_dir, "hands_off_summary.json"), 'w') as f:
                json.dump(summary_data, f)

            # Create tasks
            tasks = [
                {"id": "hc-001", "type": "health-check", "payload": {}},
                {"id": "ls-001", "type": "latest-summary", "payload": {}},
                {"id": "uk-001", "type": "unknown-type", "payload": {}},
            ]

            for task in tasks:
                task_file = os.path.join(tasks_dir, f"{task['id']}.json")
                with open(task_file, 'w') as f:
                    json.dump(task, f)

            # Run runner
            stats = ho_ai_runner.run_ai_runner(state_dir, ai_dir)

            # Check stats
            self.assertEqual(stats["total_tasks"], 3)
            self.assertEqual(stats["executed"], 3)
            self.assertEqual(stats["ok"], 2)
            self.assertEqual(stats["errored"], 1)

            # Check results were written
            results_dir = os.path.join(ai_dir, "results")
            self.assertEqual(len(os.listdir(results_dir)), 3)

            # Check tasks were archived
            processed_dir = os.path.join(ai_dir, "processed")
            self.assertEqual(len(os.listdir(processed_dir)), 3)

    def test_runner_summary_correctness(self):
        """Test that runner summary accurately reflects execution"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ai_dir = os.path.join(tmpdir, "ai")
            state_dir = os.path.join(tmpdir, "state")

            # Create directories
            tasks_dir = os.path.join(ai_dir, "tasks")
            os.makedirs(tasks_dir)
            os.makedirs(state_dir)

            # Create health file (not ok for skip test)
            health_data = {"status": "degraded", "components": {}}
            with open(os.path.join(state_dir, "hands_off_health.json"), 'w') as f:
                json.dump(health_data, f)

            # Create tasks: one will succeed, one will skip, one will error
            tasks = [
                {"id": "hc-001", "type": "health-check", "payload": {}},
                {"id": "al-001", "type": "run-autoloop", "payload": {}},
                {"id": "uk-001", "type": "invalid", "payload": {}},
            ]

            for task in tasks:
                task_file = os.path.join(tasks_dir, f"{task['id']}.json")
                with open(task_file, 'w') as f:
                    json.dump(task, f)

            # Run runner
            stats = ho_ai_runner.run_ai_runner(state_dir, ai_dir)

            # Verify counts
            self.assertEqual(stats["total_tasks"], 3)
            self.assertEqual(stats["executed"], 3)
            self.assertEqual(stats["ok"], 1)
            self.assertEqual(stats["skipped"], 1)
            self.assertEqual(stats["errored"], 1)

            # Verify results array
            self.assertEqual(len(stats["results"]), 3)
            for r in stats["results"]:
                self.assertIn("task_id", r)
                self.assertIn("status", r)
                self.assertIn("result_path", r)

    def test_dryrun_safety(self):
        """Test that runner operates in DRYRUN mode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ai_dir = os.path.join(tmpdir, "ai")
            state_dir = os.path.join(tmpdir, "state")

            # Create directories
            tasks_dir = os.path.join(ai_dir, "tasks")
            os.makedirs(tasks_dir)
            os.makedirs(state_dir)

            # Create health file with fresh data
            fresh_time = datetime.utcnow() - timedelta(minutes=1)
            health_data = {
                "status": "ok",
                "components": {
                    "polymarket_fetch": {
                        "status": "ok",
                        "last_update": fresh_time.isoformat() + "Z"
                    }
                }
            }
            with open(os.path.join(state_dir, "hands_off_health.json"), 'w') as f:
                json.dump(health_data, f)

            # Create autoloop task
            task = {"id": "al-dryrun", "type": "run-autoloop", "payload": {}}
            task_file = os.path.join(tasks_dir, "al-dryrun.json")
            with open(task_file, 'w') as f:
                json.dump(task, f)

            # Mock autoloop to verify DRYRUN mode
            mock_module = mock.MagicMock()

            def check_dryrun_mode(**kwargs):
                # Verify mode is DRYRUN
                assert kwargs.get("mode") == "DRYRUN", "Autoloop must run in DRYRUN mode"
                return {"executed": True, "mode": "DRYRUN"}

            mock_module.run_all.side_effect = check_dryrun_mode

            with mock.patch.dict('sys.modules', {'scheduler.ho_autoloop': mock_module}):
                stats = ho_ai_runner.run_ai_runner(state_dir, ai_dir)

                # Should have executed successfully
                self.assertEqual(stats["ok"], 1)


class TestCLIInvocation(unittest.TestCase):
    """Test CLI interface"""

    def test_cli_with_temp_directory(self):
        """Test CLI execution with temporary directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ai_dir = os.path.join(tmpdir, "ai")
            state_dir = os.path.join(tmpdir, "state")

            # Create minimal setup
            tasks_dir = os.path.join(ai_dir, "tasks")
            os.makedirs(tasks_dir)
            os.makedirs(state_dir)

            # Create a simple task
            task = {"id": "cli-001", "type": "health-check", "payload": {}}
            with open(os.path.join(tasks_dir, "task.json"), 'w') as f:
                json.dump(task, f)

            # Create health file
            health_data = {"status": "ok", "components": {}}
            with open(os.path.join(state_dir, "hands_off_health.json"), 'w') as f:
                json.dump(health_data, f)

            # Mock sys.argv
            with mock.patch('sys.argv', ['ho_ai_runner.py', '--state-dir', state_dir, '--ai-dir', ai_dir]):
                with mock.patch('sys.exit') as mock_exit:
                    ho_ai_runner.main()

                    # Should exit with success
                    mock_exit.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main()
