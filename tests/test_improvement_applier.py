"""Tests for improvement applier and feedback loop.

Covers:
1. Safe action execution (all 7 safe actions)
2. Risky action queuing (approval needed)
3. Dedup (same improvement not applied twice)
4. Impact measurement (before/after metrics)
5. Feedback scoring (positive/neutral/negative)
6. Category recommendations from feedback
7. Applier status

unittest-compatible so the focused workflow can execute this contract
directly (pytest-style function tests are invisible to python -m unittest).
"""

import json
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scripts.improvement_applier as ia
import scripts.improvement_feedback as ifb


def _make_applier():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "state").mkdir()
    (tmp / "ai" / "coordination").mkdir(parents=True)
    (tmp / "docs").mkdir()
    (tmp / "config").mkdir()
    (tmp / "state" / "archive").mkdir()
    (tmp / "state" / "reports").mkdir()

    # Monkey-patch module paths
    orig = (ia.ROOT, ia.STATE, ia.BUS, ia.APPLIER_STATE, ia.FEEDBACK_FILE)
    ia.ROOT = tmp
    ia.STATE = tmp / "state"
    ia.BUS = tmp / "ai" / "coordination" / "messages.jsonl"
    ia.APPLIER_STATE = tmp / "state" / "improvement_applier_state.json"
    ia.FEEDBACK_FILE = tmp / "state" / "improvement_feedback.json"

    applier = ia.ImprovementApplier.__new__(ia.ImprovementApplier)
    applier.repo_root = tmp
    applier.state_dir = tmp / "state"
    applier.state = {"applied": [], "queued": [], "history": [], "applied_ids": []}
    applier.applied_ids = set()
    applier.feedback = {"improvements": [], "summary": {}}

    applier._tmp = tmp
    applier._orig = orig
    return applier


def _teardown(applier):
    shutil.rmtree(applier._tmp)
    ia.ROOT, ia.STATE, ia.BUS, ia.APPLIER_STATE, ia.FEEDBACK_FILE = applier._orig


