# Batch 25 Status Report: Brain Orchestrator

**Status:** ✅ Complete
**Date:** 2025-11-19
**Author:** Hands-Off Engine Team

---

## 1. Executive Summary

Batch 25 implements the **Brain Orchestrator**, a safe, DRYRUN-only orchestration layer that runs the entire cognitive pipeline (Batches 18-24) end-to-end. This orchestrator:

- **Runs 7 cognitive stages sequentially** from Brain Summary through Policy Brain v2
- **Never crashes** - always produces a final report, even when stages fail
- **Provides dual outputs** - machine-readable JSON and human-readable TXT reports
- **Maintains safety** - DRYRUN mode only, no network calls, no real trades
- **Enables monitoring** - can be called from cron/systemd to track pipeline health

The orchestrator is the command center for observing the system's "thinking" process, making it easy to debug issues, track performance, and understand decision-making flow.

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      BRAIN ORCHESTRATOR                         │
│                        (Batch 25)                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ├─ Stage 1: Brain Summary (Batch 18)
                              │     Input:  [system state]
                              │     Output: state/hands_off_brain.json
                              │
                              ├─ Stage 2: Policy Agent v1 (Batch 19)
                              │     Input:  state/hands_off_brain.json
                              │     Output: state/brain_policy.json
                              │
                              ├─ Stage 3: Policy Executor (Batch 20)
                              │     Input:  state/brain_policy.json
                              │     Output: state/brain_actions.json
                              │
                              ├─ Stage 4: Action Verifier (Batch 21)
                              │     Input:  state/brain_actions.json
                              │     Output: state/brain_feedback.json
                              │
                              ├─ Stage 5: Consensus Engine (Batch 22)
                              │     Input:  state/brain_feedback.json
                              │     Output: state/brain_consensus.json
                              │
                              ├─ Stage 6: Learning Engine (Batch 23)
                              │     Input:  state/brain_consensus.json
                              │     Output: state/brain_learning.json
                              │
                              └─ Stage 7: Policy Brain v2 (Batch 24)
                                    Input:  state/brain_consensus.json
                                            state/brain_learning.json
                                    Output: state/brain_policy_v2.json

                              ↓

                    Final Orchestrator Outputs:
                    • state/brain_orchestrator_report.json
                    • state/brain_orchestrator_report.txt
```

---

## 3. JSON Contract

### Orchestrator Report Schema (`brain_orchestrator_report.json`)

```json
{
  "generated_at": "2025-11-19T12:34:56Z",
  "completed_at": "2025-11-19T12:35:12Z",
  "stages": [
    {
      "name": "brain_summary",
      "batch": 18,
      "status": "ok|error|skipped",
      "duration_ms": 123,
      "input_files": [],
      "output_files": ["state/hands_off_brain.json"],
      "errors": []
    }
    // ... 6 more stages
  ],
  "summary": {
    "stages_total": 7,
    "stages_ok": 6,
    "stages_error": 1,
    "stages_skipped": 0,
    "overall_status": "ok|degraded|failed",
    "notes": [
      "policy_brain_v2 (Batch 24) failed: Missing brain_learning.json"
    ]
  }
}
```

#### Field Descriptions

**Top-Level Fields:**
- `generated_at` (ISO-8601): Timestamp when orchestration started
- `completed_at` (ISO-8601): Timestamp when orchestration finished
- `stages` (array): Results from each cognitive stage
- `summary` (object): Aggregate statistics and overall status

**Stage Object:**
- `name` (string): Internal stage identifier
- `batch` (int): Batch number (18-24)
- `status` (enum): `"ok"`, `"error"`, or `"skipped"`
- `duration_ms` (int): Stage execution time in milliseconds
- `input_files` (array): Files this stage depends on
- `output_files` (array): Files this stage produced
- `errors` (array): Error messages if status is `"error"`

**Summary Object:**
- `stages_total` (int): Total number of stages (always 7)
- `stages_ok` (int): Count of successful stages
- `stages_error` (int): Count of failed stages
- `stages_skipped` (int): Count of skipped stages
- `overall_status` (enum):
  - `"ok"`: All stages succeeded
  - `"degraded"`: Some stages failed, but some succeeded
  - `"failed"`: All stages failed
- `notes` (array): Human-readable notes about failures

---

## 4. CLI Usage

### Basic Invocation

```bash
# Run with default settings (state/ directory)
python3 ai/ho_brain_orchestrator.py

