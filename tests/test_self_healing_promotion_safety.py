"""Safety tests: self-healing agent cannot promote draft PRs (#382).

The self-healing agent previously dispatched the "Mark Copilot PRs Ready
for Review" workflow and, on failure, directly invoked the GitHub
markPullRequestReadyForReview GraphQL mutation for drafts by trusted bot
authors. These tests prove that path is gone: unmerged-branch findings now
produce a non-authorizing proposal recorded for human review, no subprocess
call can reach a workflow dispatch or the promotion mutation, and the
module source no longer contains either executable path.
"""
import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# The agent configures a FileHandler on /var/log at import time, which is
# not writable in CI. Neutralize it before the import.
_file_handler = logging.FileHandler
logging.FileHandler = lambda *args, **kwargs: logging.NullHandler()
try:
    from scripts import self_healing_agent as sha
finally:
    logging.FileHandler = _file_handler

SOURCE = Path(sha.__file__).read_text()


class _StubHarmPrevention:
    """Harm-prevention stub so tests never write rollback artifacts."""

    def validate_change(self, **kwargs):
        return True, "test stub", None


class SelfHealingPromotionSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state_file = Path(self.tmp.name) / "self_healing_state.json"
        patchers = [
            mock.patch.object(sha, "STATE_FILE", self.state_file),
            mock.patch.object(sha, "announce_agent"),
            mock.patch(
                "autonomous.harm_prevention.get_harm_prevention",
                return_value=_StubHarmPrevention(),
            ),
        ]
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.agent = sha.SelfHealingAgent()

    def _unmerged_issue(self):
        issue = {
            "type": "unmerged_branches",
            "description": "6 agent branches have unmerged work - auto-merge may not be working",
            "severity": "high",
            "auto_fixable": True,
            "fix_action": "propose_mark_ready_review",
        }
        return issue

    def test_unmerged_branch_finding_requests_proposal_not_promotion(self):
        calls = {"n": 0}

        def fake_run(cmd, *args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 2:  # git branch -r
                return mock.Mock(
                    returncode=0,
                    stdout="\n".join(
                        f"  origin/copilot/branch-{i}" for i in range(6)
                    ) + "\n  origin/HEAD -> origin/main",
                )
            if calls["n"] >= 3:  # git log main..branch --oneline
                return mock.Mock(returncode=0, stdout="abc1234 some commit")
            return mock.Mock(returncode=0, stdout="")

        with mock.patch.object(sha.subprocess, "run", side_effect=fake_run):
            issues = self.agent.check_unmerged_branches()
        self.assertEqual(len(issues), 1)
        issue = issues[0]
        self.assertEqual(issue["fix_action"], "propose_mark_ready_review")
        self.assertNotIn("fix_cmd", issue)
        self.assertNotIn("trigger_mark_ready_workflow", json.dumps(issue))

    def test_attempt_fix_records_proposal_without_any_subprocess_call(self):
        issue = self._unmerged_issue()
        with mock.patch.object(sha.subprocess, "run") as run:
            result = self.agent.attempt_fix(issue)
            run.assert_not_called()
        self.assertTrue(result.startswith("Proposed for human review"))
        proposals = self.agent.state["pending_review_proposals"]
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0]["kind"], "mark_ready_review")
        self.assertIn("human", proposals[0]["recommended_action"])

    def test_repeated_cycles_do_not_duplicate_proposals(self):
        issue = self._unmerged_issue()
        first = self.agent.propose_mark_ready_review(issue)
        second = self.agent.propose_mark_ready_review(issue)
        self.assertEqual(first, second)
        self.assertEqual(len(self.agent.state["pending_review_proposals"]), 1)

    def test_module_source_contains_no_promotion_paths(self):
        # The executable promotion paths must not exist anywhere in the
        # module: no GraphQL draft-promotion mutation, no `gh workflow run`
        # dispatch, no trusted-author fallback. (The workflow's name may
        # legitimately appear inside the human-facing recommendation text.)
        self.assertNotIn("markPullRequestReadyForReview", SOURCE)
        self.assertNotIn('"gh", "workflow", "run"', SOURCE)
        self.assertNotIn("_manually_mark_prs_ready", SOURCE)
        self.assertNotIn("trigger_mark_ready_workflow", SOURCE)
        self.assertNotIn("_request_conflict_fixes", SOURCE)

    def test_dispatch_table_has_no_promotion_action(self):
        # No fix_action value may map to a promotion-capable handler.
        with mock.patch.object(sha.SelfHealingAgent, "propose_mark_ready_review") as propose:
            self.agent.attempt_fix(self._unmerged_issue())
            propose.assert_called_once()

    def test_proposal_survives_state_round_trip(self):
        issue = self._unmerged_issue()
        self.agent.propose_mark_ready_review(issue)
        self.agent.save_state()
        reloaded = sha.SelfHealingAgent()
        self.assertEqual(len(reloaded.state["pending_review_proposals"]), 1)


if __name__ == "__main__":
    unittest.main()
