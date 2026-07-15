from ai.factory.production_guard import (
    FactoryProductionGuard,
)


def test_validate_ready():
    guard = FactoryProductionGuard()

    result = guard.validate(
        {
            "required": True,
        }
    )

    assert result["status"] == "READY"


def test_validate_blocked():
    guard = FactoryProductionGuard()

    result = guard.validate(
        {
            "required": False,
        }
    )

    assert result["status"] == "BLOCKED"


def test_safe_mode():
    guard = FactoryProductionGuard()

    result = guard.safe_mode()

    assert result["mode"] == "SAFE"


def test_health():
    guard = FactoryProductionGuard()

    result = guard.health_report()

    assert result["status"] == "HEALTHY"


def test_history():
    guard = FactoryProductionGuard()

    guard.health_report()

    assert len(guard.history()) == 1
