import scripts.comm_hub as comm_hub
import scripts.control_api as control_api


def test_comm_hub_rejects_unverified_privileged_messages():
    hub = comm_hub.CommHub.__new__(comm_hub.CommHub)

    result = hub._route_inbound({
        "type": "approve",
        "sender_trust": 10,
        "sender_role": "owner",
        "authenticated": False,
        "payload": {"command_id": "cmd-1"},
    })

    assert result["routed_to"] == "rejected"


def test_control_api_approval_requires_configured_operator_identity(monkeypatch):
    monkeypatch.delenv("HANDS_OFF_OPERATOR_ID", raising=False)
    control = control_api.SystemControl.__new__(control_api.SystemControl)

    assert control.approve("cmd-1")["status"] == "denied"
    assert control.reject("cmd-1", actor_id="operator-1")["status"] == "denied"


def test_control_api_approval_compares_authenticated_operator(monkeypatch):
    monkeypatch.setenv("HANDS_OFF_OPERATOR_ID", "operator-1")
    control = control_api.SystemControl.__new__(control_api.SystemControl)
    control._load_approval_queue = lambda: {
        "pending": [{"id": "cmd-1", "queued_at": "now"}],
        "approved": [],
        "rejected": [],
    }
    saved = []
    control._save_approval_queue = lambda queue: saved.append(queue)
    control._stamp_command_approval = lambda *args, **kwargs: None

    assert control.approve("cmd-1", actor_id="wrong")["status"] == "denied"
    result = control.approve("cmd-1", actor_id="operator-1")
    assert result["status"] == "approved"
    assert saved[-1]["approved"][0]["id"] == "cmd-1"
