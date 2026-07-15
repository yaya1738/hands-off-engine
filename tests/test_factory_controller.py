from ai.factory.controller import FactoryController


def test_factory_controller_runs_full_cycle():
    factory = FactoryController()

    result = factory.build(
        "factory-001",
        "create audit integration",
    )

    assert result["task_id"] == "factory-001"
    assert result["execution"].status == "SUCCESS"
    assert result["verification"]["valid"] is True


def test_factory_memory_updated():
    factory = FactoryController()

    factory.build(
        "factory-002",
        "test memory",
    )

    records = factory.memory.recall_all()

    assert len(records) == 1
    assert records[0]["status"] == "SUCCESS"
