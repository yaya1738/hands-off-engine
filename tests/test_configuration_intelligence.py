from ai.factory.configuration_intelligence import (
    FactoryConfigurationIntelligence,
)


def build():
    return FactoryConfigurationIntelligence()


def test_load_config():
    manager = build()

    result = manager.load_config(
        {}
    )

    assert result["loaded"] is True


def test_validate_config():
    manager = build()

    result = manager.validate_config(
        {}
    )

    assert result["validated"] is True


def test_update_config():
    manager = build()

    result = manager.update_config(
        {}
    )

    assert result["updated"] is True


def test_rollback_config():
    manager = build()

    result = manager.rollback_config()

    assert result["rolled_back"] is True


def test_history():
    manager = build()

    manager.load_config(
        {}
    )

    assert len(manager.history()) == 1
