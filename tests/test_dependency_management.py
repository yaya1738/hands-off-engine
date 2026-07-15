from ai.factory.dependency_management import (
    FactoryDependencyManagement,
)


def build():
    return FactoryDependencyManagement()


def test_register_dependency():
    manager = build()

    result = manager.register_dependency(
        "engine",
        "database",
    )

    assert result["registered"] is True


def test_remove_dependency():
    manager = build()

    result = manager.remove_dependency(
        "engine",
        "database",
    )

    assert result["removed"] is True


def test_resolve_dependencies():
    manager = build()

    result = manager.resolve_dependencies(
        "engine"
    )

    assert result["resolved"] is True


def test_check_health():
    manager = build()

    result = manager.check_health()

    assert result["healthy"] is True


def test_history():
    manager = build()

    manager.check_health()

    assert len(manager.history()) == 1