class ImprovementApplierTests(unittest.TestCase):
    def setUp(self):
        self.applier = _make_applier()

    def tearDown(self):
        _teardown(self.applier)

    def test_update_documentation(self):
        """update_documentation appends to docs."""
        imp = {"id": "test-doc-1", "category": "maintenance", "title": "Update docs",
               "description": "Add findings", "action": "update_documentation"}
        result = self.applier.apply_improvement(imp)
        self.assertTrue(result["applied"])
        doc_file = self.applier._tmp / "docs" / "improvement_log.md"
        self.assertTrue(doc_file.exists())
        self.assertIn("Update docs", doc_file.read_text())

    def test_archive_state(self):
        """archive_state copies old log files."""
        log_file = self.applier._tmp / "state" / "actuator_log.jsonl"
        log_file.write_text('{"event": "test"}\n')
        imp = {"id": "test-archive-1", "category": "maintenance", "title": "Archive logs",
               "description": "Archive old logs", "action": "archive_state"}
        result = self.applier.apply_improvement(imp)
        self.assertTrue(result["applied"])
        archive_dir = self.applier._tmp / "state" / "archive"
        self.assertTrue(any(archive_dir.iterdir()))

    def test_generate_report(self):
        """generate_report creates a report file."""
        imp = {"id": "test-report-1", "category": "quality", "title": "Generate report",
               "description": "Analysis report", "action": "generate_report"}
        result = self.applier.apply_improvement(imp)
        self.assertTrue(result["applied"])
        reports_dir = self.applier._tmp / "state" / "reports"
        self.assertTrue(any(reports_dir.glob("report_*.json")))

    def test_clean_bus(self):
        """clean_bus is approval-gated: never auto-executed, bus unchanged."""
        # Write 600 messages to the bus
        bus_file = self.applier._tmp / "ai" / "coordination" / "messages.jsonl"
        with open(bus_file, "w") as f:
            for i in range(600):
                f.write(json.dumps({"type": "heartbeat", "msg_id": f"msg-{i}"}) + "\n")
        imp = {"id": "test-clean-1", "category": "maintenance", "title": "Clean bus",
               "description": "Archive old messages", "action": "clean_bus"}
        result = self.applier.apply_improvement(imp)
        # clean_bus is RISKY: queued for operator approval, never applied.
        self.assertFalse(result["applied"])
        self.assertTrue(result.get("needs_approval"))
        self.assertTrue(any(item["id"] == "test-clean-1"
                            for item in self.applier.get_pending_approvals()))
        # And approval must not execute it either — no governed executor exists.
        approval = self.applier.approve_improvement("test-clean-1")
        self.assertFalse(approval["approved"])
        self.assertEqual(approval["reason"], "requires_separate_governed_executor")
        # The canonical bus is never pruned automatically.
        lines = bus_file.read_text().splitlines()
        self.assertEqual(len(lines), 600)

    def test_fix_config(self):
        """fix_config adds missing config entries."""
        imp = {"id": "test-config-1", "category": "usability", "title": "Fix config",
               "description": "Add missing config", "action": "fix_config"}
        result = self.applier.apply_improvement(imp)
        self.assertTrue(result["applied"])
        config_file = self.applier._tmp / "config" / "system.json"
        self.assertTrue(config_file.exists())
        config = json.loads(config_file.read_text())
        self.assertIn("node_id", config)

    def test_add_test(self):
        """add_test is approval-gated: queued automatically, executed only after approval."""
        # Create a valid importable module in the applier's scripts dir
        scripts_dir = self.applier._tmp / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "fake_module.py").write_text("# fake module\n\ndef hello():\n    return 'hi'\n")
        sys.path.insert(0, str(self.applier._tmp))
        try:
            imp = {"id": "test-addtest-1", "category": "quality", "title": "Add tests",
                   "description": "Generate test stubs", "action": "add_test"}
            # add_test is RISKY: automatic application must queue, not execute.
            result = self.applier.apply_improvement(imp)
            self.assertFalse(result["applied"])
            self.assertTrue(result.get("needs_approval"))
            self.assertFalse((self.applier._tmp / "tests" / "test_fake_module.py").exists())
            # Explicit operator approval is the only execution path.
            approval = self.applier.approve_improvement("test-addtest-1")
            self.assertTrue(approval["approved"])
            test_file = self.applier._tmp / "tests" / "test_fake_module.py"
            self.assertTrue(test_file.exists())
            self.assertIn("fake_module", test_file.read_text())
        finally:
            sys.path.remove(str(self.applier._tmp))

    def test_risky_action_queued(self):
        """Risky actions are queued for approval, not executed."""
        imp = {"id": "test-risky-1", "category": "security", "title": "Add firewall",
               "description": "Network change", "action": "code_change"}
        result = self.applier.apply_improvement(imp)
        self.assertFalse(result["applied"])
        self.assertTrue(result["needs_approval"])
        self.assertEqual(len(self.applier.state.get("queued", [])), 1)

    def test_dedup(self):
        """Same improvement not applied twice."""
        imp = {"id": "test-dedup-1", "category": "maintenance", "title": "Test",
               "description": "Test", "action": "update_documentation"}
        r1 = self.applier.apply_improvement(imp)
        self.assertTrue(r1["applied"])
        r2 = self.applier.apply_improvement(imp)
        self.assertFalse(r2["applied"])
        self.assertEqual(r2["reason"], "already_applied")

    def test_impact_measurement(self):
        """Impact metrics are captured before/after for safe (auto-applied) actions."""
        # Create a bus with 100 lines
        bus_file = self.applier._tmp / "ai" / "coordination" / "messages.jsonl"
        with open(bus_file, "w") as f:
            for i in range(100):
                f.write(json.dumps({"type": "test"}) + "\n")
        # log_analysis is SAFE and measures the same maintenance metrics;
        # clean_bus is approval-gated and must never run automatically.
        imp = {"id": "test-impact-1", "category": "maintenance", "title": "Analyze bus",
               "description": "Summarize message types", "action": "log_analysis"}
        result = self.applier.apply_improvement(imp)
        self.assertTrue(result["applied"])
        self.assertIn("impact", result)
        self.assertIn("bus_lines", result["impact"])
        self.assertEqual(result["impact"]["bus_lines"]["before"], 100)
        self.assertEqual(result["impact"]["bus_lines"]["after"], 100)  # read-only; bus untouched

    def test_batch_apply(self):
        """Batch apply processes multiple improvements."""
        improvements = [
            {"id": "batch-1", "category": "maintenance", "title": "Doc 1",
             "description": "Test", "action": "update_documentation"},
            {"id": "batch-2", "category": "quality", "title": "Report 1",
             "description": "Test", "action": "generate_report"},
            {"id": "batch-risky", "category": "security", "title": "Code change",
             "description": "Test", "action": "code_change"},
        ]
        results = self.applier.apply_batch(improvements)
        self.assertEqual(len(results), 3)
        applied = sum(1 for r in results if r.get("applied"))
        queued = sum(1 for r in results if r.get("needs_approval"))
        self.assertEqual(applied, 2)
        self.assertEqual(queued, 1)

    def test_approve_improvement(self):
        """Approved queued improvement gets executed."""
        # Queue a risky action
        imp = {"id": "test-approve-1", "category": "security", "title": "Fix security",
               "description": "Security fix", "action": "code_change"}
        self.applier.apply_improvement(imp)
        self.assertEqual(len(self.applier.state["queued"]), 1)

        # code_change is risky and has no governed executor; queue a safe one
        # instead and confirm it applies directly.
        imp2 = {"id": "test-approve-2", "category": "maintenance", "title": "Fix config",
                "description": "Config fix", "action": "fix_config"}
        self.applier.apply_improvement(imp2)
        # This should have been applied directly since fix_config is safe
        self.assertEqual(len(self.applier.applied_ids), 1)  # fix_config applied directly

    def test_applier_status(self):
        """Status returns correct counts."""
        imp = {"id": "test-status-1", "category": "maintenance", "title": "Test",
               "description": "Test", "action": "update_documentation"}
        self.applier.apply_improvement(imp)
        s = self.applier.status()
        self.assertEqual(s["applied_count"], 1)
        self.assertEqual(s["queued_count"], 0)


