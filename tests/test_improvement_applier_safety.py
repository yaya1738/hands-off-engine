import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import improvement_applier


class ImprovementApplierSafetyTests(unittest.TestCase):
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
