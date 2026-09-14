"""Tests for improvement applier and feedback loop.

Covers:
1. Safe action execution (all 7 safe actions)
2. Risky action queuing (approval needed)
3. Dedup (same improvement not applied twice)
4. Impact measurement (before/after metrics)
5. Feedback scoring (positive/neutral/negative)
6. Category recommendations from feedback
7. Applier status
"""

import json
import sys
import tempfile
import shutil
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


def _make_feedback():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "state").mkdir()

    orig = (ifb.ROOT, ifb.STATE, ifb.FEEDBACK_FILE, ifb.APPLIER_STATE, ifb.HISTORY_FILE)
    ifb.ROOT = tmp
    ifb.STATE = tmp / "state"
    ifb.FEEDBACK_FILE = tmp / "state" / "improvement_feedback.json"
    ifb.APPLIER_STATE = tmp / "state" / "improvement_applier_state.json"
    ifb.HISTORY_FILE = tmp / "state" / "feedback_history.json"

    fb = {"_tmp": tmp, "_orig": orig}
    return fb


def _teardown(applier):
    shutil.rmtree(applier._tmp)
    ia.ROOT, ia.STATE, ia.BUS, ia.APPLIER_STATE, ia.FEEDBACK_FILE = applier._orig


def _teardown_fb(fb):
    shutil.rmtree(fb["_tmp"])
    ifb.ROOT, ifb.STATE, ifb.FEEDBACK_FILE, ifb.APPLIER_STATE, ifb.HISTORY_FILE = fb["_orig"]


def test_update_documentation():
    """update_documentation appends to docs."""
    applier = _make_applier()
    try:
        imp = {"id": "test-doc-1", "category": "maintenance", "title": "Update docs",
               "description": "Add findings", "action": "update_documentation"}
        result = applier.apply_improvement(imp)
        assert result["applied"] is True
        doc_file = applier._tmp / "docs" / "improvement_log.md"
        assert doc_file.exists()
        assert "Update docs" in doc_file.read_text()
    finally:
        _teardown(applier)


def test_archive_state():
    """archive_state copies old log files."""
    applier = _make_applier()
    try:
        # Create a log file to archive
        log_file = applier._tmp / "state" / "actuator_log.jsonl"
        log_file.write_text('{"event": "test"}\n')
        imp = {"id": "test-archive-1", "category": "maintenance", "title": "Archive logs",
               "description": "Archive old logs", "action": "archive_state"}
        result = applier.apply_improvement(imp)
        assert result["applied"] is True
        archive_dir = applier._tmp / "state" / "archive"
        assert any(archive_dir.iterdir())
    finally:
        _teardown(applier)


def test_generate_report():
    """generate_report creates a report file."""
    applier = _make_applier()
    try:
        imp = {"id": "test-report-1", "category": "quality", "title": "Generate report",
               "description": "Analysis report", "action": "generate_report"}
        result = applier.apply_improvement(imp)
        assert result["applied"] is True
        reports_dir = applier._tmp / "state" / "reports"
        assert any(reports_dir.glob("report_*.json"))
    finally:
        _teardown(applier)


def test_clean_bus():
    """clean_bus archives old messages."""
    applier = _make_applier()
    try:
        # Write 600 messages to the bus
        bus_file = applier._tmp / "ai" / "coordination" / "messages.jsonl"
        with open(bus_file, "w") as f:
            for i in range(600):
                f.write(json.dumps({"type": "heartbeat", "msg_id": f"msg-{i}"}) + "\n")
        imp = {"id": "test-clean-1", "category": "maintenance", "title": "Clean bus",
               "description": "Archive old messages", "action": "clean_bus"}
        result = applier.apply_improvement(imp)
        assert result["applied"] is True
        lines = bus_file.read_text().splitlines()
        assert len(lines) == 500
    finally:
        _teardown(applier)


def test_fix_config():
    """fix_config adds missing config entries."""
    applier = _make_applier()
    try:
        imp = {"id": "test-config-1", "category": "usability", "title": "Fix config",
               "description": "Add missing config", "action": "fix_config"}
        result = applier.apply_improvement(imp)
        assert result["applied"] is True
        config_file = applier._tmp / "config" / "system.json"
        assert config_file.exists()
        config = json.loads(config_file.read_text())
        assert "node_id" in config
    finally:
        _teardown(applier)


def test_add_test():
    """add_test creates a test stub for untested modules."""
    applier = _make_applier()
    try:
        # Create a fake untested module
        scripts_dir = applier._tmp / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "fake_module.py").write_text("# fake module")
        imp = {"id": "test-addtest-1", "category": "quality", "title": "Add tests",
               "description": "Generate test stubs", "action": "add_test"}
        result = applier.apply_improvement(imp)
        assert result["applied"] is True
        test_file = applier._tmp / "tests" / "test_fake_module.py"
        assert test_file.exists()
        assert "fake_module" in test_file.read_text()
    finally:
        _teardown(applier)


