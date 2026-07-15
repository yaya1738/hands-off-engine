from ai.factory.dependency_intelligence import (
    FactoryDependencyIntelligence,
)


def build():
    return FactoryDependencyIntelligence()


def test_register_dependency():
    engine = build()

    result = engine.register_dependency(
        "engine",
        "state",
    )

    assert result["registered"] is True


def test_resolve_dependencies():
    engine = build()

    result = engine.resolve_dependencies(
        "engine"
    )

    assert result["resolved"] is True


def test_check_dependency_health():
    engine = build()

    result = engine.check_dependency_health(
        "engine"
    )

    assert result["checked"] is True


def test_update_dependency():
    engine = build()

    result = engine.update_dependency(
        "engine",
        "events",
    )

    assert result["updated"] is True


def test_history():
    engine = build()

    engine.register_dependency(
        "x",
        "y",
    )

    assert len(engine.history()) == 1
