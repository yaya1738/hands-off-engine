from ai.factory.audit_bridge import FactoryAuditBridge


def test_factory_event_converted_to_audit_event():
    bridge = FactoryAuditBridge()

    event = bridge.create_audit_event(
        "factory-001",
        "BUILD_COMPLETE",
        {
            "status": "SUCCESS",
        },
    )

    assert event["source"] == "factory"
    assert event["task_id"] == "factory-001"
    assert event["action"] == "BUILD_COMPLETE"
    assert event["result"]["status"] == "SUCCESS"
