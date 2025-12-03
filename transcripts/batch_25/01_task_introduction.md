# Chunk 01: Task Introduction & Planning

## User Request

User provided a comprehensive prompt for implementing **Batch 25: Brain Orchestrator**, which would serve as an end-to-end cognitive pipeline runner for the Hands-Off Engine.

### High-Level Goal

Create a **single, safe, DRYRUN-only orchestrator** that runs the entire "brain pipeline" in order, using all the Batch 18–24 components, and produces a clear, machine-readable + human-readable report.

### Key Requirements

**The orchestrator should:**
- Run 7 cognitive stages sequentially (Batches 18-24)
- Never crash - always produce a final report
- Generate both JSON (machine-readable) and TXT (human-readable) reports
- Operate in DRYRUN mode only
- Handle failures gracefully without stopping the pipeline
- Provide CLI interface with options

**Safety Requirements (Non-Negotiable):**
- DRYRUN ONLY - no real trades, no LIVE mode toggles
- No Network Calls - no HTTP, requests, sockets
- File Isolation - confined to state/ directory
- Always-Complete Philosophy - generate report even if stages fail

### Existing Context

The prompt explained that Batches 18-24 already exist (conceptually) with these responsibilities:

1. **Batch 18 – Brain Summary** (`reports/ho_brain_report.py`)
   - Unify system state into single brain input file
   - Output: `state/hands_off_brain.json`

2. **Batch 19 – Policy Agent v1** (`ai/ho_policy_agent.py`)
   - Read brain summary, generate policy recommendations
   - Output: `state/brain_policy.json`

3. **Batch 20 – Policy Executor** (`ai/ho_policy_executor.py`)
   - Execute safe, DRYRUN actions based on policy
   - Output: `state/brain_actions.json`

4. **Batch 21 – Action Verifier** (`ai/ho_action_verifier.py`)
   - Analyze action successes/failures
   - Output: `state/brain_feedback.json`

5. **Batch 22 – Consensus Engine** (`ai/ho_consensus_engine.py`)
   - Run multiple agents, compute consensus
   - Output: `state/brain_consensus.json`

6. **Batch 23 – Learning Engine** (`ai/ho_learning_engine.py`)
   - Track issue recurrence, agent performance
   - Output: `state/brain_learning.json`

7. **Batch 24 – Policy Brain v2** (`ai/ho_policy_brain_v2.py`)
   - Learning-weighted policy recommendations
   - Output: `state/brain_policy_v2.json`

### Deliverables Required

1. **Orchestrator Module** (`ai/ho_brain_orchestrator.py`)
   - Single entrypoint running full chain
   - Generate `state/brain_orchestrator_report.json`
   - Generate `state/brain_orchestrator_report.txt`

2. **CLI Interface**
   - `--state-dir` option (default: state)
   - `--verbose` option for step-by-step logs
   - Exit code 0 if report generated (even with stage failures)
   - Exit code 1 only on catastrophic failure

3. **Test Suite** (`tests/integration/test_brain_orchestrator.py`)
   - Minimum 12 tests
   - Cover happy path, failures, CLI, schema validation
   - Use temp directories for isolation

4. **Documentation** (`docs/BATCH_25_STATUS_REPORT.md`)
   - Executive summary
   - Architecture diagram
   - JSON contract
   - CLI usage
   - Safety & failure modes
   - Integration notes

### JSON Report Structure

Expected schema for `brain_orchestrator_report.json`:

```json
{
  "generated_at": "2025-11-19T12:34:56Z",
  "stages": [
    {
      "name": "brain_summary",
      "batch": 18,
      "status": "ok|error|skipped",
      "duration_ms": 42,
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
    "notes": [...]
  }
}
```

## Assistant Response: Initial Planning

Created a comprehensive todo list to track implementation:

1. Review existing batch modules (18-24) to understand their APIs
2. Create directory structure (ai/, reports/, state/, docs/, tests/)
3. Implement stub modules for batches 18-24
4. Implement ai/ho_brain_orchestrator.py with orchestration logic
5. Implement tests/integration/test_brain_orchestrator.py with 12+ tests
6. Create docs/BATCH_25_STATUS_REPORT.md
7. Run test suite and verify all tests pass
8. Commit and push changes to the branch

## Initial Repository Exploration

Explored the repository structure:
- Found existing code in alpha/, executor/, termux-hands-off/
- Confirmed ai/, reports/, state/, docs/, tests/ directories don't exist yet
- Need to create entire batch system from scratch

**Decision:** Since the batch modules don't exist yet, will implement them as stubs that follow the expected API contracts, allowing the orchestrator to demonstrate the full pipeline flow.

---

**Next:** Chunk 02 - Environment Setup & Stub Implementation