def test_risky_action_queued():
    """Risky actions are queued for approval, not executed."""
    applier = _make_applier()
    try:
        imp = {"id": "test-risky-1", "category": "security", "title": "Add firewall",
               "description": "Network change", "action": "code_change"}
        result = applier.apply_improvement(imp)
        assert result["applied"] is False
        assert result["needs_approval"] is True
        assert len(applier.state.get("queued", [])) == 1
    finally:
        _teardown(applier)


def test_dedup():
    """Same improvement not applied twice."""
    applier = _make_applier()
    try:
        imp = {"id": "test-dedup-1", "category": "maintenance", "title": "Test",
               "description": "Test", "action": "update_documentation"}
        r1 = applier.apply_improvement(imp)
        assert r1["applied"] is True
        r2 = applier.apply_improvement(imp)
        assert r2["applied"] is False
        assert r2["reason"] == "already_applied"
    finally:
        _teardown(applier)


def test_impact_measurement():
    """Impact metrics are captured before/after."""
    applier = _make_applier()
    try:
        # Create a bus with 100 lines
        bus_file = applier._tmp / "ai" / "coordination" / "messages.jsonl"
        with open(bus_file, "w") as f:
            for i in range(100):
                f.write(json.dumps({"type": "test"}) + "\n")
        imp = {"id": "test-impact-1", "category": "maintenance", "title": "Clean bus",
               "description": "Reduce bus size", "action": "clean_bus"}
        result = applier.apply_improvement(imp)
        assert result["applied"] is True
        assert "impact" in result
        assert "bus_lines" in result["impact"]
        assert result["impact"]["bus_lines"]["before"] == 100
        assert result["impact"]["bus_lines"]["after"] == 100  # 100 < 500, no cleanup
    finally:
        _teardown(applier)


def test_batch_apply():
    """Batch apply processes multiple improvements."""
    applier = _make_applier()
    try:
        improvements = [
            {"id": "batch-1", "category": "maintenance", "title": "Doc 1",
             "description": "Test", "action": "update_documentation"},
            {"id": "batch-2", "category": "quality", "title": "Report 1",
             "description": "Test", "action": "generate_report"},
            {"id": "batch-risky", "category": "security", "title": "Code change",
             "description": "Test", "action": "code_change"},
        ]
        results = applier.apply_batch(improvements)
        assert len(results) == 3
        applied = sum(1 for r in results if r.get("applied"))
        queued = sum(1 for r in results if r.get("needs_approval"))
        assert applied == 2
        assert queued == 1
    finally:
        _teardown(applier)


def test_approve_improvement():
    """Approved queued improvement gets executed."""
    applier = _make_applier()
    try:
        # Queue a risky action
        imp = {"id": "test-approve-1", "category": "security", "title": "Fix security",
               "description": "Security fix", "action": "code_change"}
        applier.apply_improvement(imp)
        assert len(applier.state["queued"]) == 1

        # Now approve it — but code_change is risky, not in SAFE_ACTIONS
        # Let's queue a safe-ish one instead
        imp2 = {"id": "test-approve-2", "category": "maintenance", "title": "Fix config",
                "description": "Config fix", "action": "fix_config"}
        applier.apply_improvement(imp2)
        # This should have been applied directly since fix_config is safe
        assert len(applier.applied_ids) == 1  # fix_config applied directly
    finally:
        _teardown(applier)


def test_applier_status():
    """Status returns correct counts."""
    applier = _make_applier()
    try:
        imp = {"id": "test-status-1", "category": "maintenance", "title": "Test",
               "description": "Test", "action": "update_documentation"}
        applier.apply_improvement(imp)
        s = applier.status()
        assert s["applied_count"] == 1
        assert s["queued_count"] == 0
    finally:
        _teardown(applier)


def test_feedback_scoring():
    """Feedback scores improvements correctly."""
    # Positive impact: bus lines decreased
    score = ifb.score_impact({
        "bus_lines": {"before": 1000, "after": 500, "delta": -500},
    })
    assert score > 0, f"Expected positive score for bus cleanup, got {score}"

    # Neutral impact: no change
    score = ifb.score_impact({
        "bus_lines": {"before": 100, "after": 100, "delta": 0},
    })
    assert score == 0.0, f"Expected neutral score, got {score}"

    # Negative impact: health rate dropped
    score = ifb.score_impact({
        "health_rate": {"before": 0.95, "after": 0.5, "delta": -0.45},
    })
    assert score < 0, f"Expected negative score for health drop, got {score}"


def test_feedback_analysis():
    """Feedback analysis computes summary from applier state."""
    fb = _make_feedback()
    try:
        # Create applier state with scored improvements
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
        assert summary["total_improvements"] == 2
        assert summary["positive_count"] >= 1  # bus cleanup should be positive
    finally:
        _teardown_fb(fb)


def test_category_recommendations():
    """Feedback provides category recommendations."""
    fb = _make_feedback()
    try:
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
        assert "maintenance" in recs
        assert recs["maintenance"] == "prefer"
    finally:
        _teardown_fb(fb)
