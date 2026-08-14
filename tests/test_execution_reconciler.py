from ai.factory.execution_journal import FactoryExecutionJournal
from ai.factory.execution_reconciler import FactoryExecutionReconciler


def test_reconciler_classifies_unresolved_execution_without_replay(tmp_path):
    journal = FactoryExecutionJournal(str(tmp_path / "journal.json"))
    journal.record("exec-1", "STARTED", {"objective": "safe restart"})

    reconciler = FactoryExecutionReconciler(journal)
    candidates = reconciler.inspect()

    assert len(candidates) == 1
    assert candidates[0]["execution_id"] == "exec-1"
    assert candidates[0]["state"] == "STARTED"
    assert candidates[0]["reconciliation"] == "AMBIGUOUS_REVIEW_REQUIRED"


def test_reconciler_ignores_terminal_execution(tmp_path):
    journal = FactoryExecutionJournal(str(tmp_path / "journal.json"))
    journal.record("exec-2", "STARTED", {"objective": "completed work"})
    journal.record("exec-2", "COMPLETED", {"objective": "completed work"})

    assert FactoryExecutionReconciler(journal).inspect() == []
