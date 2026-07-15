from ai.factory.state_manager import (
    FactoryStateManager,
)


def test_save():
    manager = FactoryStateManager()

    result = manager.save(
        {
            "running": True,
        }
    )

    assert result["status"] == "SAVED"


def test_load():
    manager = FactoryStateManager()

    manager.save(
        {
            "mode": "AUTO",
        }
    )

    result = manager.load()

    assert result["state"]["mode"] == "AUTO"


def test_checkpoint():
    manager = FactoryStateManager()

    manager.save(
        {
            "version": 1,
        }
    )

    result = manager.checkpoint()

    assert result["checkpoint"]["version"] == 1


def test_history():
    manager = FactoryStateManager()

    manager.save({})

    assert len(manager.history()) == 1
