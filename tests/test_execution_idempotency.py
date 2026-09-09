import os
import tempfile

import pytest

from ai.factory.execution_journal import FactoryExecutionJournal


def test_idempotency_key_replays_terminal_result_without_new_execution():
    with tempfile.TemporaryDirectory() as directory:
        journal = FactoryExecutionJournal(os.path.join(directory, "journal.json"))
        intent = {"objective": "same objective", "idempotency_key": "request-1"}
        journal.record("exec-1", "STARTED", intent)
        result = {"status": "verified", "success": True}
        journal.record("exec-1", "COMPLETED", {**intent, "result": result})

        existing = journal.find_by_idempotency_key("request-1")
        assert existing["execution_id"] == "exec-1"
        assert existing["state"] == "COMPLETED"
        assert existing["intent"]["result"] == result


def test_idempotency_key_cannot_be_reused_for_another_objective():
    with tempfile.TemporaryDirectory() as directory:
        journal = FactoryExecutionJournal(os.path.join(directory, "journal.json"))
        journal.record("exec-1", "STARTED", {"objective": "first", "idempotency_key": "request-1"})
        with pytest.raises(ValueError):
            journal.record("exec-1", "STARTED", {"objective": "first", "idempotency_key": "request-1"})


def test_terminal_execution_rejects_duplicate_terminal_transition():
    with tempfile.TemporaryDirectory() as directory:
        journal = FactoryExecutionJournal(os.path.join(directory, "journal.json"))
        journal.record("exec-1", "STARTED")
        journal.record("exec-1", "COMPLETED")
        with pytest.raises(ValueError):
            journal.record("exec-1", "FAILED")