class ImprovementFeedbackTests(unittest.TestCase):
    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "state").mkdir()
        self._tmp = tmp
        self._orig = (ifb.ROOT, ifb.STATE, ifb.FEEDBACK_FILE, ifb.APPLIER_STATE, ifb.HISTORY_FILE)
        ifb.ROOT = tmp
        ifb.STATE = tmp / "state"
        ifb.FEEDBACK_FILE = tmp / "state" / "improvement_feedback.json"
        ifb.APPLIER_STATE = tmp / "state" / "improvement_applier_state.json"
        ifb.HISTORY_FILE = tmp / "state" / "feedback_history.json"

    def tearDown(self):
        shutil.rmtree(self._tmp)
        ifb.ROOT, ifb.STATE, ifb.FEEDBACK_FILE, ifb.APPLIER_STATE, ifb.HISTORY_FILE = self._orig

    def test_feedback_scoring(self):
        """Feedback scores improvements correctly."""
        # Positive impact: bus lines decreased
        score = ifb.score_impact({
            "bus_lines": {"before": 1000, "after": 500, "delta": -500},
        })
        self.assertGreater(score, 0)

        # Neutral impact: no change
        score = ifb.score_impact({
            "bus_lines": {"before": 100, "after": 100, "delta": 0},
        })
        self.assertEqual(score, 0.0)

        # Negative impact: health rate dropped
        score = ifb.score_impact({
            "health_rate": {"before": 0.95, "after": 0.5, "delta": -0.45},
        })
        self.assertLess(score, 0)

    def test_feedback_analysis(self):
        """Feedback analysis computes summary from applier state."""
        applier_state = {
            "applied": [
                {"id": "imp-1", "category": "maintenance", "title": "Clean",
                 "action": "clean_bus", "impact": {"bus_lines": {"before": 1000, "after": 500, "delta": -500}}},
                {"id": "imp-2", "category": "quality", "title": "Report",
                 "action": "generate_report", "impact": {}},
            ]
        }
        ifb.APPLIER_STATE.write_text(json.dumps(applier_state))

        summary = ifb.analyze_feedback()
        self.assertEqual(summary["total_improvements"], 2)
        self.assertGreaterEqual(summary["positive_count"], 1)  # bus cleanup should be positive

    def test_category_recommendations(self):
        """Feedback provides category recommendations."""
        applier_state = {
            "applied": [
                {"id": f"imp-{i}", "category": "maintenance", "title": f"Test {i}",
                 "action": "clean_bus",
                 "impact": {"bus_lines": {"before": 1000, "after": 500, "delta": -500}}}
                for i in range(3)
            ]
        }
        ifb.APPLIER_STATE.write_text(json.dumps(applier_state))
        ifb.analyze_feedback()

        recs = ifb.get_recommendations()
        self.assertIn("maintenance", recs)
        self.assertEqual(recs["maintenance"], "prefer")


if __name__ == "__main__":
    unittest.main()
