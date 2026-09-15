import json
from pathlib import Path

from scripts.factory_interaction_health import read_factory_interaction_metrics


def test_factory_interaction_metrics_reuse_bounded_health(tmp_path: Path):
    bus = tmp_path / "ai" / "coordination" / "messages.jsonl"
    bus.parent.mkdir(parents=True)
    bus.write_text(
        "\n".join(
            [
                json.dumps({"msg_id": "m-1", "type": "task_assignment", "context": {"task_id": "t-1"}}),
                json.dumps({"msg_id": "m-2", "type": "task_result", "context": {"task_id": "t-1", "reply_to": "m-1"}}),
                json.dumps({"msg_id": "m-3", "type": "event"}),
                json.dumps({"msg_id": "m-4", "type": "reply", "context": {"reply_to": "missing"}}),
            ]
        )
        + "\n"
    )

    metrics = read_factory_interaction_metrics(tmp_path, bus_limit=4)

    assert metrics["available"] is True
    assert metrics["interaction_event_count"] == 4
    assert metrics["interaction_correlated_event_count"] == 2
    assert metrics["interaction_correlation_rate"] == 0.5
    assert metrics["interaction_orphan_reply_count"] == 1
    assert metrics["interaction_single_event_count"] == 1
    assert metrics["interaction_window_truncated"] is False
    assert metrics["interaction_health"]["event_count"] == 4
    assert metrics["interaction_health"]["admission_observation"] == {"available": False}


def test_factory_interaction_metrics_include_shared_admission_observation(tmp_path: Path):
    bus = tmp_path / "ai" / "coordination" / "messages.jsonl"
    bus.parent.mkdir(parents=True)
    bus.write_text(
        json.dumps(
            {
                "msg_id": "bus-1",
                "type": "inbound_from_agent",
                "payload": {
                    "event_type": "task_admission",
                    "decision": {
                        "msg_id": "req-1",
                        "reply_to": "req-1",
                        "task_id": "task-1",
                        "admitted": True,
                        "reason": "accepted",
                        "decided_at": "2026-09-15T06:00:00Z",
                        "secret": "must-not-escape",
                    },
                },
            }
        )
        + "\n"
    )

    metrics = read_factory_interaction_metrics(tmp_path, bus_limit=1)

    assert metrics["interaction_health"]["admission_observation"] == {
        "available": True,
        "msg_id": "req-1",
        "reply_to": "req-1",
        "task_id": "task-1",
        "admitted": True,
        "reason": "accepted",
        "decided_at": "2026-09-15T06:00:00Z",
    }
    assert "secret" not in str(metrics)


def test_factory_interaction_metrics_do_not_infer_relationships(tmp_path: Path):
    bus = tmp_path / "ai" / "coordination" / "messages.jsonl"
    bus.parent.mkdir(parents=True)
    bus.write_text(
        json.dumps({"msg_id": "m-1", "type": "event"})
        + "\n"
        + json.dumps({"msg_id": "m-2", "type": "event"})
        + "\n"
    )

    metrics = read_factory_interaction_metrics(tmp_path, bus_limit=2)

    assert metrics["interaction_correlated_event_count"] == 0
    assert metrics["interaction_single_event_count"] == 2
