from ai.factory.resource_allocator import (
    FactoryResourceAllocator,
)


def build():
    return FactoryResourceAllocator()


def test_registry():
    engine = build()

    result = engine.resource_registry(
        "compute",
        {},
    )

    assert result["registered"] is True


def test_estimate():
    engine = build()

    result = engine.estimate_cost({})

    assert result["estimated"] is True


def test_allocate():
    engine = build()

    result = engine.allocate_resources({})

    assert result["allocated"] is True


def test_rebalance():
    engine = build()

    result = engine.rebalance([])

    assert result["rebalanced"] is True


def test_efficiency():
    engine = build()

    result = engine.measure_efficiency({})

    assert result["measured"] is True


def test_history():
    engine = build()

    engine.allocate_resources({})

    assert len(engine.history()) == 1
