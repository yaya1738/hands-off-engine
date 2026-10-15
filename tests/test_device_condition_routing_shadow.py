from datetime import datetime, timezone

from scripts.device_condition_routing_shadow import assess_node_routing_shadow

NOW = datetime(2026, 10, 15, 17, 0, tzinfo=timezone.utc)


def observation(minutes_ago, snapshot, assessment=None):
    from datetime import timedelta
    return {
        "observed_at": (NOW - timedelta(minutes=minutes_ago)).isoformat(),
        "snapshot": snapshot,
        "assessment": assessment or {},
    }


def test_missing_observations_are_unknown_even_if_runtime_heartbeat_is_recent():
    result = assess_node_routing_shadow(
        {"node_id": "node-1", "health": "healthy", "last_heartbeat": NOW.isoformat()},
        now=NOW,
    )
    assert result["device_condition"]["status"] == "unknown"
    assert result["recommendation"] == "collect_fresh_observations"
    assert result["dispatch_changed"] is False


def test_stale_observations_do_not_become_healthy_from_heartbeat():
    result = assess_node_routing_shadow(
        {"node_id": "node-1", "health": "healthy", "last_heartbeat": NOW.isoformat(),
         "device_condition_history": [observation(90, {"battery_percent": 95})]},
        now=NOW,
    )
    assert result["device_condition"]["status"] == "stale"
    assert "device_condition_stale" in result["reasons"]
    assert result["recommendation"] == "collect_fresh_observations"


def test_repeated_thermal_events_generate_only_shadow_advice():
    result = assess_node_routing_shadow(
        {"node_id": "node-1", "device_condition_history": [
            observation(10, {"temperature_c": 43}),
            observation(5, {"temperature_c": 44}),
        ]},
        task_class="intensive", now=NOW,
    )
    assert result["recommendation"] == "consider_alternate_capable_node"
    assert "recurring_thermal_pressure" in result["reasons"]
    assert result["decision_mode"] == "shadow"
    assert result["dispatch_changed"] is False
    assert result["authorization_changed"] is False


def test_clean_fresh_observations_do_not_claim_device_is_perfect():
    result = assess_node_routing_shadow(
        {"node_id": "node-1", "device_condition_history": [
            observation(2, {"battery_percent": 80, "temperature_c": 30}),
        ]},
        now=NOW,
    )
    assert result["recommendation"] == "no_condition_based_objection"
    assert result["device_condition"]["status"] == "fresh"


def test_unknown_task_class_fails_to_manual_policy_review():
    result = assess_node_routing_shadow(
        {"device_condition_history": [observation(1, {"temperature_c": 30})]},
        task_class="unclassified", now=NOW,
    )
    assert result["recommendation"] == "manual_policy_review"
    assert "unknown_task_class" in result["reasons"]



def test_recent_resource_pressure_is_visible_in_shadow_advice():
    result = assess_node_routing_shadow(
        {"node_id": "node-1", "device_condition_history": [
            observation(2, {"battery_percent": 18},
                        {"concerns": ["memory_pressure"], "warnings": ["battery_low"]}),
        ]},
        task_class="intensive", now=NOW,
    )
    assert "recurring_resource_pressure" in result["reasons"]
    assert result["recommendation"] == "consider_alternate_capable_node"
    assert result["dispatch_changed"] is False
