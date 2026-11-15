import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.github_governance_monitor import monitor_once, _check_status


class GitHubGovernanceMonitorTests(unittest.TestCase):
    def test_empty_check_runs_are_not_misclassified_as_success(self):
        self.assertEqual(_check_status({"check_runs": []}), "missing")

    def test_check_status_distinguishes_pending_failed_and_passed(self):
        self.assertEqual(_check_status({"check_runs": [{"status": "in_progress"}]}), "pending")
        self.assertEqual(_check_status({"check_runs": [{"status": "completed", "conclusion": "failure"}]}), "failed")
        self.assertEqual(_check_status({"check_runs": [{"status": "completed", "conclusion": "success"}]}), "passed")

    def test_monitor_persists_findings_and_deduplicates_bus_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)
            old = (now - timedelta(days=20)).isoformat()

            def fetch(path):
                if "/pulls?" in path:
                    return [
                        {"number": 1, "title": "Draft with missing checks", "draft": True,
                         "head": {"sha": "a" * 40}, "updated_at": old,
                         "mergeable": False, "mergeable_state": "dirty"},
                        {"number": 2, "title": "Failed CI", "draft": False,
                         "head": {"sha": "b" * 40}, "updated_at": now.isoformat(),
                         "mergeable": True, "mergeable_state": "clean"},
                    ]
                if "/check-runs" in path and "a" * 40 in path:
                    return {"check_runs": []}
                if "/check-runs" in path and "b" * 40 in path:
                    return {"check_runs": [{"status": "completed", "conclusion": "failure"}]}
                if "/pulls/1/reviews" in path:
                    return [{"user": {"login": "reviewer"}, "state": "APPROVED"}]
                if "/pulls/2/reviews" in path:
                    return [{"user": {"login": "reviewer"}, "state": "CHANGES_REQUESTED"}]
                if "/issues/374/comments" in path:
                    return [{"id": 99, "body": "secret text must not be copied"}]
                raise AssertionError(path)

            first = monitor_once(fetch, root=root, now=now)
            bus = root / "ai" / "coordination" / "messages.jsonl"
            first_lines = bus.read_text().splitlines()
            second = monitor_once(fetch, root=root, now=now)
            second_lines = bus.read_text().splitlines()

            categories = {item["category"] for item in first["findings"]}
            self.assertTrue({"ci_missing", "ci_failed", "stale_pr", "merge_blocked", "review_changes_requested"} <= categories)
            self.assertEqual(first["draft_pr_count"], 1)
            self.assertEqual(first["new_coordination_comments"], 1)
            self.assertEqual(len(first_lines), 1)
            self.assertEqual(len(second_lines), 1)
            self.assertEqual(first["signature"], second["signature"])
            self.assertNotIn("secret text", json.dumps(first))

    def test_monitor_handles_api_failure_without_claiming_checks_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)

            def fail(_path):
                raise RuntimeError("rate limited")

            report = monitor_once(fail, root=Path(tmp), now=now)
            self.assertEqual(report["api_status"], "partial")
            self.assertEqual(report["monitored_pr_count"], 0)
            self.assertEqual(report["mode"], "read_only")
            self.assertTrue(report["errors"])

    def test_monitor_reports_missing_runtime_evidence_as_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)

            def fetch(path):
                if "/pulls?" in path:
                    return []
                if "/issues/374/comments" in path:
                    return []
                raise AssertionError(path)

            report = monitor_once(fetch, root=Path(tmp), now=now)
            self.assertFalse(report["runtime_evidence"]["available"])
            self.assertIsNone(report["runtime_evidence"]["age_seconds"])


if __name__ == "__main__":
    unittest.main()
