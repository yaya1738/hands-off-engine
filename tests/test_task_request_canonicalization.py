from pathlib import Path

from scripts.factory_request_intake import RequestIntake
from scripts import task_request


def test_task_request_routes_through_commhub(monkeypatch, tmp_path):
    seen = {}

    class FakeHub:
        def __init__(self, repo_root=None):
            seen["repo_root"] = Path(repo_root)

        def receive(self, sender, msg_type, payload, channel=None):
            seen.update({
                "sender": sender,
                "msg_type": msg_type,
                "payload": payload,
                "channel": channel,
            })
            return {"routed_to": "logged", "acknowledged": True}

    monkeypatch.setattr("scripts.comm_hub.CommHub", FakeHub)

    result = task_request.send_request(
        "work_request",
        "Need the next bounded task",
        params={"scope": "tests"},
        repo_root=tmp_path,
    )

    assert result["acknowledged"] is True
    assert seen["repo_root"] == tmp_path
    assert seen["sender"] == "anyclaw"
    assert seen["msg_type"] == "task_request"
    assert seen["channel"] == "messages_jsonl"
    assert seen["payload"]["type"] == "task_request"
    assert seen["payload"]["context"]["request_type"] == "work_request"
    assert not (tmp_path / "state" / "task_request_state.json").exists()


def test_request_intake_accepts_governed_commhub_envelope(tmp_path):
    state = tmp_path / "state"
    state.mkdir(parents=True)
    (state / "party_registry.json").write_text(
        '{"anyclaw":{"id":"anyclaw","role":"agent","trust_level":9}}\n'
    )
    bus = tmp_path / "ai" / "coordination"
    bus.mkdir(parents=True)
    (bus / "messages.jsonl").write_text(
        '{"id":"outer-1","from":"anyclaw","to":"system_internal",'
        '"type":"inbound_from_agent","channel":"messages_jsonl",'
        '"timestamp":"2026-09-15T00:00:00+00:00",'
        '"payload":{"type":"task_request","message":"Need work",'
        '"msg_id":"req-1","context":{"request_type":"work_request","params":{}}}}\n'
    )

    decisions = RequestIntake(repo_root=tmp_path).admit_once()

    assert len(decisions) == 1
    assert decisions[0]["msg_id"] == "req-1"
    assert decisions[0]["from"] == "anyclaw"
    assert decisions[0]["admitted"] is True


def test_request_intake_fails_closed_for_non_task_payload(tmp_path):
    state = tmp_path / "state"
    state.mkdir(parents=True)
    (state / "party_registry.json").write_text(
        '{"anyclaw":{"id":"anyclaw","role":"agent","trust_level":9}}\n'
    )
    bus = tmp_path / "ai" / "coordination"
    bus.mkdir(parents=True)
    (bus / "messages.jsonl").write_text(
        '{"from":"anyclaw","type":"inbound_from_agent",'
        '"payload":{"type":"status_probe","message":"probe"}}\n'
    )

    assert RequestIntake(repo_root=tmp_path).admit_once() == []
