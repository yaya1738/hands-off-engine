from ai.factory.memory import FactoryMemory


def test_memory_stores_records():
    memory = FactoryMemory()

    memory.remember(
        {
            "task": "build pipeline",
            "status": "SUCCESS",
        }
    )

    results = memory.recall_all()

    assert len(results) == 1
    assert results[0]["status"] == "SUCCESS"


def test_memory_search():
    memory = FactoryMemory()

    memory.remember({"status": "FAILED"})
    memory.remember({"status": "SUCCESS"})

    results = memory.find_by_status("FAILED")

    assert len(results) == 1