# Run with verbose output
python3 ai/ho_brain_orchestrator.py --verbose

# Run with custom state directory
python3 ai/ho_brain_orchestrator.py --state-dir /tmp/brain_state

# Combine options
python3 ai/ho_brain_orchestrator.py --state-dir ./custom_state --verbose
```

### CLI Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--state-dir` | path | `state` | Directory for all state files |
| `--verbose` | flag | `false` | Enable verbose logging to stdout |

### Exit Codes

- **0**: Orchestrator ran successfully (report was generated)
  - Note: Individual stages may have failed, but the orchestrator completed
- **1**: Catastrophic error (could not generate report at all)

### Example Output (Verbose Mode)

```
[12:34:56] ============================================================
[12:34:56] BRAIN ORCHESTRATOR - Starting cognitive pipeline
[12:34:56] ============================================================
[12:34:57] Starting Stage 1: brain_summary (Batch 18)
[12:34:58]   ✓ Completed: 2 files generated
[12:34:58] Starting Stage 2: policy_agent_v1 (Batch 19)
[12:34:59]   ✓ Completed: 1 files generated
[12:34:59] Starting Stage 3: policy_executor (Batch 20)
[12:35:00]   ✓ Completed: 2 files generated
[12:35:00] Starting Stage 4: action_verifier (Batch 21)
[12:35:01]   ✓ Completed: 1 files generated
[12:35:01] Starting Stage 5: consensus_engine (Batch 22)
[12:35:02]   ✓ Completed: 1 files generated
[12:35:02] Starting Stage 6: learning_engine (Batch 23)
[12:35:03]   ✓ Completed: 1 files generated
[12:35:03] Starting Stage 7: policy_brain_v2 (Batch 24)
[12:35:04]   ✓ Completed: 1 files generated
[12:35:04] ============================================================
[12:35:04] Pipeline complete: OK
[12:35:04]   Total stages: 7
[12:35:04]   Successful:   7
[12:35:04]   Failed:       0
[12:35:04]   Skipped:      0
[12:35:04] ============================================================
```

---

## 5. Safety & Failure Modes

### DRYRUN Guarantees

The orchestrator and all cognitive stages operate in **DRYRUN mode only**:

✅ **Allowed:**
- Reading from `state/` directory
- Writing to `state/` directory
- Importing Python modules
- Local computation and analysis
- Logging to stdout

❌ **Never Allowed:**
- Network calls (HTTP, sockets, APIs)
- Placing real trades
- Modifying system state outside `state/`
- Executing external commands
- Writing to legacy runtime trees

### Failure Handling Philosophy

The orchestrator implements an **"always complete"** philosophy:

1. **Stage Failures Don't Cascade**
   - If Stage 3 fails, Stages 4-7 still attempt to run
   - They may fail due to missing inputs, but they get a chance

2. **Graceful Degradation**
   - Each stage failure is recorded with clear error messages
   - Overall status reflects the worst outcome: `ok` → `degraded` → `failed`

3. **Report Always Generated**
   - Even if all 7 stages fail, the orchestrator writes its report
   - Only exits with code 1 if it cannot write the report itself

4. **Error Context Preserved**
   - Error messages are captured in the JSON report
   - In verbose mode, full stack traces are included
   - Both help with debugging without crashing the system

### Common Failure Scenarios

| Scenario | Stage Behavior | Orchestrator Behavior |
|----------|----------------|----------------------|
| Missing input file | Stage marks `status: "error"` | Continues to next stage |
| Stage raises exception | Error captured in `errors` array | Continues to next stage |
| All stages fail | Each marked `"error"` | `overall_status: "failed"`, exit 0 |
| Cannot write report | N/A | Exit code 1 (only catastrophic case) |

---

## 6. Integration Notes

### Cron / Systemd Integration

The orchestrator is designed to be called periodically from cron or systemd timers:

