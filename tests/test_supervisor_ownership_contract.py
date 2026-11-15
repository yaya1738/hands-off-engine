"""Regression tests for supervisor lock/PID ownership boundaries."""
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
        try:
            self.assertIsNone(supervisor._acquire_lock(self.lock))
            self.assertEqual(self.lock.read_text(), "owner-record")
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
             mock.patch.object(supervisor, "_is_supervisor_process", return_value=True):
            self.assertTrue(supervisor._can_signal_supervisor(111))

    def test_state_write_uses_atomic_replacement(self):
        supervisor._save_state({"healthy": True})
        self.assertEqual(supervisor._load_state(), {"healthy": True})
        self.assertFalse(list(self.state.parent.glob(self.state.name + ".*.tmp")))


if __name__ == "__main__":
    unittest.main()
