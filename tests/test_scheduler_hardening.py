import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import scheduler, improvement_cycle


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

    def test_malformed_job_entries_are_ignored(self):
        scheduler.SCHEDULER_STATE.write_text(json.dumps({
            "jobs": {"health_check": "invalid", "integrity_check": {"next_run_at": 123}}
        }))
        restored = scheduler.load_state()
        self.assertNotIn("health_check", restored["jobs"])
        self.assertEqual(restored["jobs"]["integrity_check"]["next_run_at"], 123)

    def test_missing_due_time_is_initialized_once(self):
        job = {}
        due_at = scheduler.get_due_time(job, scheduler.TASKS[0], now=100)
        self.assertEqual(due_at, 400)
        self.assertEqual(job["next_run_at"], 400)

        # A later poll must retain the original deadline, not postpone it.
        self.assertEqual(scheduler.get_due_time(job, scheduler.TASKS[0], now=200), 400)

    def test_missing_due_time_is_persisted_by_scheduler_loop(self):
        previous_running = scheduler._RUNNING
        state = {"jobs": {"health_check": {}}}
        try:
            with mock.patch.object(scheduler, "TASKS", [scheduler.TASKS[0]]), mock.patch.object(scheduler, "acquire_lock", return_value=object()), mock.patch.object(scheduler, "release_lock"), mock.patch.object(scheduler, "load_state", return_value=state), mock.patch.object(scheduler.time, "time", return_value=100), mock.patch.object(scheduler.time, "sleep", side_effect=lambda _: setattr(scheduler, "_RUNNING", False)):
                scheduler.run_forever()
            saved = json.loads(scheduler.SCHEDULER_STATE.read_text())
            self.assertEqual(saved["jobs"]["health_check"]["next_run_at"], 400)
        finally:
            scheduler._RUNNING = previous_running

    def test_boolean_due_times_are_repaired_before_numeric_conversion(self):
        for raw_due in (True, False):
            with self.subTest(raw_due=raw_due):
                job = {"next_run_at": raw_due}
                due_at = scheduler.get_due_time(job, scheduler.TASKS[0], now=100)
                self.assertEqual(due_at, 400)
                self.assertEqual(job["next_run_at"], 400)
                self.assertIs(type(job["next_run_at"]), int)

    def test_boolean_due_time_repair_is_persisted_by_scheduler_loop(self):
        previous_running = scheduler._RUNNING
        state = {"jobs": {"health_check": {"next_run_at": True}}}
        try:
            with mock.patch.object(scheduler, "TASKS", [scheduler.TASKS[0]]), \
                 mock.patch.object(scheduler, "acquire_lock", return_value=object()), \
                 mock.patch.object(scheduler, "release_lock"), \
                 mock.patch.object(scheduler, "load_state", return_value=state), \
                 mock.patch.object(scheduler.time, "time", return_value=100), \
                 mock.patch.object(scheduler.time, "sleep", side_effect=lambda _: setattr(scheduler, "_RUNNING", False)):
                scheduler.run_forever()
            saved = json.loads(scheduler.SCHEDULER_STATE.read_text())
            self.assertEqual(saved["jobs"]["health_check"]["next_run_at"], 400)
        finally:
            scheduler._RUNNING = previous_running

    def test_scheduler_is_owned_by_primary_supervisor_only(self):
        primary = (ROOT / "scripts" / "supervisor.py").read_text()
        termux = (ROOT / "scripts" / "termux_supervisor.py").read_text()
        self.assertIn('"name": "factory_scheduler"', primary)
        self.assertIn('"scheduler.py"', primary)
        self.assertNotIn('"scheduler.py"', termux)

    def test_event_router_and_control_room_have_single_owners(self):
        from scripts import termux_supervisor

        node1 = (ROOT / "scripts" / "node1_runtime.py").read_text()
        primary = (ROOT / "scripts" / "supervisor.py").read_text()
        self.assertIn("from scripts.event_router import EventRouter", node1)
        self.assertIn("router.process_once()", node1)
        self.assertIn('"name": "control_room"', primary)
        self.assertNotIn("event_router", termux_supervisor.DAEMONS)
        self.assertNotIn("control_room", termux_supervisor.DAEMONS)

    def test_malformed_due_time_is_recovered_without_crashing(self):
        job = {"next_run_at": "not-a-time"}
        due_at = scheduler.get_due_time(job, scheduler.TASKS[0], now=100)
        self.assertEqual(due_at, 400)
        self.assertEqual(job["next_run_at"], 400)

    def test_numeric_string_due_time_is_normalized(self):
        job = {"next_run_at": "123"}
        due_at = scheduler.get_due_time(job, scheduler.TASKS[0], now=100)
        self.assertEqual(due_at, 123)
        self.assertEqual(job["next_run_at"], 123)

    def test_non_finite_due_time_is_recovered(self):
        job = {"next_run_at": "nan"}
        due_at = scheduler.get_due_time(job, scheduler.TASKS[0], now=100)
        self.assertEqual(due_at, 400)
        self.assertEqual(job["next_run_at"], 400)

    def test_non_finite_numeric_due_time_is_persistently_repaired(self):
        job = {"next_run_at": float("nan")}
        due_at = scheduler.get_due_time(job, scheduler.TASKS[0], now=100)
        self.assertEqual(due_at, 400)
        self.assertEqual(job["next_run_at"], 400)

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

    def test_run_task_uses_file_backed_bounded_output(self):
        task = {"name": "sample", "script": "sample.py"}
        process = mock.Mock(pid=123, returncode=0)
        process.wait.return_value = 0

        def fake_popen(*args, **kwargs):
            # Simulate output far beyond the retained tail limit.
            kwargs["stdout"].write(b"x" * (scheduler.MAX_OUTPUT_CHARS * 100))
            return process

        with mock.patch.object(scheduler.subprocess, "Popen", side_effect=fake_popen) as popen:
            result = scheduler.run_task(task)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["output"]), scheduler.MAX_OUTPUT_CHARS)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        self.assertNotEqual(popen.call_args.kwargs["stdout"], scheduler.subprocess.PIPE)
        self.assertTrue(popen.call_args.kwargs["stdout"].closed)

    def test_run_task_kills_process_group_on_timeout(self):
        task = {"name": "sample", "script": "sample.py"}
        process = mock.Mock(pid=456, returncode=None)
        process.wait.side_effect = [
            scheduler.subprocess.TimeoutExpired("sample", scheduler.TASK_TIMEOUT_SECONDS),
            -9,
        ]
        process.returncode = -9

        with mock.patch.object(scheduler.subprocess, "Popen", return_value=process), \
             mock.patch.object(scheduler.os, "killpg") as killpg:
            result = scheduler.run_task(task)

        self.assertFalse(result["success"])
        killpg.assert_called_once_with(456, scheduler.signal.SIGKILL)
        self.assertEqual(process.wait.call_count, 2)

    def test_scheduler_log_is_bounded(self):
        scheduler.SCHEDULER_LOG.write_text(json.dumps([{"n": i} for i in range(100)]))
        scheduler.append_log({"n": 100})
        rows = json.loads(scheduler.SCHEDULER_LOG.read_text())
        self.assertEqual(len(rows), 100)
        self.assertEqual(rows[-1]["n"], 100)

    def test_improvement_cycle_subprocess_output_is_file_backed_and_bounded(self):
        process = mock.Mock(pid=789, returncode=0)
        process.wait.return_value = 0

        def fake_popen(*args, **kwargs):
            kwargs["stdout"].write(b"z" * (improvement_cycle.MAX_SUBPROCESS_OUTPUT_CHARS * 100))
            return process

        with mock.patch.object(improvement_cycle.subprocess, "Popen", side_effect=fake_popen) as popen:
            result = improvement_cycle.run_subprocess("sample.py")

        self.assertTrue(result["success"])
        self.assertEqual(len(result["output"]), improvement_cycle.MAX_SUBPROCESS_OUTPUT_CHARS)
        self.assertNotEqual(popen.call_args.kwargs["stdout"], improvement_cycle.subprocess.PIPE)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        self.assertTrue(popen.call_args.kwargs["stdout"].closed)

    def test_improvement_cycle_subprocess_kills_process_group_on_timeout(self):
        process = mock.Mock(pid=987, returncode=-9)
        process.wait.side_effect = [
            improvement_cycle.subprocess.TimeoutExpired("sample", improvement_cycle.SUBPROCESS_TIMEOUT_SECONDS),
            -9,
        ]

        with mock.patch.object(improvement_cycle.subprocess, "Popen", return_value=process), \
             mock.patch.object(improvement_cycle.os, "killpg") as killpg:
            result = improvement_cycle.run_subprocess("sample.py")

        self.assertFalse(result["success"])
        killpg.assert_called_once_with(987, improvement_cycle.signal.SIGKILL)
        self.assertEqual(process.wait.call_count, 2)

    def test_apply_generated_candidates_reads_snapshot_and_calls_applier_once(self):
        candidate = {"id": "imp-123", "action": "update_documentation"}
        snapshot = self.state_dir / "improvement_state.json"
        snapshot.write_text(json.dumps({"improvements": [candidate]}))
        fake_applier = mock.Mock()
        fake_applier.apply_batch.return_value = [{"applied": True, "id": "imp-123"}]

        with mock.patch.object(improvement_cycle, "STATE", self.state_dir), \
             mock.patch.object(improvement_cycle, "ROOT", ROOT), \
             mock.patch("scripts.improvement_applier.ImprovementApplier", return_value=fake_applier):
            result = improvement_cycle.apply_generated_candidates()

        self.assertEqual(result, [{"applied": True, "id": "imp-123"}])
        fake_applier.apply_batch.assert_called_once_with([candidate])

    def test_cycle_does_not_apply_when_candidate_generation_fails(self):
        fake_results = [
            {"success": False, "output": "generation failed"},
            {"success": True, "output": "status ok"},
            {"success": True, "output": "feedback ok"},
            {"success": True, "output": "approval ok"},
        ]
        with mock.patch.object(improvement_cycle, "STATE", self.state_dir), \
             mock.patch.object(improvement_cycle, "CYCLE_LOG", self.state_dir / "cycles.json"), \
             mock.patch.object(improvement_cycle, "run_subprocess", side_effect=fake_results), \
             mock.patch.object(improvement_cycle, "apply_generated_candidates") as apply:
            result = improvement_cycle.main()

        apply.assert_not_called()
        self.assertFalse(result["applier_apply"])
        self.assertEqual(result["applied_count"], 0)

    def test_periodic_operations_have_one_declared_owner(self):
        node1 = (ROOT / "scripts" / "node1_runtime.py").read_text()
        cycle = (ROOT / "scripts" / "improvement_cycle.py").read_text()
        scheduler_source = (ROOT / "scripts" / "scheduler.py").read_text()

        # Candidate generation/dispatch and apply have one periodic owner.
        self.assertNotIn("generate_improvements", node1)
        self.assertNotIn("apply_batch(", node1)
        self.assertIn("apply_batch(candidates)", cycle)
        self.assertIn("apply_generated_candidates()", cycle)

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