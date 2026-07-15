from ai.factory.resource_management import (
    FactoryResourceManagement,
)


def build():
    return FactoryResourceManagement()


def test_register_resource():
    manager = build()

    result = manager.register_resource(
        "CPU",
        {
            "units": 4,
        }
    )

    assert result["registered"] is True


def test_allocate_resource():
    manager = build()

    result = manager.allocate_resource(
        "CPU",
        {
            "task": "RUN",
        }
    )

    assert result["allocated"] is True


def test_release_resource():
    manager = build()

    result = manager.release_resource(
        "CPU"
    )

    assert result["released"] is True


def test_check_capacity():
    manager = build()

    result = manager.check_capacity()

    assert result["capacity_available"] is True


def test_history():
    manager = build()

    manager.register_resource(
        "A",
        {}
    )

    assert len(manager.history()) == 1
