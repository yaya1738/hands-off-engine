import pytest

from ai.factory.resource_allocator import FactoryResourceAllocator


def test_allocation_amount_is_bounded():
    allocator = FactoryResourceAllocator(max_allocation_amount=2)
    assert allocator.allocate_resources({"task": "x"}, 2)["allocated"] is True
    with pytest.raises(ValueError):
        allocator.allocate_resources({"task": "x"}, 3)


def test_invalid_amounts_fail_closed():
    allocator = FactoryResourceAllocator()
    for amount in (0, -1, True, 1.5, "1"):
        with pytest.raises(ValueError):
            allocator.allocate_resources({"task": "x"}, amount)


def test_outstanding_allocations_are_bounded():
    allocator = FactoryResourceAllocator(max_outstanding_allocations=2)
    allocator.allocate_resources({"task": "1"})
    allocator.allocate_resources({"task": "2"})
    with pytest.raises(RuntimeError):
        allocator.allocate_resources({"task": "3"})
