from pathlib import Path
import unittest

from scripts.merge_authority import evaluate_merge_request

ROOT = Path(__file__).resolve().parents[1]


class MergeAuthorityTests(unittest.TestCase):
    def test_agent_request_never_authorizes_merge(self):
        for requester in ("copilot", "claude", "grok", "telegram", "github-actions[bot]"):
            result = evaluate_merge_request(375, requester)
            self.assertEqual(result["decision"], "human_review_required")
            self.assertFalse(result["automated_merge"])

    def test_invalid_pr_numbers_are_rejected(self):
        for value in (0, -1, True, "375", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    evaluate_merge_request(value, "copilot")

    def test_empty_requester_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_merge_request(375, " ")

    def test_coordination_agent_has_no_merge_executor_or_secret_fallback(self):
        source = (ROOT / "scripts" / "coordination_agent.py").read_text()
        self.assertNotIn('"pr", "merge"', source)
        self.assertNotIn("gh pr merge", source)
        self.assertNotIn("TELEGRAM_BOT_TOKEN', '", source)
        self.assertIn('os.getenv("TELEGRAM_BOT_TOKEN")', source)
        self.assertIn("evaluate_merge_request", source)

    def test_workflows_have_no_automated_merge_or_draft_promotion(self):
        auto = (ROOT / ".github/workflows/auto-merge.yml").read_text()
        ready = (ROOT / ".github/workflows/mark-ready.yml").read_text()
        self.assertNotIn("gh pr merge", auto)
        self.assertNotIn("repository_dispatch", auto)
        self.assertIn("contents: read", auto)
        self.assertIn("pull-requests: read", auto)
        self.assertIn("workflow_dispatch:", ready)
        self.assertNotIn("pull_request:", ready)
        self.assertNotIn("gh pr merge", ready)
        self.assertIn("TRUSTED_OPERATORS", ready)


if __name__ == "__main__":
    unittest.main()
