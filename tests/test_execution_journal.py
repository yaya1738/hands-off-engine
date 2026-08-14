import os
import tempfile

from ai.factory.execution_journal import FactoryExecutionJournal


def test_execution_journal_survives_restart_and_finds_interrupted_work():
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "journal.json")

        first = FactoryExecutionJournal(storage_path=path)
        first.record("exec-1", "STARTED", {"goal": "continue"})

        second = FactoryExecutionJournal(storage_path=path)
        interrupted = second.interrupted()

        assert second.latest("exec-1")["state"] == "STARTED"
        assert interrupted[0]["execution_id"] == "exec-1"

        second.record("exec-1", "COMPLETED")
        third = FactoryExecutionJournal(storage_path=path)
        assert third.interrupted() == []
