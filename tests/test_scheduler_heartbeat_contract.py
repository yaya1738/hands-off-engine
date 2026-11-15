"""Scheduler heartbeat producer contract tests."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import scheduler


class SchedulerHeartbeatContractTests(unittest.TestCase):
    def test_idle_and_task_heartbeats_are_atomic_and_identify_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "heartbeat.json"
            with mock.patch.object(scheduler, "SCHEDULER_HEARTBEAT", path), \
                 mock.patch.object(scheduler.os, "getpid", return_value=1234), \
                 mock.patch.object(scheduler.time, "time", return_value=100.0):
                self.assertTrue(scheduler.write_heartbeat())
                idle = json.loads(path.read_text())
                self.assertEqual(idle["pid"], 1234)
                self.assertEqual(idle["phase"], "idle")
                self.assertIsNone(idle["task_deadline"])

                self.assertTrue(scheduler.write_heartbeat(
                    phase="task", task="integrity_check", task_deadline=160.0
                ))
                active = json.loads(path.read_text())
                self.assertEqual(active["phase"], "task")
                self.assertEqual(active["task"], "integrity_check")
                self.assertEqual(active["task_deadline"], 160.0)
                self.assertEqual(active["updated_at"], 100.0)
            self.assertFalse(list(Path(tmp).glob("heartbeat.json.*.tmp")))

    def test_heartbeat_storage_failure_is_nonfatal(self):
        with mock.patch.object(scheduler, "_atomic_write_json", side_effect=OSError("disk unavailable")):
            self.assertFalse(scheduler.write_heartbeat())


if __name__ == "__main__":
    unittest.main()
