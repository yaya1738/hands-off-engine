from ai.factory.resource_allocation import (
    FactoryResourceAllocation,
)


def build():
    return FactoryResourceAllocation()


def test_register_resource():
    manager = build()

    result = manager.register_resource(
        "cpu",
        {}
    )

    assert result["registered"] is True


def test_allocate_resource():
    manager = build()

    result = manager.allocate_resource(
        "cpu",
        {}
    )

    assert result["allocated"] is True


def test_release_resource():
    manager = build()

    result = manager.release_resource(
        "cpu"
    )

    assert result["released"] is True


def test_optimize_allocation():
    manager = build()

    result = manager.optimize_allocation()

    assert result["optimized"] is True


def test_history():
    manager = build()

    manager.register_resource(
        "x",
        {}
    )

    assert len(manager.history()) == 1
