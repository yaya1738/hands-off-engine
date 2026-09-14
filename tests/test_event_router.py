import json, sys, tempfile, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _make_router():
    """Create a router with temp state dir."""
    from scripts.event_router import EventRouter, MESSAGES_FILE, STATE_DIR, ROUTER_STATE, INBOUND_DIR, TRIGGER_REQUESTS
    import scripts.event_router as r
    tmp = Path(tempfile.mkdtemp())
    (tmp / "state").mkdir()
    (tmp / "ai" / "coordination").mkdir(parents=True)

    router = EventRouter.__new__(EventRouter)
    router.repo_root = tmp
    router.state_dir = tmp / "state"
    router.processed_ids = set()
    router.cursor = 0

    r.MESSAGES_FILE = tmp / "ai" / "coordination" / "messages.jsonl"
    r.ROUTER_STATE = tmp / "state" / "router_state.json"
    r.TRIGGER_REQUESTS = tmp / "state" / "trigger_requests.jsonl"
    r.INBOUND_DIR = tmp / "state" / "inbound"
    r.INBOUND_DIR.mkdir(exist_ok=True)

    router._tmp = tmp
    return router


def _write_msg(router, msg):
    """Append a message to the messages.jsonl."""
    import scripts.event_router as r
    with open(r.MESSAGES_FILE, "a") as f:
        f.write(json.dumps(msg) + "\n")


def test_classify_wake_event():
    router = _make_router()
    msg = {
        "type": "continuation_event",
        "context": {"event_type": "task_completed", "is_wake": True},
    }
    assert router.classify_event(msg) == "wake"


def test_classify_heartbeat():
    router = _make_router()
    msg = {
        "type": "continuation_event",
        "context": {"event_type": "heartbeat", "is_wake": False},
    }
    assert router.classify_event(msg) == "heartbeat"


def test_classify_task_result_as_wake():
    router = _make_router()
    msg = {"type": "task_result", "context": {}}
    assert router.classify_event(msg) == "wake"


def test_classify_system_status_as_heartbeat():
    router = _make_router()
    msg = {"type": "system_status", "context": {}}
    assert router.classify_event(msg) == "heartbeat"


def test_route_task_result_to_factory():
    router = _make_router()
    msg = {
        "from": "anyclaw", "type": "task_result",
        "msg_id": "result-001",
        "context": {"task_id": "t-001"},
    }
    record = router.route_event(msg)
    assert record is not None
    assert record["to"] == "factory"
    assert record["routed"] is True


def test_route_task_assignment_to_anyclaw():
    router = _make_router()
    msg = {
        "from": "factory", "type": "task_assignment",
        "msg_id": "task-001",
        "context": {"task_id": "t-001", "action": "health_check"},
    }
    record = router.route_event(msg)
    assert record is not None
    assert record["to"] == "anyclaw"
    assert record["routed"] is True


def test_dedup_by_msg_id():
    router = _make_router()
    msg = {
        "from": "anyclaw", "type": "task_result",
        "msg_id": "dup-001",
        "context": {"task_id": "t-dup"},
    }
    # Write same message twice
    _write_msg(router, msg)
    _write_msg(router, msg)

    count = router.process_once()
    assert count == 1, f"Should dedup, routed {count}"


def test_process_once_end_to_end():
    router = _make_router()
    msg = {
        "from": "anyclaw", "type": "task_result",
        "msg_id": "e2e-001",
        "context": {"task_id": "t-e2e", "status": "success"},
    }
    _write_msg(router, msg)
    count = router.process_once()
    assert count == 1

    # Verify routed to factory's inbound
    inbound = router.state_dir / "inbound" / "factory.jsonl"
    assert inbound.exists()
    records = [json.loads(l) for l in inbound.read_text().strip().split("\n") if l.strip()]
    assert len(records) == 1
    assert records[0]["to"] == "factory"


def test_trigger_request_created_for_external_party():
    router = _make_router()
    msg = {
        "from": "anyclaw", "type": "continuation_event",
        "msg_id": "trigger-001",
        "context": {"event_type": "task_completed", "is_wake": True, "task_id": "t-trig"},
        "message": "Task completed",
    }
    _write_msg(router, msg)
    router.process_once()

    triggers = router.get_pending_triggers()
    assert len(triggers) == 1
    assert triggers[0]["target_party"] == "factory"


def test_no_trigger_for_non_wake():
    router = _make_router()
    msg = {
        "from": "anyclaw", "type": "continuation_event",
        "msg_id": "hb-001",
        "context": {"event_type": "heartbeat", "is_wake": False},
        "message": "alive",
    }
    _write_msg(router, msg)
    router.process_once()

    triggers = router.get_pending_triggers()
    assert len(triggers) == 0


def test_status():
    router = _make_router()
    status = router.get_status()
    assert status["cursor"] == 0
    assert status["processed_count"] == 0
    assert status["pending_triggers"] == 0


def test_approval_needed_routes_to_operator():
    router = _make_router()
    msg = {
        "from": "anyclaw", "type": "blocker",
        "msg_id": "block-001",
        "context": {"event_type": "approval_needed"},
        "message": "Need approval",
    }
    record = router.route_event(msg)
    assert record["to"] == "operator"
