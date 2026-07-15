from ai.factory.job_results import (
    FactoryJobResults,
)


def test_record_result():
    store = FactoryJobResults()

    store.record(
        "job-001",
        "SUCCESS",
        {
            "value": 10,
        },
    )

    result = store.get(
        "job-001"
    )

    assert result["status"] == "SUCCESS"
    assert result["output"]["value"] == 10


def test_find_by_status():
    store = FactoryJobResults()

    store.record(
        "job-002",
        "FAILED",
    )

    results = store.find_by_status(
        "FAILED"
    )

    assert len(results) == 1


def test_list_results():
    store = FactoryJobResults()

    assert store.list() == []
