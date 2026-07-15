from ai.factory.version_intelligence import (
    FactoryVersionIntelligence,
)


def build():
    return FactoryVersionIntelligence()


def test_register_version():
    engine = build()

    result = engine.register_version(
        "engine",
        "1.0",
    )

    assert result["registered"] is True


def test_compare_versions():
    engine = build()

    result = engine.compare_versions(
        "engine"
    )

    assert result["compared"] is True


def test_validate_upgrade():
    engine = build()

    result = engine.validate_upgrade(
        "engine",
        "2.0",
    )

    assert result["validated"] is True


def test_rollback_version():
    engine = build()

    result = engine.rollback_version(
        "engine"
    )

    assert result["rolled_back"] is True


def test_history():
    engine = build()

    engine.register_version(
        "x",
        "1",
    )

    assert len(engine.history()) == 1
