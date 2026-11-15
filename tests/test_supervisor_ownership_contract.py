"""Regression tests for supervisor lock/PID ownership boundaries."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import supervisor


class SupervisorOwnershipContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        logs = root / "logs"
        logs.mkdir()
        self.pid = root / "supervisor.pid"
        self.lock = root / "supervisor.lock"
        self.state = root / "supervisor_state.json"
        self.log = logs / "supervisor.log"
        self.patchers = [
            mock.patch.object(supervisor, "STATE", root),
            mock.patch.object(supervisor, "LOG_DIR", logs),
            mock.patch.object(supervisor, "SUPERVISOR_PID", self.pid),
            mock.patch.object(supervisor, "SUPERVISOR_LOCK", self.lock),
            mock.patch.object(supervisor, "SUPERVISOR_LOG", self.log),
            mock.patch.object(supervisor, "WATCHDOG_STATE", self.state),
            mock.patch.object(supervisor, "SERVICES", []),
        ]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_contending_lock_attempt_does_not_truncate_owner_data(self):
        self.lock.write_text("owner-record")
        owner = supervisor._acquire_lock(self.lock)
        self.assertIsNotNone(owner)
        owner_record = self.lock.read_text()
        self.assertEqual(owner_record, str(os.getpid()))
        try:
            self.assertIsNone(supervisor._acquire_lock(self.lock))
            self.assertEqual(self.lock.read_text(), owner_record)
        finally:
            os.close(owner)

    def test_duplicate_supervisor_cannot_overwrite_registered_pid(self):
        owner = supervisor._acquire_lock(self.lock)
        self.assertIsNotNone(owner)
        self.pid.write_text("4242")
        try:
            supervisor.run(max_loops=1)
            self.assertEqual(self.pid.read_text(), "4242")
        finally:
            os.close(owner)

    def test_pid_is_written_only_after_lock_is_acquired(self):
        original = supervisor._write_pid_file
        def checked_write():
            self.assertTrue(supervisor._lock_is_held(self.lock))
            original()
        with mock.patch.object(supervisor, "_write_pid_file", side_effect=checked_write):
            supervisor.run(max_loops=1)
        self.assertFalse(self.pid.exists())
        self.assertFalse(supervisor._lock_is_held(self.lock))

    def test_stop_predicate_rejects_matching_non_owner_pid(self):
        self.pid.write_text("111")
        with mock.patch.object(supervisor, "_is_process_alive", return_value=True), \
             mock.patch.object(supervisor, "_lock_is_held", return_value=True), \
             mock.patch.object(supervisor, "_is_supervisor_process", return_value=True):
            self.assertFalse(supervisor._can_signal_supervisor(222))

    def test_stop_predicate_accepts_registered_live_owner_only(self):
        self.pid.write_text("111")
        with mock.patch.object(supervisor, "_is_process_alive", return_value=True), \
             mock.patch.object(supervisor, "_lock_is_held", return_value=True), \
             mock.patch.object(supervisor, "_is_supervisor_process", return_value=True), \
             mock.patch.object(supervisor, "_lock_owner_pid", return_value=111):
            self.assertTrue(supervisor._can_signal_supervisor(111))

    def test_stop_refuses_registered_process_that_does_not_own_lock(self):
        self.pid.write_text("111")
        with mock.patch.object(supervisor, "_is_process_alive", return_value=True), \
             mock.patch.object(supervisor, "_lock_is_held", return_value=True), \
             mock.patch.object(supervisor, "_is_supervisor_process", return_value=True), \
             mock.patch.object(supervisor, "_lock_owner_pid", return_value=222):
            self.assertFalse(supervisor._can_signal_supervisor(111))

    def test_heartbeat_verdict_distinguishes_idle_stale_and_hung(self):
        heartbeat = self.state.parent / "scheduler_heartbeat.json"
        heartbeat.write_text(json.dumps({
            "pid": 321, "phase": "idle", "task": None,
            "task_deadline": None, "updated_at": 990.0,
        }))
        self.assertEqual(supervisor._heartbeat_verdict(heartbeat, 1000.0, expected_pid=321), "ok")
        self.assertEqual(supervisor._heartbeat_verdict(heartbeat, 1200.0, expected_pid=321), "stale")

        heartbeat.write_text(json.dumps({
            "pid": 321, "phase": "task", "task": "integrity_check",
            "task_deadline": 1060.0, "updated_at": 1000.0,
        }))
        self.assertEqual(supervisor._heartbeat_verdict(heartbeat, 1080.0, expected_pid=321), "ok")
        self.assertEqual(supervisor._heartbeat_verdict(heartbeat, 1091.0, expected_pid=321), "hung")

    def test_exit_75_requires_verified_scheduler_process_owner(self):
        heartbeat = self.state.parent / "scheduler_heartbeat.json"
        heartbeat.write_text(json.dumps({
            "pid": 321, "phase": "idle", "task": None,
            "task_deadline": None, "updated_at": 1000.0,
        }))
        service = {"singleton_lock": self.lock, "heartbeat": heartbeat}
        with mock.patch.object(supervisor, "_lock_is_held", return_value=True), \
             mock.patch.object(supervisor, "_is_process_alive", return_value=True), \
             mock.patch.object(supervisor, "_is_scheduler_process", return_value=False):
            self.assertFalse(supervisor._external_owner_healthy(service, 1001.0))
        with mock.patch.object(supervisor, "_lock_is_held", return_value=True), \
             mock.patch.object(supervisor, "_lock_owner_pid", return_value=321), \
             mock.patch.object(supervisor, "_is_process_alive", return_value=True), \
             mock.patch.object(supervisor, "_is_scheduler_process", return_value=True):
            self.assertTrue(supervisor._external_owner_healthy(service, 1001.0))
        with mock.patch.object(supervisor, "_lock_is_held", return_value=True), \
             mock.patch.object(supervisor, "_lock_owner_pid", return_value=999), \
             mock.patch.object(supervisor, "_is_process_alive", return_value=True), \
             mock.patch.object(supervisor, "_is_scheduler_process", return_value=True):
            self.assertFalse(supervisor._external_owner_healthy(service, 1001.0))

    def test_supervisor_restarts_service_after_startup_heartbeat_grace_expires(self):
        class Clock:
            def __init__(self):
                self.now = 1000.0
            def time(self):
                return self.now
            def monotonic(self):
                return self.now
            def sleep(self, seconds):
                self.now += 130.0

        class Child:
            pid = 45678
            returncode = None
            def poll(self):
                return self.returncode
            def terminate(self):
                self.returncode = -15
            def wait(self, timeout=None):
                return self.returncode
            def kill(self):
                self.returncode = -9

        heartbeat = self.state.parent / "scheduler_heartbeat.json"
        service = {
            "name": "factory_scheduler", "cmd": ["scheduler.py"],
            "cwd": str(self.state.parent), "log": self.log,
            "heartbeat": heartbeat, "singleton_lock": self.lock,
        }
        child = Child()
        with mock.patch.object(supervisor, "SERVICES", [service]), \
             mock.patch.object(supervisor, "time", Clock()), \
             mock.patch.object(supervisor.subprocess, "Popen", return_value=child):
            supervisor.run(max_loops=2)
        self.assertEqual(child.returncode, -15)
        self.assertIn("factory_scheduler heartbeat stale; restarting", self.log.read_text())

    def test_state_write_uses_atomic_replacement(self):
        supervisor._save_state({"healthy": True})
        self.assertEqual(supervisor._load_state(), {"healthy": True})
        self.assertFalse(list(self.state.parent.glob(self.state.name + ".*.tmp")))


if __name__ == "__main__":
    unittest.main()