**Example cron entry (every 5 minutes):**
```cron
*/5 * * * * cd /path/to/hands-off-engine && python3 ai/ho_brain_orchestrator.py --state-dir /var/lib/hands-off/state >> /var/log/hands-off/orchestrator.log 2>&1
```

**Example systemd timer:**
```ini
[Unit]
Description=Hands-Off Brain Orchestrator

[Service]
Type=oneshot
WorkingDirectory=/path/to/hands-off-engine
ExecStart=/usr/bin/python3 ai/ho_brain_orchestrator.py --state-dir /var/lib/hands-off/state
User=hands-off
Group=hands-off

[Install]
WantedBy=multi-user.target
```

### Dashboard Integration

A downstream dashboard or monitoring system should read:

1. **Latest orchestrator report**
   - `state/brain_orchestrator_report.json` for machine processing
   - `state/brain_orchestrator_report.txt` for human review

2. **Stage-specific outputs**
   - `state/brain_policy_v2.json` for latest policy recommendation
   - `state/brain_actions.json` for recent actions
   - `state/brain_learning.json` for agent performance metrics

3. **Key metrics to monitor**
   - `summary.overall_status`: Alert if `"degraded"` or `"failed"`
   - `summary.stages_error`: Track error rate over time
   - Stage `duration_ms`: Detect performance degradation
   - `summary.notes`: Extract failure reasons for alerting

### Supervisor Agent Integration

A future AI supervisor agent could:

1. **Monitor orchestrator health**
   - Parse `brain_orchestrator_report.json` after each run
   - Detect patterns in recurring failures
   - Escalate issues that persist across multiple runs

2. **Trigger remediation**
   - If Stage 18 fails repeatedly, check system state collectors
   - If Stage 24 fails, verify learning engine is updating
   - Restart failed components or adjust configuration

3. **Provide context to human operators**
   - Summarize trends: "Policy Brain v2 has failed 8/10 recent runs"
   - Suggest fixes: "Missing brain_learning.json - check Batch 23"
   - Generate detailed incident reports

---

## 7. Files Created

### Core Implementation
- `ai/ho_brain_orchestrator.py` - Main orchestrator module (460 lines)
- `ai/__init__.py` - Package initialization

### Supporting Modules (Batches 18-24 stubs)
- `reports/ho_brain_report.py` - Batch 18: Brain Summary
- `reports/__init__.py`
- `ai/ho_policy_agent.py` - Batch 19: Policy Agent v1
- `ai/ho_policy_executor.py` - Batch 20: Policy Executor
- `ai/ho_action_verifier.py` - Batch 21: Action Verifier
- `ai/ho_consensus_engine.py` - Batch 22: Consensus Engine
- `ai/ho_learning_engine.py` - Batch 23: Learning Engine
- `ai/ho_policy_brain_v2.py` - Batch 24: Policy Brain v2

### Tests
- `tests/integration/test_brain_orchestrator.py` - 16 comprehensive tests
- `tests/__init__.py`
- `tests/integration/__init__.py`

### Documentation
- `docs/BATCH_25_STATUS_REPORT.md` - This document

### Runtime Outputs
The orchestrator generates these files at runtime:
- `state/brain_orchestrator_report.json` - Machine-readable report
- `state/brain_orchestrator_report.txt` - Human-readable report

---

## 8. Test Coverage

### Test Suite Summary

**Total Tests:** 16
**All Passing:** ✅

