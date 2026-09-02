"""Checkpoint analysis with a fail-closed workspace-inspection boundary."""

from typing import Any, Dict, List
from ai.factory.change_classifier import FactoryChangeClassifier
from ai.factory.change_scope_analyzer import FactoryChangeScopeAnalyzer


class FactoryCheckpointManager:
    def __init__(self, validator=None, allowed_paths=None):
        self.validator = validator
        self.allowed_paths = allowed_paths or [
            "ai/factory/",
            "tests/",
            "tools/",
        ]
        self._history: List[Dict[str, Any]] = []
        self.classifier = FactoryChangeClassifier()
        self.scope_analyzer = FactoryChangeScopeAnalyzer()

    def _git_changes(self):
        """Return no locally executed git state; authority is required."""
        return []

    def _analyze_changes(self, changes):
        unexpected = []
        temporary_patterns = ("apply_", "update_", "integrate_")
        for item in changes:
            path = item[2:].strip() if len(item) > 2 else item
            if any(path.startswith(pattern) for pattern in temporary_patterns):
                unexpected.append(path)
            elif not any(path.startswith(prefix) for prefix in self.allowed_paths):
                unexpected.append(path)
        return unexpected

    def evaluate(self):
        changes = self._git_changes()
        validation = self.validator() if self.validator else None
        validation_state = (
            validation.get("state") if isinstance(validation, dict) else "NOT_RUN"
        )
        unexpected = self._analyze_changes(changes)
        classification = self.classifier.classify([item[2:].strip() for item in changes])
        scope = self.scope_analyzer.analyze(classification.get("classified", []))
        state = "REVIEW_REQUIRED"
        action = "SUBMIT_WORKSPACE_INSPECTION"
        report = {
            "state": state,
            "action": action,
            "validation_state": validation_state,
            "changed_files_count": len(changes),
            "classification_warnings": unexpected,
            "classification": classification,
            "scope": scope,
            "authority_required": True,
            "authority": "FactoryAuthorityGateway",
        }
        self._history.append(report)
        return report

    def history(self):
        return self._history
