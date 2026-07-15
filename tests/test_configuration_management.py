from ai.factory.configuration_management import (
    FactoryConfigurationManagement,
)


def build():
    return FactoryConfigurationManagement()


def test_set_config():
    manager = build()

    result = manager.set_config(
        "mode",
        "ACTIVE",
    )

    assert result["set"] is True


def test_get_config():
    manager = build()

    manager.set_config(
        "x",
        1,
    )

    result = manager.get_config(
        "x"
    )

    assert result["found"] is True


def test_update_config():
    manager = build()

    result = manager.update_config(
        {
            "a": 1,
        }
    )

    assert result["updated"] is True


def test_validate_config():
    manager = build()

    result = manager.validate_config()

    assert result["valid"] is True


def test_history():
    manager = build()

    manager.set_config(
        "x",
        1,
    )

    assert len(manager.history()) == 1
