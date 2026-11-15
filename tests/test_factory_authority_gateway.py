import json
import tempfile
import unittest
from pathlib import Path

from ai.factory.authority_gateway import FactoryAuthorityGateway


class FactoryAuthorityGatewayTests(unittest.TestCase):
    def test_submit_goal_persists_review_only_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            gateway = FactoryAuthorityGateway(tmp)
            result = gateway.submit_goal(
                "Review failed CI for PR 12",
                priority=2,
                source="github_governance_monitor",
                idempotency_key="finding:pr12:ci_failed:abc",
                metadata={"pr_number": 12, "category": "ci_failed"},
            )
            rows = [json.loads(line) for line in (Path(tmp) / "state" / "factory_objectives.jsonl").read_text().splitlines()]
            self.assertEqual(result["status"], "queued_for_review")
            self.assertFalse(result["execution_enabled"])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["status"], "pending_review")
            self.assertTrue(rows[0]["approval_required"])
            self.assertFalse(rows[0]["execution_enabled"])

    def test_duplicate_idempotency_key_does_not_append_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            gateway = FactoryAuthorityGateway(tmp)
            kwargs = {"idempotency_key": "same-finding", "source": "monitor"}
            first = gateway.submit_goal("Inspect stale PR", **kwargs)
            second = gateway.submit_goal("Inspect stale PR", **kwargs)
            queue = Path(tmp) / "state" / "factory_objectives.jsonl"
            self.assertEqual(first["goal_id"], second["goal_id"])
            self.assertEqual(second["status"], "idempotent_replay")
            self.assertEqual(len(queue.read_text().splitlines()), 1)

    def test_conflicting_reuse_of_idempotency_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            gateway = FactoryAuthorityGateway(tmp)
            gateway.submit_goal("First objective", idempotency_key="same")
            with self.assertRaisesRegex(ValueError, "different objective"):
                gateway.submit_goal("Different objective", idempotency_key="same")

    def test_invalid_priority_and_objective_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            gateway = FactoryAuthorityGateway(tmp)
            for priority in (True, 0, 6, 2.5):
                with self.subTest(priority=priority), self.assertRaises(ValueError):
                    gateway.submit_goal("Valid objective", priority=priority)
            with self.assertRaises(ValueError):
                gateway.submit_goal("   ")

    def test_metadata_must_be_bounded_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            gateway = FactoryAuthorityGateway(tmp)
            with self.assertRaisesRegex(ValueError, "JSON serializable"):
                gateway.submit_goal("Objective", metadata={"bad": object()})
            with self.assertRaisesRegex(ValueError, "exceeds 4096"):
                gateway.submit_goal("Objective", metadata={"payload": "x" * 5000})

    def test_list_goals_is_bounded_newest_first_and_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            gateway = FactoryAuthorityGateway(tmp)
            first = gateway.submit_goal("First objective", idempotency_key="first")
            second = gateway.submit_goal("Second objective", idempotency_key="second")
            rows = gateway.list_goals(limit=1)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["goal_id"], second["goal_id"])
            self.assertEqual(rows[0]["status"], "pending_review")
            self.assertEqual(gateway.get_goal(first["goal_id"])["objective"], "First objective")

    def test_list_goals_rejects_unbounded_or_boolean_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            gateway = FactoryAuthorityGateway(tmp)
            for limit in (True, 0, 201, 1.5):
                with self.subTest(limit=limit), self.assertRaises(ValueError):
                    gateway.list_goals(limit=limit)

    def test_get_goal_rejects_malformed_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            gateway = FactoryAuthorityGateway(tmp)
            with self.assertRaises(ValueError):
                gateway.get_goal("../state")


if __name__ == "__main__":
    unittest.main()


class GatewayPermissionTests(unittest.TestCase):
    """Objective queue and lock must be owner-only regardless of umask."""

    def test_queue_and_lock_are_0600_under_permissive_umask(self):
        import os
        old_umask = os.umask(0o000)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                gateway = FactoryAuthorityGateway(tmp)
                gateway.submit_goal(
                    "Owner-only objective", source="test", idempotency_key="perm-goal")
                for path in (gateway.queue_path, gateway.lock_path):
                    self.assertTrue(path.exists(), path)
                    mode = path.stat().st_mode & 0o777
                    self.assertEqual(mode, 0o600, f"{path.name} must be 0600, got {oct(mode)}")
        finally:
            os.umask(old_umask)

    def test_existing_queue_mode_is_preserved_on_append(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            gateway = FactoryAuthorityGateway(tmp)
            gateway.submit_goal("First objective", source="test", idempotency_key="k1")
            # Owner-read-only: appends must preserve whatever mode exists.
            os.chmod(gateway.queue_path, 0o700)
            gateway.submit_goal("Second objective", source="test", idempotency_key="k2")
            self.assertEqual(gateway.queue_path.stat().st_mode & 0o777, 0o700)
