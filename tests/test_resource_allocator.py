from ai.factory.resource_allocator import (
    FactoryResourceAllocator,
)


def build():
    return FactoryResourceAllocator()


def test_request():
    allocator = build()

    result = allocator.request(
        {
            "compute": 10,
        }
    )

    assert result["requested"] is True


def test_allocate():
    allocator = build()

    result = allocator.allocate(
        {
            "mission": "A",
        }
    )

    assert result["allocated"] is True


def test_prioritize():
    allocator = build()

    result = allocator.prioritize(
        [
            {
                "id": 1,
            }
        ]
    )

    assert result["priority"]["id"] == 1


def test_utilization():
    allocator = build()

    allocator.request(
        {
            "cpu": 1,
        }
    )

    result = allocator.utilization()

    assert result["resources"] == 1


def test_history():
    allocator = build()

    allocator.request({})

    assert len(allocator.history()) == 1
