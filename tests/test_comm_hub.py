import json, sys, tempfile, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.comm_hub import CommHub, DEFAULT_PARTIES


def _make_hub():
    """Make a hub with a temp state dir to avoid touching real state."""
    tmp = Path(tempfile.mkdtemp())
    hub = CommHub.__new__(CommHub)
    hub.repo_root = tmp
    hub.state_dir = tmp / "state"
    hub.state_dir.mkdir(exist_ok=True)
    (tmp / "ai" / "coordination").mkdir(parents=True, exist_ok=True)
    (tmp / "state" / "inbound").mkdir(parents=True, exist_ok=True)
    (tmp / "state" / "outbound").mkdir(parents=True, exist_ok=True)
    hub.parties = dict(DEFAULT_PARTIES)
    hub.pending_acks = {}
    hub._tmp = tmp
    return hub


def test_default_parties_loaded():
    hub = _make_hub()
    assert len(hub.list_parties()) >= 5
    ids = [p["id"] for p in hub.list_parties()]
    assert "operator" in ids
    assert "claude-code" in ids


def test_register_party():
    hub = _make_hub()
    hub.register_party("test-bot", "Test Bot", "agent", ["webhook"], trust_level=3)
    p = hub.get_party("test-bot")
    assert p is not None
    assert p["trust_level"] == 3
    assert "webhook" in p["channels"]


def test_send_to_subscribed_party():
    hub = _make_hub()
    result = hub.send("operator", "system_status", {"health": "ok"})
    assert result["status"] == "sent"
    assert "id" in result


def test_send_skips_unsubscribed_party():
    hub = _make_hub()
    result = hub.send("copilot", "daily_digest", {"summary": "test"})
    # copilot is not subscribed to daily_digest
    assert result["status"] == "skipped"


def test_send_to_unknown_party():
    hub = _make_hub()
    result = hub.send("nonexistent", "info", {"text": "hi"})
    assert result["status"] == "error"


def test_broadcast():
    hub = _make_hub()
    results = hub.broadcast("system_status", {"health": "ok"})
    # At least operator and system_internal should receive it
    assert len(results) >= 1


def test_receive_inbound():
    hub = _make_hub()
    result = hub.receive("operator", "status_query", {"query": "health"}, channel="telegram")
    assert result["routed_to"] == "status_response"


def test_receive_trade_command():
    hub = _make_hub()
    result = hub.receive("operator", "trade_command", {"action": "trade", "params": {"market": "ETH"}, "mode": "LIVE"}, channel="telegram")
    assert result["routed_to"] == "command_queue"
    assert "command_id" in result


def test_receive_approval():
    hub = _make_hub()
    # First submit a LIVE command so there's something to approve
    from scripts.control_api import SystemControl
    sc = SystemControl.__new__(SystemControl)
    sc.repo_root = hub._tmp
    sc.state_dir = hub._tmp / "state"
    sc.queue_file = sc.state_dir / "command_queue.jsonl"
    sc.results_file = sc.state_dir / "results.jsonl"
    sc.approval_file = sc.state_dir / "approval_queue.json"

    cmd_id = sc.execute(action="trade", params={"market": "ETH"}, mode="LIVE", sync=False)

    # Seed approval queue
    q = {"pending": [{"id": cmd_id, "action": "execute", "mode": "LIVE"}], "approved": [], "rejected": []}
    sc.approval_file.write_text(json.dumps(q, indent=2) + "\n")

    # Receive approve
    result = hub.receive("operator", "approve", {"command_id": cmd_id}, channel="telegram")
    assert result["routed_to"] == "approval_workflow"
    assert result["result"]["status"] == "approved"


def test_acknowledge():
    hub = _make_hub()
    # Send a message that requires ack
    result = hub.send("operator", "trade_alert", {"market": "ETH"})
    msg_id = result["id"]
    # Acknowledge it
    ack = hub.acknowledge(msg_id)
    assert ack["status"] == "acknowledged"
    # Should not be unacknowledged anymore
    unacked = hub.get_unacknowledged()
    assert msg_id not in unacked


def test_telegram_markdown_format():
    hub = _make_hub()
    result = hub.send("operator", "system_status", {"health": "ok", "uptime": "3d"})
    # Should have formatted_text
    assert result["status"] == "sent"


def test_messages_jsonl_written():
    hub = _make_hub()
    hub.send("operator", "system_status", {"health": "ok"})
    msgs_file = hub._tmp / "ai" / "coordination" / "messages.jsonl"
    assert msgs_file.exists()
    lines = msgs_file.read_text().strip().split("\n")
    assert len(lines) >= 1
    entry = json.loads(lines[-1])
    assert entry["to"] == "operator"
