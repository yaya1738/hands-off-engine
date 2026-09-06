from pathlib import Path

import pytest

from telegram.communication_protocol import ConversationProtocol, ConversationStore


def test_round_trip_and_correlation(tmp_path: Path):
    protocol = ConversationProtocol(tmp_path)
    inbound = protocol.receive("Please prioritize the deployment hardening work.", metadata={"source": "telegram"})
    outbound = protocol.emit(
        "I will continue autonomously and report only material blockers.",
        kind="ack",
        correlation_id=inbound.message_id,
    )

    messages = ConversationStore(tmp_path).read()
    assert [m.message_id for m in messages] == [inbound.message_id, outbound.message_id]
    assert ConversationStore(tmp_path).pending_responses() == []


def test_blocker_can_request_human_response(tmp_path: Path):
    protocol = ConversationProtocol(tmp_path)
    blocker = protocol.emit(
        "Credential rotation requires external authorization before production can proceed.",
        kind="blocker",
        priority="high",
        requires_response=True,
    )

    assert blocker.direction == "outbound"
    assert blocker.requires_response is True
    assert "Credential rotation" in protocol.render(blocker)


def test_invalid_message_rejected(tmp_path: Path):
    protocol = ConversationProtocol(tmp_path)
    with pytest.raises(ValueError):
        protocol.emit("", kind="progress")
