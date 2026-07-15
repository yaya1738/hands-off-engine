from ai.factory.deployment_manager import (
    FactoryDeploymentManager,
)


def test_prepare():
    manager = FactoryDeploymentManager()

    result = manager.prepare(
        "v1",
    )

    assert result["status"] == "READY"


def test_deploy():
    manager = FactoryDeploymentManager()

    manager.prepare("v1")

    result = manager.deploy()

    assert result["status"] == "DEPLOYED"


def test_rollback():
    manager = FactoryDeploymentManager()

    result = manager.rollback()

    assert result["status"] == "ROLLED_BACK"


def test_status():
    manager = FactoryDeploymentManager()

    manager.prepare("v1")

    assert manager.status()["version"] == "v1"


def test_history():
    manager = FactoryDeploymentManager()

    manager.prepare("v1")

    assert len(manager.history()) == 1
