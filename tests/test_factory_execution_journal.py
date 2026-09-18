import json

from ai.factory.execution_journal import FactoryExecutionJournal


def test_execution_journal_replays_idempotency(tmp_path):
    journal = FactoryExecutionJournal(str(tmp_path / "journal.json"))

    first = journal.record(
        "exec-1",
        "STARTED",
        {"objective": "inspect runtime", "idempotency_key": "task-1"},
    )
    assert first["state"] == "STARTED"

    found = journal.find_by_idempotency_key("task-1")
    assert found["execution_id"] == "exec-1"

    terminal = journal.record(
        "exec-1",
        "COMPLETED",
        {
            "objective": "inspect runtime",
            "idempotency_key": "task-1",
            "result": {"status": "verified"},
        },
    )
    assert terminal["state"] == "COMPLETED"

    reloaded = FactoryExecutionJournal(str(tmp_path / "journal.json"))
    replay = reloaded.find_by_idempotency_key("task-1")
    assert replay["state"] == "COMPLETED"
    assert replay["intent"]["result"]["status"] == "verified"


def test_execution_journal_rejects_terminal_transition(tmp_path):
    journal = FactoryExecutionJournal(str(tmp_path / "journal.json"))
    journal.record("exec-2", "STARTED", {"objective": "x"})
    journal.record("exec-2", "CANCELLED", {"objective": "x"})

    try:
        journal.record("exec-2", "COMPLETED", {"objective": "x"})
    except ValueError as exc:
        assert "illegal execution lifecycle transition" in str(exc)
    else:
        raise AssertionError("terminal execution must not transition again")
