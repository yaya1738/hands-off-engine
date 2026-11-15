import json
import os

import pytest

from ai.factory.authority_gateway import FactoryAuthorityGateway
from ai.factory.objective_review import FactoryObjectiveReview, ObjectiveReviewError


def make_review(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ADMIN_USER_IDS", "12345,67890")
    gateway = FactoryAuthorityGateway(tmp_path)
    goal = gateway.submit_goal(
        "Review scheduler ownership and propose a safe plan",
        priority=2,
        source="test",
        idempotency_key="review-test-goal",
    )
    return FactoryObjectiveReview(tmp_path, gateway), goal["goal_id"]


def test_review_requires_authenticated_allowlisted_telegram_actor(tmp_path, monkeypatch):
    review, goal_id = make_review(tmp_path, monkeypatch)
    with pytest.raises(ObjectiveReviewError, match="authenticated"):
        review.review(goal_id, "accept_for_planning", authenticated=False, authenticated_actor_id="12345")
    with pytest.raises(ObjectiveReviewError, match="not in TELEGRAM_ADMIN_USER_IDS"):
        review.review(goal_id, "accept_for_planning", authenticated=True, authenticated_actor_id="999")
    with pytest.raises(ObjectiveReviewError, match="unsupported review channel"):
        review.review(goal_id, "accept_for_planning", authenticated=True, authenticated_actor_id="12345", channel="webhook")


def test_accept_creates_append_only_review_and_planning_only_handoff(tmp_path, monkeypatch):
    review, goal_id = make_review(tmp_path, monkeypatch)
    result = review.review(
        goal_id,
        "accept_for_planning",
        authenticated=True,
        authenticated_actor_id="12345",
        correlation_id="telegram-update-7",
    )
    assert result["status"] == "accepted_for_planning"
    assert result["planning_only"] is True
    assert result["execution_enabled"] is False

    events = [json.loads(line) for line in review.events_path.read_text().splitlines()]
    planning = [json.loads(line) for line in review.planning_path.read_text().splitlines()]
    assert len(events) == 1
    assert events[0]["actor_id"] == "12345"
    assert events[0]["channel"] == "telegram"
    assert events[0]["correlation_id"] == "telegram-update-7"
    assert len(planning) == 1
    assert planning[0]["status"] == "queued_for_planning"
    assert planning[0]["dispatch_enabled"] is False
    assert planning[0]["execution_enabled"] is False
    assert "task_assignment" not in planning[0]


def test_same_review_is_idempotent_and_does_not_duplicate_planning(tmp_path, monkeypatch):
    review, goal_id = make_review(tmp_path, monkeypatch)
    kwargs = {
        "authenticated": True,
        "authenticated_actor_id": "12345",
        "channel": "telegram",
    }
    first = review.review(goal_id, "accept_for_planning", **kwargs)
    second = review.review(goal_id, "accept_for_planning", **kwargs)
    assert first["review_event_id"] == second["review_event_id"]
    assert second["status"] == "idempotent_replay"
    assert len(review.events_path.read_text().splitlines()) == 1
    assert len(review.planning_path.read_text().splitlines()) == 1


def test_conflicting_terminal_decision_is_rejected(tmp_path, monkeypatch):
    review, goal_id = make_review(tmp_path, monkeypatch)
    kwargs = {"authenticated": True, "authenticated_actor_id": "12345"}
    review.review(goal_id, "reject", **kwargs)
    with pytest.raises(ObjectiveReviewError, match="conflicting terminal review"):
        review.review(goal_id, "accept_for_planning", **kwargs)
    assert not review.planning_path.exists()


def test_rejected_objective_never_enters_planning_queue(tmp_path, monkeypatch):
    review, goal_id = make_review(tmp_path, monkeypatch)
    result = review.review(goal_id, "reject", authenticated=True, authenticated_actor_id="12345")
    assert result["status"] == "rejected"
    assert result["execution_enabled"] is False
    assert not review.planning_path.exists()


def test_review_rejects_unknown_goal_and_invalid_decision(tmp_path, monkeypatch):
    review, goal_id = make_review(tmp_path, monkeypatch)
    kwargs = {"authenticated": True, "authenticated_actor_id": "12345"}
    with pytest.raises(ObjectiveReviewError, match="not found"):
        review.review("a" * 64, "reject", **kwargs)
    with pytest.raises(ObjectiveReviewError, match="decision must"):
        review.review(goal_id, "execute", **kwargs)
