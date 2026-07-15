from ai.factory.command_history import FactoryCommandHistory


def test_command_history_records():
    history = FactoryCommandHistory()

    history.record(
        "run_task",
        {
            "task_id": "001",
        },
        {
            "status": "SUCCESS",
        },
    )

    records = history.all()

    assert len(records) == 1
    assert records[0]["command"] == "run_task"


def test_find_command():
    history = FactoryCommandHistory()

    history.record(
        "status",
        {},
        {
            "status": "HEALTHY",
        },
    )

    result = history.find("status")

    assert len(result) == 1
    assert result[0]["result"]["status"] == "HEALTHY"
