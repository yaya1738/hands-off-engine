# Chunk 04: Test Suite Implementation

## Test Suite Overview

**File:** `tests/integration/test_brain_orchestrator.py`
**Total Tests:** 16 (exceeded 12 minimum requirement)
**Framework:** Python unittest
**Execution Time:** ~170ms

### Test Class Structure

```python
class TestBrainOrchestrator(unittest.TestCase):
    """Test suite for Brain Orchestrator"""

    def setUp(self):
        """Create temporary directory for each test"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()
```

**Key Pattern:** Each test gets isolated temp directory, preventing cross-test contamination.

## Test Coverage

### Test 1: Happy Path - All Stages Succeed

```python
def test_happy_path_all_stages_ok(self):
    """Test 1: All stages succeed in happy path"""
    orchestrator = BrainOrchestrator(
        state_dir=self.state_dir,
        verbose=False
    )

    report = orchestrator.run_all()

    # Verify report structure
    self.assertIn("generated_at", report)
    self.assertIn("stages", report)
    self.assertIn("summary", report)

    # All 7 stages should be recorded
    self.assertEqual(len(report["stages"]), 7)

    # All should succeed
    self.assertEqual(report["summary"]["stages_ok"], 7)
    self.assertEqual(report["summary"]["stages_error"], 0)
    self.assertEqual(report["summary"]["overall_status"], "ok")
```

### Test 2: Missing Initial Brain Summary

```python
def test_missing_initial_brain_summary_file_handled(self):
    """Test 2: Handle failure when Stage 18 fails"""

    # Mock Stage 18 to fail
    def mock_brain_summary(state_dir):
        raise RuntimeError("Simulated brain summary failure")

    with patch("reports.ho_brain_report.write_brain_summary", mock_brain_summary):
        orchestrator = BrainOrchestrator(state_dir=self.state_dir, verbose=False)
        report = orchestrator.run_all()

        # Stage 1 should fail
        self.assertEqual(report["stages"][0]["status"], "error")

        # Subsequent stages should also fail (missing input)
        for i in range(1, 7):
            self.assertEqual(report["stages"][i]["status"], "error")

        # Overall status should be failed
        self.assertEqual(report["summary"]["overall_status"], "failed")
```

### Test 3: Policy Brain v2 Failure Isolated

```python
def test_policy_brain_v2_failure_recorded_but_orchestrator_completes(self):
    """Test 3: Stage 24 fails but orchestrator completes"""

    def mock_policy_v2(state_dir):
        raise FileNotFoundError("brain_learning.json not found")

    with patch("ai.ho_policy_brain_v2.generate_policy_v2", mock_policy_v2):
        orchestrator = BrainOrchestrator(state_dir=self.state_dir, verbose=False)
        report = orchestrator.run_all()
        orchestrator.write_reports(report)

        # Stages 1-6 should succeed
        for i in range(6):
            self.assertEqual(report["stages"][i]["status"], "ok")

        # Stage 7 should fail
        self.assertEqual(report["stages"][6]["status"], "error")

        # Reports should still be written
        self.assertTrue((self.state_dir / "brain_orchestrator_report.json").exists())
```

### Test 4: Both Reports Generated

```python
def test_orchestrator_writes_json_and_txt_reports(self):
    """Test 4: Both JSON and TXT reports are written"""
    orchestrator = BrainOrchestrator(state_dir=self.state_dir, verbose=False)
    report = orchestrator.run_all()
    orchestrator.write_reports(report)

    json_path = self.state_dir / "brain_orchestrator_report.json"
    txt_path = self.state_dir / "brain_orchestrator_report.txt"

    self.assertTrue(json_path.exists())
    self.assertTrue(txt_path.exists())

    # Verify JSON is valid
    with open(json_path) as f:
        loaded = json.load(f)
        self.assertEqual(loaded["summary"]["stages_total"], 7)
```

### Test 5: JSON Schema Validation

```python
def test_json_report_structure_valid(self):
    """Test 5: JSON report has all required fields"""
    orchestrator = BrainOrchestrator(state_dir=self.state_dir, verbose=False)
    report = orchestrator.run_all()

    # Top-level keys
    self.assertIn("generated_at", report)
    self.assertIn("completed_at", report)
    self.assertIn("stages", report)
    self.assertIn("summary", report)

    # Each stage has required fields
    for stage in report["stages"]:
        required_fields = [
            "name", "batch", "status", "duration_ms",
            "input_files", "output_files", "errors"
        ]
        for field in required_fields:
            self.assertIn(field, stage)

        # Validate types
        self.assertIsInstance(stage["name"], str)
        self.assertIsInstance(stage["batch"], int)
        self.assertIn(stage["status"], ["ok", "error", "skipped"])
```

### Test 6: Summary Counts Match

```python
def test_summary_counts_match_stage_statuses(self):
    """Test 6: Summary counts match actual stage statuses"""

    # Mock stages 2 and 5 to fail
    with patch("ai.ho_policy_agent.write_policy_recommendation",
               side_effect=RuntimeError("Forced")), \
         patch("ai.ho_consensus_engine.run_consensus",
               side_effect=RuntimeError("Forced")):

        orchestrator = BrainOrchestrator(state_dir=self.state_dir, verbose=False)
        report = orchestrator.run_all()

        # Count manually
        ok = sum(1 for s in report["stages"] if s["status"] == "ok")
        error = sum(1 for s in report["stages"] if s["status"] == "error")

        # Verify summary matches
        self.assertEqual(report["summary"]["stages_ok"], ok)
        self.assertEqual(report["summary"]["stages_error"], error)
```

### Test 7: CLI Invocation

```python
def test_cli_invocation_basic(self):
    """Test 7: CLI can be invoked and produces reports"""
    result = subprocess.run(
        [sys.executable, "ai/ho_brain_orchestrator.py",
         "--state-dir", str(self.state_dir)],
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True,
        text=True
    )

    self.assertEqual(result.returncode, 0)

    # Reports should exist
    self.assertTrue((self.state_dir / "brain_orchestrator_report.json").exists())
    self.assertTrue((self.state_dir / "brain_orchestrator_report.txt").exists())
```

### Additional Tests (8-16)

- **Test 8:** File operations isolated to temp state dir
- **Test 9:** Orchestrator handles empty state directory
- **Test 10:** Overall status "degraded" when some fail
- **Test 11:** Overall status "failed" when all fail
- **Test 12:** ISO-8601 timestamp validation
- **Test 13:** Verbose mode produces output
- **Test 14:** Stage duration recorded
- **Test 15:** Errors captured in failed stages
- **Test 16:** Batch numbers are correct (18-24)

## Test Execution Results

```
Ran 16 tests in 0.169s

OK
```

All tests passed successfully with:
- ✅ Zero failures
- ✅ Zero errors
- ✅ Fast execution (<200ms)
- ✅ 100% pass rate

---

**Next:** Chunk 05 - Documentation & Testing
