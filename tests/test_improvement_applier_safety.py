import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import improvement_applier


class ImprovementApplierSafetyTests(unittest.TestCase):
    def test_clean_bus_is_queued_without_mutating_canonical_messages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            bus_file = root / "ai" / "coordination" / "messages.jsonl"
            bus_file.parent.mkdir(parents=True)
            original = "".join(json.dumps({"type": "task_assignment", "n": i}) + "\n" for i in range(510))
            bus_file.write_text(original)
            old_state = improvement_applier.APPLIER_STATE
            old_feedback = improvement_applier.FEEDBACK_FILE
            improvement_applier.APPLIER_STATE = state_dir / "applier.json"
            improvement_applier.FEEDBACK_FILE = state_dir / "feedback.json"
            try:
                applier = improvement_applier.ImprovementApplier(repo_root=root)
                candidate = {
                    "id": "imp-clean-bus",
                    "category": "maintenance",
                    "title": "Analyze bus growth",
                    "description": "Do not prune",
                    "action": "clean_bus",
                }
                first = applier.apply_improvement(candidate)
                second = applier.apply_improvement(candidate)
                self.assertFalse(first["applied"])
                self.assertTrue(first["needs_approval"])
                self.assertEqual(second["reason"], "already_queued")
                self.assertEqual(len(applier.get_pending_approvals()), 1)
                self.assertEqual(bus_file.read_text(), original)
                self.assertNotIn("clean_bus", improvement_applier.SAFE_ACTIONS)
                self.assertIn("clean_bus", improvement_applier.RISKY_ACTIONS)
            finally:
                improvement_applier.APPLIER_STATE = old_state
                improvement_applier.FEEDBACK_FILE = old_feedback

    def test_unsupported_risky_action_remains_queued_after_approval_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old_state = improvement_applier.APPLIER_STATE
            old_feedback = improvement_applier.FEEDBACK_FILE
            improvement_applier.APPLIER_STATE = root / "state" / "applier.json"
            improvement_applier.FEEDBACK_FILE = root / "state" / "feedback.json"
            try:
                applier = improvement_applier.ImprovementApplier(repo_root=root)
                queued = applier.apply_improvement({
                    "id": "imp-code-change",
                    "category": "security",
                    "title": "Change source code",
                    "description": "Requires governed executor",
                    "action": "code_change",
                })
                self.assertTrue(queued["needs_approval"])
                result = applier.approve_improvement("imp-code-change")
                self.assertFalse(result["approved"])
                self.assertEqual(result["reason"], "requires_separate_governed_executor")
                self.assertEqual(len(applier.get_pending_approvals()), 1)
                self.assertNotIn("imp-code-change", applier.applied_ids)
            finally:
                improvement_applier.APPLIER_STATE = old_state
                improvement_applier.FEEDBACK_FILE = old_feedback

    def test_maintenance_candidates_are_observational_not_bus_mutations(self):
        from scripts import self_improvement

        self.assertEqual(self_improvement.ACTION_MAP["maintenance"], "log_analysis")
        source = (ROOT / "scripts" / "self_improvement.py").read_text()
        self.assertNotIn("Initialize improvement applier", source)
        self.assertNotIn("Clean up bus messages", source)
        self.assertIn("Analyze coordination bus growth", source)

    def test_add_test_action_requires_approval_and_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            tests_dir = root / "tests"
            old_state = improvement_applier.APPLIER_STATE
            old_feedback = improvement_applier.FEEDBACK_FILE
            improvement_applier.APPLIER_STATE = state_dir / "applier.json"
            improvement_applier.FEEDBACK_FILE = state_dir / "feedback.json"
            try:
                applier = improvement_applier.ImprovementApplier(repo_root=root)
                result = applier.apply_improvement({
                    "id": "imp-add-test",
                    "category": "quality",
                    "title": "Add tests for module",
                    "description": "Generate test stub",
                    "action": "add_test",
                })

                self.assertFalse(result["applied"])
                self.assertTrue(result["needs_approval"])
                self.assertFalse(tests_dir.exists())
                saved = json.loads(improvement_applier.APPLIER_STATE.read_text())
                self.assertEqual(saved["queued"][0]["id"], "imp-add-test")
            finally:
                improvement_applier.APPLIER_STATE = old_state
                improvement_applier.FEEDBACK_FILE = old_feedback


if __name__ == "__main__":
    unittest.main()