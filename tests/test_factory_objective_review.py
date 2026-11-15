import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai.factory.authority_gateway import FactoryAuthorityGateway
from ai.factory.objective_review import FactoryObjectiveReview, ObjectiveReviewError


class FactoryObjectiveReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"TELEGRAM_ADMIN_USER_IDS": "12345,67890"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.temp.cleanup)
        self.gateway = FactoryAuthorityGateway(self.root)
        result = self.gateway.submit_goal(
            "Review scheduler ownership and propose a safe plan",
            priority=2,
            source="test",
            idempotency_key="review-test-goal",
        )
        self.goal_id = result["goal_id"]
        self.review = FactoryObjectiveReview(self.root, self.gateway)

    def test_review_requires_authenticated_allowlisted_telegram_actor(self):
        with self.assertRaisesRegex(ObjectiveReviewError, "authenticated"):
            self.review.review(self.goal_id, "accept_for_planning", authenticated=False, authenticated_actor_id="12345")
        with self.assertRaisesRegex(ObjectiveReviewError, "not in TELEGRAM_ADMIN_USER_IDS"):
            self.review.review(self.goal_id, "accept_for_planning", authenticated=True, authenticated_actor_id="999")
        with self.assertRaisesRegex(ObjectiveReviewError, "unsupported review channel"):
            self.review.review(self.goal_id, "accept_for_planning", authenticated=True, authenticated_actor_id="12345", channel="webhook")

    def test_accept_creates_append_only_review_and_planning_only_handoff(self):
        result = self.review.review(
            self.goal_id,
            "accept_for_planning",
            authenticated=True,
            authenticated_actor_id="12345",
            correlation_id="telegram-update-7",
        )
        self.assertEqual(result["status"], "accepted_for_planning")
        self.assertTrue(result["planning_only"])
        self.assertFalse(result["execution_enabled"])
        events = [json.loads(line) for line in self.review.events_path.read_text().splitlines()]
        planning = [json.loads(line) for line in self.review.planning_path.read_text().splitlines()]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["actor_id"], "12345")
        self.assertEqual(events[0]["channel"], "telegram")
        self.assertEqual(events[0]["correlation_id"], "telegram-update-7")
        self.assertEqual(len(planning), 1)
        self.assertEqual(planning[0]["status"], "queued_for_planning")
        self.assertFalse(planning[0]["dispatch_enabled"])
        self.assertFalse(planning[0]["execution_enabled"])
        self.assertNotIn("task_assignment", planning[0])

    def test_same_review_is_idempotent_and_does_not_duplicate_planning(self):
        kwargs = {"authenticated": True, "authenticated_actor_id": "12345", "channel": "telegram"}
        first = self.review.review(self.goal_id, "accept_for_planning", **kwargs)
        second = self.review.review(self.goal_id, "accept_for_planning", **kwargs)
        self.assertEqual(first["review_event_id"], second["review_event_id"])
        self.assertEqual(second["status"], "idempotent_replay")
        self.assertEqual(len(self.review.events_path.read_text().splitlines()), 1)
        self.assertEqual(len(self.review.planning_path.read_text().splitlines()), 1)

    def test_conflicting_terminal_decision_is_rejected(self):
        kwargs = {"authenticated": True, "authenticated_actor_id": "12345"}
        self.review.review(self.goal_id, "reject", **kwargs)
        with self.assertRaisesRegex(ObjectiveReviewError, "conflicting terminal review"):
            self.review.review(self.goal_id, "accept_for_planning", **kwargs)
        self.assertFalse(self.review.planning_path.exists())

    def test_rejected_objective_never_enters_planning_queue(self):
        result = self.review.review(self.goal_id, "reject", authenticated=True, authenticated_actor_id="12345")
        self.assertEqual(result["status"], "rejected")
        self.assertFalse(result["execution_enabled"])
        self.assertFalse(self.review.planning_path.exists())

    def test_review_rejects_unknown_goal_and_invalid_decision(self):
        kwargs = {"authenticated": True, "authenticated_actor_id": "12345"}
        with self.assertRaisesRegex(ObjectiveReviewError, "not found"):
            self.review.review("a" * 64, "reject", **kwargs)
        with self.assertRaisesRegex(ObjectiveReviewError, "decision must"):
            self.review.review(self.goal_id, "execute", **kwargs)


if __name__ == "__main__":
    unittest.main()
