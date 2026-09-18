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


def test_execution_journal_appends_events_without_rewriting_snapshot():
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "journal.json")
        journal = FactoryExecutionJournal(storage_path=path)

        journal.record("exec-1", "STARTED", {"goal": "continue"})
        assert os.path.exists(path + ".events")
        assert os.path.getsize(path + ".events") > 0

        journal.record("exec-1", "COMPLETED")
        restarted = FactoryExecutionJournal(storage_path=path)
        assert restarted.latest("exec-1")["state"] == "COMPLETED"


def test_execution_journal_loads_legacy_snapshot_and_new_events():
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "journal.json")
        with open(path, "w", encoding="utf-8") as handle:
            import json
            json.dump(
                [{
                    "execution_id": "legacy",
                    "state": "STARTED",
                    "intent": {"goal": "legacy"},
                    "ts": "2026-01-01T00:00:00+00:00",
                }],
                handle,
            )

        journal = FactoryExecutionJournal(storage_path=path)
        journal.record("legacy", "COMPLETED")
        restarted = FactoryExecutionJournal(storage_path=path)
        assert restarted.latest("legacy")["state"] == "COMPLETED"
        assert len(restarted.history()) == 2

