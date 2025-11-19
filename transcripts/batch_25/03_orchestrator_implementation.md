# Chunk 03: Orchestrator Implementation

## Core Architecture

**File:** `ai/ho_brain_orchestrator.py` (470 lines)

### BrainOrchestrator Class

Main class that manages the entire cognitive pipeline:

```python
class BrainOrchestrator:
    """
    Orchestrates the entire cognitive pipeline (Batches 18-24).
    """

    def __init__(self, state_dir: Path, verbose: bool = False):
        self.state_dir = Path(state_dir)
        self.verbose = verbose
        self.stages_results: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None
```

### Stage Execution Methods

Implemented 7 stage runner methods, one for each batch:

#### Pattern for Each Stage

```python
def run_stage_XX_name(self) -> Dict[str, Any]:
    """Run Batch XX: Name"""
    stage_name = "stage_name"
    batch = XX

    start_ms = int(time.time() * 1000)
    result = {
        "name": stage_name,
        "batch": batch,
        "status": "ok",
        "duration_ms": 0,
        "input_files": [...],
        "output_files": [],
        "errors": []
    }

    try:
        # Import and run the stage module
        from module import function
        output = function(self.state_dir)

        result["output_files"] = output.get("output_files", [])
        result["status"] = "ok"

    except FileNotFoundError as e:
        result["status"] = "error"
        result["errors"].append(f"Missing input file: {e}")

    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))
        if self.verbose:
            result["errors"].append(traceback.format_exc())

    result["duration_ms"] = int(time.time() * 1000) - start_ms
    return result
```

#### Key Design Elements

1. **Timing Capture**
   - Start time recorded before execution
   - Duration computed in milliseconds
   - Allows performance monitoring

2. **Error Handling Strategy**
   - Try-catch around every stage
   - FileNotFoundError handled separately (common case)
   - Generic Exception catches unexpected errors
   - Traceback included in verbose mode

3. **Status Recording**
   - Default to "ok"
   - Switch to "error" on exception
   - Include error messages for debugging

4. **No Cascading Failures**
   - Each stage runs independently
   - Exceptions caught and recorded
   - Orchestrator continues to next stage

### Main Orchestration Logic

```python
def run_all(self) -> Dict[str, Any]:
    """Run all stages in sequence."""

    self.start_time = datetime.utcnow()

    # Run all 7 stages
    self.stages_results = [
        self.run_stage_18_brain_summary(),
        self.run_stage_19_policy_agent(),
        self.run_stage_20_policy_executor(),
        self.run_stage_21_action_verifier(),
        self.run_stage_22_consensus_engine(),
        self.run_stage_23_learning_engine(),
        self.run_stage_24_policy_brain_v2(),
    ]

    self.end_time = datetime.utcnow()

    # Compute summary statistics
    stages_total = len(self.stages_results)
    stages_ok = sum(1 for s in self.stages_results if s["status"] == "ok")
    stages_error = sum(1 for s in self.stages_results if s["status"] == "error")
    stages_skipped = sum(1 for s in self.stages_results if s["status"] == "skipped")

    # Determine overall status
    if stages_error == 0:
        overall_status = "ok"
    elif stages_ok > 0:
        overall_status = "degraded"
    else:
        overall_status = "failed"

    # Collect failure notes
    notes = []
    for stage in self.stages_results:
        if stage["status"] == "error":
            notes.append(
                f"{stage['name']} (Batch {stage['batch']}) failed: "
                f"{stage['errors'][0] if stage['errors'] else 'unknown error'}"
            )

    return {
        "generated_at": self.start_time.isoformat() + "Z",
        "completed_at": self.end_time.isoformat() + "Z",
        "stages": self.stages_results,
        "summary": {
            "stages_total": stages_total,
            "stages_ok": stages_ok,
            "stages_error": stages_error,
            "stages_skipped": stages_skipped,
            "overall_status": overall_status,
            "notes": notes
        }
    }
```

### Report Generation

#### JSON Report

```python
def write_reports(self, report: Dict[str, Any]) -> None:
    """Write both JSON and TXT reports."""

    # Write JSON report
    json_path = self.state_dir / "brain_orchestrator_report.json"
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)
```

#### TXT Report

```python
    # Write TXT report
    txt_path = self.state_dir / "brain_orchestrator_report.txt"
    with open(txt_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("HANDS-OFF ENGINE - BRAIN ORCHESTRATOR (BATCH 25)\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Generated at: {report['generated_at']}\n")
        f.write(f"Completed at: {report['completed_at']}\n\n")

        f.write("Stages:\n")
        for i, stage in enumerate(report["stages"], 1):
            status_marker = (
                "[OK]" if stage["status"] == "ok"
                else "[ERR]" if stage["status"] == "error"
                else "[SKIP]"
            )
            f.write(f"  {i}. {status_marker:6} Batch {stage['batch']:2d} - {stage['name']}\n")

            if stage["errors"]:
                # Only write first line of error
                error_line = stage["errors"][0].split('\n')[0]
                f.write(f"       Reason: {error_line}\n")

        # ... summary section
```

### CLI Interface

```python
def main() -> int:
    """Main entry point for CLI."""

    parser = argparse.ArgumentParser(
        description="Brain Orchestrator - Run the complete cognitive pipeline"
    )

    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path("state"),
        help="Directory for state files (default: state)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging to stdout"
    )

    args = parser.parse_args()

    try:
        orchestrator = BrainOrchestrator(
            state_dir=args.state_dir,
            verbose=args.verbose
        )

        report = orchestrator.run_all()
        orchestrator.write_reports(report)

        return 0  # Success even if stages failed

    except Exception as e:
        print(f"CATASTROPHIC ERROR: {e}", file=sys.stderr)
        return 1  # Only for report generation failure
```

### Verbose Logging

```python
def log(self, message: str) -> None:
    """Log message if verbose mode is enabled."""
    if self.verbose:
        print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {message}")
```

Example output:
```
[12:34:56] ============================================================
[12:34:56] BRAIN ORCHESTRATOR - Starting cognitive pipeline
[12:34:56] ============================================================
[12:34:57] Starting Stage 1: brain_summary (Batch 18)
[12:34:58]   ✓ Completed: 2 files generated
```

### Import Path Handling

Critical fix for module imports when running as script:

```python
# Add parent directory to path for imports
_SCRIPT_DIR = Path(__file__).parent.parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
```

This allows the script to import `ai.*` and `reports.*` modules when run from any directory.

---

**Next:** Chunk 04 - Test Suite Implementation
