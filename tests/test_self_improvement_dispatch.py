import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import self_improvement
from scripts.task_worker import validate_task_envelope


class DurableImprovementDispatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old = {
            "STATE": self_improvement.STATE,
            "BUS": self_improvement.BUS,
            "DISPATCH_STATE": self_improvement.DISPATCH_STATE,
            "DISPATCH_LOCK": self_improvement.DISPATCH_LOCK,
        }
        self_improvement.STATE = self.root / "state"
        self_improvement.BUS = self.root / "messages.jsonl"
        self_improvement.DISPATCH_STATE = self.root / "state" / "dispatch.json"
        self_improvement.DISPATCH_LOCK = self.root / "state" / "dispatch.lock"

    def tearDown(self):
        for name, value in self.old.items():
            setattr(self_improvement, name, value)
        self.temp.cleanup()

    def _candidate(self, cid):
        return {
            "id": cid,
            "category": "reliability",
            "title": f"Candidate {cid}",
            "description": "Read-only health log review",
        }

    def _write_pending(self, cid="imp-pending"):
        message = {
            "msg_id": f"msg-{cid}",
            "timestamp": "2026-11-15T00:00:00+00:00",
            "from": "factory",
            "to": "anyclaw",
            "type": "task_assignment",
            "context": {
                "task_id": f"task-{cid}",
                "action": "read_file_fact",
                "params": {"file_path": "state/health_log.jsonl"},
                "reply_to": "self_improvement",
                "correlation_id": cid,
            },
            "payload": {"candidate_id": cid},
        }
        state = {
            "dispatched": {},
            "pending": {
                cid: {
                    "msg_id": message["msg_id"],
                    "task_id": message["context"]["task_id"],
                    "action": message["context"]["action"],
                    "dispatched_at": message["timestamp"],
                    "message": message,
                }
            },
            "history": [],
        }
        self_improvement._save_dispatch_state(state)
        return message

    def _bus_messages(self):
        if not self_improvement.BUS.exists():
            return []
        return [
            json.loads(line)
            for line in self_improvement.BUS.read_text().splitlines()
            if line.strip()
        ]

    def test_dispatched_envelope_is_accepted_by_real_local_worker(self):
        message = self_improvement.dispatch_one([self._candidate("imp-contract")])
        valid, error = validate_task_envelope(message)
        self.assertTrue(valid, error)
        self.assertEqual(message["context"]["task_id"], "task-imp-contract")
        self.assertEqual(message["context"]["action"], "read_file_fact")
        self.assertEqual(
            message["context"]["params"]["file_path"],
            "state/health_log.jsonl",
        )
        self.assertNotIn("task_id", message)
        self.assertNotIn("action", message)
        self.assertNotIn("params", message)

    def test_dispatches_at_most_one_candidate_per_call(self):
        result = self_improvement.dispatch_one([
            self._candidate("imp-one"),
            self._candidate("imp-two"),
        ])
        self.assertEqual(result["payload"]["candidate_id"], "imp-one")
        self.assertEqual(len(self._bus_messages()), 1)
        state = self_improvement._load_dispatch_state()
        self.assertEqual(len(state["dispatched"]), 1)
        self.assertEqual(state["pending"], {})

    def test_pending_outbox_recovers_after_pre_append_crash(self):
        message = self._write_pending()
        self_improvement.dispatch_one([])
        self.assertEqual(self._bus_messages(), [message])
        state = self_improvement._load_dispatch_state()
        self.assertIn("imp-pending", state["dispatched"])
        self.assertEqual(state["pending"], {})

    def test_recovery_does_not_duplicate_message_already_on_bus(self):
        message = self._write_pending()
        self_improvement.BUS.parent.mkdir(parents=True, exist_ok=True)
        self_improvement.BUS.write_text(json.dumps(message) + "\n")
        self_improvement.dispatch_one([])
        self.assertEqual(len(self._bus_messages()), 1)
        state = self_improvement._load_dispatch_state()
        self.assertIn("imp-pending", state["dispatched"])
        self.assertEqual(state["pending"], {})

    def test_pending_record_survives_append_failure_and_retries(self):
        with mock.patch.object(self_improvement, "_append_bus", side_effect=OSError("simulated crash")):
            with self.assertRaises(OSError):
                self_improvement.dispatch_one([self._candidate("imp-retry")])

        state = self_improvement._load_dispatch_state()
        self.assertIn("imp-retry", state["pending"])
        self.assertNotIn("imp-retry", state["dispatched"])

        self_improvement.dispatch_one([])
        self.assertEqual(len(self._bus_messages()), 1)
        state = self_improvement._load_dispatch_state()
        self.assertIn("imp-retry", state["dispatched"])
        self.assertEqual(state["pending"], {})


if __name__ == "__main__":
    unittest.main()

class DispatchStatePermissionTests(unittest.TestCase):
    """Dispatch state, lock, and a newly created bus must be owner-only."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old = {
            "STATE": self_improvement.STATE,
            "BUS": self_improvement.BUS,
            "DISPATCH_STATE": self_improvement.DISPATCH_STATE,
            "DISPATCH_LOCK": self_improvement.DISPATCH_LOCK,
        }
        self_improvement.STATE = self.root / "state"
        self_improvement.BUS = self.root / "ai" / "coordination" / "messages.jsonl"
        self_improvement.DISPATCH_STATE = self.root / "state" / "dispatch.json"
        self_improvement.DISPATCH_LOCK = self.root / "state" / "dispatch.lock"

    def tearDown(self):
        for name, value in self.old.items():
            setattr(self_improvement, name, value)
        self.temp.cleanup()

    def test_dispatch_files_are_0600_under_permissive_umask(self):
        import os
        old_umask = os.umask(0o000)
        try:
            message = {
                "msg_id": "perm-msg-1",
                "from": "factory",
                "to": "anyclaw",
                "type": "task_assignment",
                "context": {"task_id": "t-perm", "action": "system_status", "params": {}},
            }
            self.assertTrue(self_improvement._append_bus(message))
            self_improvement._save_dispatch_state({"dispatched": {}, "pending": {}, "history": []})
            with self_improvement._open_private(
                    self_improvement.DISPATCH_LOCK,
                    os.O_WRONLY | os.O_CREAT | os.O_APPEND, "a"):
                pass
            for path in (
                self_improvement.BUS,
                self_improvement.DISPATCH_STATE,
                self_improvement.DISPATCH_LOCK,
            ):
                self.assertTrue(path.exists(), path)
                mode = path.stat().st_mode & 0o777
                self.assertEqual(mode, 0o600, f"{path.name} must be 0600, got {oct(mode)}")
        finally:
            os.umask(old_umask)

    def test_existing_bus_mode_is_preserved_on_append(self):
        import os
        self_improvement.BUS.parent.mkdir(parents=True, exist_ok=True)
        self_improvement.BUS.write_text("")
        # Owner-read-only: appends must preserve whatever mode exists.
        os.chmod(self_improvement.BUS, 0o700)
        message = {
            "msg_id": "perm-msg-2",
            "from": "factory",
            "to": "anyclaw",
            "type": "task_assignment",
            "context": {"task_id": "t-perm2", "action": "system_status", "params": {}},
        }
        self.assertTrue(self_improvement._append_bus(message))
        self.assertEqual(self_improvement.BUS.stat().st_mode & 0o777, 0o700)
