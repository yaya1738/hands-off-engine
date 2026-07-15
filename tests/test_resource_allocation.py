from ai.factory.resource_allocation import (
    FactoryResourceAllocation,
)


def build():
    return FactoryResourceAllocation()


def test_register_resource():
    allocator = build()

    result = allocator.register_resource(
        "cpu",
        10,
    )

    assert result["registered"] is True


def test_allocate():
    allocator = build()

    result = allocator.allocate(
        "cpu",
        {
            "goal": "RUN",
        }
    )

    assert result["allocated"] is True


def test_rebalance():
    allocator = build()

    result = allocator.rebalance()

    assert result["rebalanced"] is True


def test_availability():
    allocator = build()

    allocator.register_resource(
        "memory",
        5,
    )

    result = allocator.availability()

    assert "memory" in result["resources"]


def test_history():
    allocator = build()

    allocator.rebalance()

    assert len(allocator.history()) == 1
