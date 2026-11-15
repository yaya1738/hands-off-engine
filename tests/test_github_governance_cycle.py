import tempfile
import unittest
from pathlib import Path

from ai.factory.authority_gateway import FactoryAuthorityGateway
from scripts.github_governance_cycle import admit_findings


class GovernanceObjectiveAdmissionTests(unittest.TestCase):
    def test_allowlisted_findings_become_review_only_objectives(self):
        with tempfile.TemporaryDirectory() as tmp:
            gateway = FactoryAuthorityGateway(tmp)
            report = {"findings": [
                {"id": "pr:5:ci_failed:abc", "category": "ci_failed", "pr_number": 5,
                 "title": "Broken checks", "detail": "Latest head failed", "head_sha": "abc"},
                {"id": "pr:6:stale_pr:def", "category": "stale_pr", "pr_number": 6,
                 "title": "Old PR", "detail": "No updates"},
            ]}
            result = admit_findings(report, gateway=gateway)
            self.assertEqual(result["queued"], 2)
            queue = Path(tmp) / "state" / "factory_objectives.jsonl"
            rows = [__import__("json").loads(line) for line in queue.read_text().splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(row["status"] == "pending_review" for row in rows))
            self.assertTrue(all(row["execution_enabled"] is False for row in rows))

    def test_repeated_findings_are_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            gateway = FactoryAuthorityGateway(tmp)
            report = {"findings": [{"id": "pr:5:ci_failed:abc", "category": "ci_failed", "pr_number": 5}]}
            first = admit_findings(report, gateway=gateway)
            second = admit_findings(report, gateway=gateway)
            self.assertEqual(first["queued"], 1)
            self.assertEqual(second["replayed"], 1)
            queue = Path(tmp) / "state" / "factory_objectives.jsonl"
            self.assertEqual(len(queue.read_text().splitlines()), 1)

    def test_unrecognized_findings_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = admit_findings({"findings": [
                {"id": "x", "category": "unknown"},
                {"category": "ci_failed"},
            ]}, gateway=FactoryAuthorityGateway(tmp))
            self.assertEqual(result["skipped"], 2)
            self.assertFalse((Path(tmp) / "state" / "factory_objectives.jsonl").exists())

    def test_invalid_report_is_rejected(self):
        with self.assertRaises(ValueError):
            admit_findings({"findings": "not-a-list"})


if __name__ == "__main__":
    unittest.main()
