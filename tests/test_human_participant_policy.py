import json
from datetime import datetime, timezone, timedelta

import pytest

from messaging.human_participant_policy import ContactHistory, evaluate_contact_request


PARTY = {
    "id": "aharon",
    "role": "human_participant",
    "email_consent": True,
    "channels": ["email"],
}
PAYLOAD = {
    "task_id": "task-17",
    "correlation_id": "task-17-question-1",
    "reason_code": "material_ambiguity",
    "context": "Two safe approaches have different maintenance costs.",
    "question": "Which trade-off should we prioritize?",
    "why_it_matters": "The answer changes the implementation plan.",
}


def test_well_formed_relevant_question_is_eligible():
    result = evaluate_contact_request(PARTY, PAYLOAD, [], now=datetime(2026, 10, 15, tzinfo=timezone.utc))
    assert result == {"allowed": True, "reason": "eligible", "task_id": "task-17",
                      "correlation_id": "task-17-question-1"}


@pytest.mark.parametrize("change,reason", [
    ({"email_consent": False}, "consent_not_recorded"),
    ({"role": "agent"}, "not_a_human_participant"),
    ({"channels": ["telegram"]}, "email_channel_not_enabled"),
])
def test_participant_must_be_enabled(change, reason):
    party = {**PARTY, **change}
    assert evaluate_contact_request(party, PAYLOAD, [])["reason"] == reason


def test_heartbeats_and_unstructured_messages_are_not_eligible():
    payload = {**PAYLOAD, "reason_code": "heartbeat"}
    assert evaluate_contact_request(PARTY, payload, [])["reason"] == "ineligible_reason_code"
    payload = {k: v for k, v in PAYLOAD.items() if k != "question"}
    assert "missing_context" in evaluate_contact_request(PARTY, payload, [])["reason"]


def test_duplicate_open_question_is_blocked():
    history = [{"participant_id": "aharon", "correlation_id": PAYLOAD["correlation_id"],
                "status": "awaiting_reply", "timestamp": "2026-10-14T00:00:00+00:00"}]
    result = evaluate_contact_request(PARTY, PAYLOAD, history,
                                      now=datetime(2026, 10, 15, tzinfo=timezone.utc))
    assert result["reason"] == "duplicate_open_question"


def test_cooldown_and_daily_cap_are_enforced():
    now = datetime(2026, 10, 15, 12, tzinfo=timezone.utc)
    recent = [{"participant_id": "aharon", "correlation_id": "old", "status": "sent",
               "timestamp": (now - timedelta(hours=2)).isoformat()}]
    assert evaluate_contact_request(PARTY, PAYLOAD, recent, now=now)["reason"] == "participant_cooldown"
    today = [{"participant_id": "aharon", "correlation_id": str(i), "status": "answered",
              "timestamp": now.isoformat()} for i in range(3)]
    assert evaluate_contact_request(PARTY, PAYLOAD, today, now=now)["reason"] == "daily_contact_cap"


def test_contact_history_persists_atomically_and_refuses_corrupt_state(tmp_path):
    store = ContactHistory(tmp_path / "state" / "contact_history.json")
    store.record("aharon", PAYLOAD, "awaiting_reply", now=datetime(2026, 10, 15, tzinfo=timezone.utc))
    assert json.loads(store.path.read_text())[0]["correlation_id"] == PAYLOAD["correlation_id"]
    store.path.write_text("{broken")
    with pytest.raises(RuntimeError, match="refusing contact"):
        store.load()
