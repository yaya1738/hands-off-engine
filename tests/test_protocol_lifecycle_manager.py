from ai.factory.protocol_lifecycle_manager import (
    FactoryProtocolLifecycleManager,
)


def test_register_protocol():

    manager = FactoryProtocolLifecycleManager()

    result = manager.register_protocol(
        "capability_onboarding",
        "FactoryRuntime",
        "integrate new capabilities",
        [
            "verification",
            "history",
        ],
    )

    assert result["registered"] is True


def test_verify_protocol():

    manager = FactoryProtocolLifecycleManager()

    manager.register_protocol(
        "workflow",
        "FactoryRuntime",
        "execute reusable workflows",
    )

    result = manager.verify_protocol("workflow")

    assert result["verified"] is True


def test_status():

    manager = FactoryProtocolLifecycleManager()

    manager.register_protocol(
        "test",
        "runtime",
        "testing",
    )

    assert manager.status()["count"] == 1
