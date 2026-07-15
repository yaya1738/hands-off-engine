from ai.factory.config_manager import (
    FactoryConfigManager,
)


def test_load():
    manager = FactoryConfigManager()

    result = manager.load(
        {
            "mode": "SAFE",
        }
    )

    assert result["status"] == "LOADED"


def test_validate():
    manager = FactoryConfigManager()

    result = manager.validate()

    assert result["valid"] is True


def test_update():
    manager = FactoryConfigManager()

    result = manager.update(
        "threshold",
        0.8,
    )

    assert result["value"] == 0.8


def test_history():
    manager = FactoryConfigManager()

    manager.validate()

    assert len(manager.history()) == 1
