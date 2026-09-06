from pathlib import Path

import pytest

from telegram.communication_protocol import ConversationProtocol, ConversationStore


def test_round_trip_and_correlation(tmp_path: Path):
    protocol = ConversationProtocol(tmp_path)
    inbound = protocol.receive("Please prioritize the deployment hardening work.", metadata={"source": "telegram"})
    outbound = protocol.emit("I will continue autonomously and report only material blockers.", kind="ack", correlation_id=inbound.message_id)
    messages = ConversationStore(tmp_path).read()
    assert [m.message_id for m in messages] == [inbound.message_id, outbound.message_id]
    assert ConversationStore(tmp_path).pending_responses() == []


def test_blocker_can_request_human_response_and_response_closes_it(tmp_path: Path):
    protocol = ConversationProtocol(tmp_path)
    blocker = protocol.emit("Credential rotation requires external authorization before production can proceed.", kind="blocker", priority="high", requires_response=True)
    assert blocker.direction == "outbound"
    assert blocker.requires_response is True
    assert blocker in protocol.store.pending_human_requests()
    response = protocol.receive("Authorization is complete.", kind="response", correlation_id=blocker.message_id)
    assert response.correlation_id == blocker.message_id
    assert protocol.store.pending_human_requests() == []


def test_outbound_ack_does_not_mark_human_request_answered(tmp_path: Path):
    protocol = ConversationProtocol(tmp_path)
    request = protocol.emit("Choose the next bounded action.", kind="decision", priority="high", correlation_id="task-1", requires_response=True)
    protocol.emit("I recorded the decision request.", kind="ack", correlation_id=request.message_id)
    assert protocol.store.pending_human_requests() == [request]


def test_secret_text_is_redacted(tmp_path: Path):
    protocol = ConversationProtocol(tmp_path)
    message = protocol.emit("token=super-secret-value", kind="blocker")
    assert "super-secret-value" not in message.text
    assert "[REDACTED]" in message.text


def test_invalid_message_rejected(tmp_path: Path):
    protocol = ConversationProtocol(tmp_path)
    with pytest.raises(ValueError):
        protocol.emit("", kind="progress")
