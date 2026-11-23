import json

from audit import get_audit_logger


def test_component_logger_records_action_and_metadata(tmp_path):
    audit = get_audit_logger(component="tests.component", log_dir=str(tmp_path))

    event = audit.log_action(
        action_type="unit_test_action",
        action_data={"source": "test", "count": 3},
        result="completed",
    )

    assert event.component == "tests.component"
    assert event.action == "unit_test_action"
    assert event.outcome == "completed"
    assert event.metadata == {"source": "test", "count": 3}
    log_file = tmp_path / "tests_component.jsonl"
    assert log_file.exists()
    saved = json.loads(log_file.read_text(encoding="utf-8").splitlines()[0])
    assert saved["metadata"]["count"] == 3


def test_component_logger_supports_documented_edge_and_order_methods(tmp_path):
    audit = get_audit_logger(component="tests.market", log_dir=str(tmp_path))

    edge = audit.log_edge_detection(
        market="market-1",
        p_fair=0.6,
        p_market=0.5,
        edge=0.1,
        action="BUY YES",
    )
    simulated = audit.log_order(
        order_type="limit",
        market="market-1",
        side="YES",
        size=5.0,
        dryrun=True,
    )
    live_intent = audit.log_order(
        order_type="limit",
        market="market-1",
        side="YES",
        size=5.0,
        dryrun=False,
    )

    assert edge.action == "edge_detection"
    assert simulated.action == "order_intent"
    assert simulated.outcome == "simulated"
    assert live_intent.outcome == "submitted_unverified"