| Test # | Name | Coverage |
|--------|------|----------|
| 1 | `test_happy_path_all_stages_ok` | All stages succeed |
| 2 | `test_missing_initial_brain_summary_file_handled` | Stage 18 failure propagation |
| 3 | `test_policy_brain_v2_failure_recorded_but_orchestrator_completes` | Single stage failure isolation |
| 4 | `test_orchestrator_writes_json_and_txt_reports` | Report generation |
| 5 | `test_json_report_structure_valid` | Schema validation |
| 6 | `test_summary_counts_match_stage_statuses` | Arithmetic correctness |
| 7 | `test_cli_invocation_basic` | Command-line interface |
| 8 | `test_file_operations_isolated_to_temp_state_dir` | File isolation |
| 9 | `test_orchestrator_handles_empty_state_dir` | Empty directory handling |
| 10 | `test_overall_status_degraded_when_some_failures` | Degraded status |
| 11 | `test_overall_status_failed_when_all_stages_fail` | Failed status |
| 12 | `test_generated_at_is_valid_iso_timestamp` | Timestamp validation |
| 13 | `test_verbose_mode_produces_output` | Logging behavior |
| 14 | `test_stage_duration_is_recorded` | Performance tracking |
| 15 | `test_errors_are_captured_in_failed_stages` | Error capture |
| 16 | `test_batch_numbers_are_correct` | Metadata correctness |

### Running Tests

```bash
# Run all tests
python3 -m pytest tests/integration/test_brain_orchestrator.py -v

# Or using unittest
python3 -m unittest tests/integration/test_brain_orchestrator.py

# Run specific test
python3 -m unittest tests.integration.test_brain_orchestrator.TestBrainOrchestrator.test_happy_path_all_stages_ok
```

---

## 9. Future Enhancements

### Potential Batch 26+ Additions

1. **Partial Stage Execution**
   - `--from-stage N` and `--to-stage M` CLI options
   - Useful for debugging specific pipeline segments

2. **Retry Logic**
   - Configurable retries for transient failures
   - Exponential backoff for network-dependent stages (when added)

3. **Parallel Stage Execution**
   - Some stages could run concurrently if dependencies allow
   - Would require DAG-based orchestration

4. **Historical Trend Analysis**
   - Track orchestrator runs over time
   - Detect degradation patterns
   - Generate weekly/monthly health reports

5. **Performance Budgets**
   - Alert if any stage exceeds duration threshold
   - Track 95th percentile execution times

6. **Stage Skipping Logic**
   - If brain_policy.json is recent enough, skip Stage 19
   - Configurable freshness thresholds

---

## 10. Lessons Learned

### Design Decisions

1. **"Always Complete" Philosophy**
   - Decision: Never crash, always produce a report
   - Rationale: In production, partial data is better than no data
   - Tradeoff: Requires careful error handling in every stage

2. **Dual Report Formats**
   - Decision: Both JSON (machines) and TXT (humans)
   - Rationale: Serves both automated monitoring and manual debugging
   - Tradeoff: Slightly more code, but huge UX improvement

3. **No Stage Skipping by Default**
   - Decision: Run all stages even if upstream fails
   - Rationale: Maximize information gathered per run
   - Tradeoff: Some stages will always fail after upstream failure

4. **Exit Code 0 on Stage Failures**
   - Decision: Only exit 1 on catastrophic orchestrator failure
   - Rationale: Cron/systemd should see success if report was generated
   - Tradeoff: Must read report to know true status

### Testing Insights

1. **Mock Granularity**
   - Fine-grained mocks (per-stage) enabled precise failure simulation
   - Allowed testing all failure modes without real file corruption

2. **Temp Directory Isolation**
   - Every test gets its own temp directory
   - Zero cross-test contamination
   - Makes tests parallelizable in the future

3. **Schema Validation Tests**
   - Explicit tests for JSON structure prevented regressions
   - Easier to evolve schema with confidence

---

## 11. Conclusion

Batch 25 delivers a **production-ready orchestration layer** for the Hands-Off Engine's cognitive pipeline. It provides:

- ✅ Safe, DRYRUN-only execution
- ✅ Robust error handling (never crashes)
- ✅ Clear, actionable reports (JSON + TXT)
- ✅ Comprehensive test coverage (16 tests)
- ✅ Easy integration with cron/systemd/dashboards

The orchestrator is the **control plane** for observing system cognition, making it trivial to:
- Run the full pipeline on demand
- Debug individual stage failures
- Monitor system health over time
- Feed data to downstream supervisors

**Next recommended batches:**
- **Batch 26**: Implement real cognitive logic in Batches 18-24 modules
- **Batch 27**: Build a web dashboard to visualize orchestrator reports
- **Batch 28**: Add AI supervisor agent for automated remediation

---

**End of Report**
