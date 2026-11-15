import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import scheduler


class SchedulerHardeningTests(unittest.TestCase):
    def setUp(self):
        self.temp = __import__("tempfile").TemporaryDirectory()
        self.state_dir = Path(self.temp.name)
        self.old_values = {
            "STATE": scheduler.STATE,
            "SCHEDULER_STATE": scheduler.SCHEDULER_STATE,
            "SCHEDULER_LOG": scheduler.SCHEDULER_LOG,
            "SCHEDULER_LOCK": scheduler.SCHEDULER_LOCK,
        }
        scheduler.STATE = self.state_dir
        scheduler.SCHEDULER_STATE = self.state_dir / "scheduler_state.json"
        scheduler.SCHEDULER_LOG = self.state_dir / "scheduler_log.json"
        scheduler.SCHEDULER_LOCK = self.state_dir / "scheduler.lock"

    def tearDown(self):
        for name, value in self.old_values.items():
            setattr(scheduler, name, value)
        self.temp.cleanup()

    def test_initial_schedule_is_staggered(self):
        state = scheduler.initialize_state(now=1000)
        due = [state["jobs"][task["name"]]["next_run_at"] for task in scheduler.TASKS]
        self.assertEqual(due, [1000, 1010, 1020, 1030])

    def test_next_run_survives_restart(self):
        state = scheduler.initialize_state(now=1000)
        job = state["jobs"][scheduler.TASKS[0]["name"]]
        job["last_started_at"] = 1000
        job["next_run_at"] = 1300
        scheduler.save_state(state)

        restored = scheduler.load_state()
        self.assertEqual(restored["jobs"][scheduler.TASKS[0]["name"]]["next_run_at"], 1300)
        self.assertEqual(restored["jobs"][scheduler.TASKS[0]["name"]]["last_started_at"], 1000)

    def test_lock_rejects_second_scheduler_instance(self):
        first = scheduler.acquire_lock()
        self.assertIsNotNone(first)
        try:
            second = scheduler.acquire_lock()
            self.assertIsNone(second)
        finally:
            scheduler.release_lock(first)

        third = scheduler.acquire_lock()
        self.assertIsNotNone(third)
        scheduler.release_lock(third)

    def test_run_task_uses_timeout_and_bounds_output(self):
        task = {"name": "sample", "script": "sample.py"}
        fake = mock.Mock(returncode=0, stdout="x" * 1000, stderr="")
        with mock.patch.object(scheduler.subprocess, "run", return_value=fake) as run:
            result = scheduler.run_task(task)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["output"]), scheduler.MAX_OUTPUT_CHARS)
        self.assertEqual(run.call_args.kwargs["timeout"], scheduler.TASK_TIMEOUT_SECONDS)

    def test_run_task_records_timeout_as_failure(self):
        task = {"name": "sample", "script": "sample.py"}
        error = scheduler.subprocess.TimeoutExpired("sample", 60)
        with mock.patch.object(scheduler.subprocess, "run", side_effect=error):
            result = scheduler.run_task(task)
        self.assertFalse(result["success"])
        self.assertIsNone(result["returncode"])

    def test_scheduler_log_is_bounded(self):
        scheduler.SCHEDULER_LOG.write_text(json.dumps([{"n": i} for i in range(100)]))
        scheduler.append_log({"n": 100})
        rows = json.loads(scheduler.SCHEDULER_LOG.read_text())
        self.assertEqual(len(rows), 100)
        self.assertEqual(rows[-1]["n"], 100)

    def test_periodic_operations_have_one_declared_owner(self):
        node1 = (ROOT / "scripts" / "node1_runtime.py").read_text()
        cycle = (ROOT / "scripts" / "improvement_cycle.py").read_text()
        scheduler_source = (ROOT / "scripts" / "scheduler.py").read_text()

        # Node 1 consumes generated candidates and owns safe application only.
        self.assertNotIn("generate_improvements", node1)
        self.assertIn("applier.apply_batch(candidates)", node1)
        self.assertIn('"improvement_state.json"', node1)

        # The improvement cycle no longer duplicates scheduler/Node 1 jobs.
        for duplicate in (
            "health_monitor.py",
            "learning_loop.py",
            "state_integrity.py",
            "lifecycle_projection.py",
        ):
            self.assertNotIn(duplicate, cycle)

        # Each periodic script is registered once by the scheduler.
        self.assertIn('"health_check"', scheduler_source)
        self.assertIn('"improvement_cycle"', scheduler_source)
        self.assertIn('"integrity_check"', scheduler_source)
        self.assertIn('"learning_analysis"', scheduler_source)
        self.assertEqual(scheduler_source.count('"script": "improvement_cycle.py"'), 1)


if __name__ == "__main__":
    unittest.main()
