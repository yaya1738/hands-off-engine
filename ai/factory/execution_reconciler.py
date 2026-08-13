from typing import Any, Dict, List

from ai.factory.execution_journal import FactoryExecutionJournal


class FactoryExecutionReconciler:
    """Classify interrupted executions without replaying side effects."""

    def __init__(self, journal: FactoryExecutionJournal):
        self.journal = journal

    def inspect(self) -> List[Dict[str, Any]]:
        """Return unresolved executions as explicit manual-reconciliation candidates."""
        return [
            {
                **entry,
                "reconciliation": "AMBIGUOUS_REVIEW_REQUIRED",
            }
            for entry in self.journal.interrupted()
        ]
