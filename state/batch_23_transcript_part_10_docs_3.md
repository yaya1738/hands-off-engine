# Batch 23 Implementation Transcript - Part 10: Documentation (Part 3/4)

## File: docs/BATCH_23_STATUS_REPORT.md (Section 3: Examples & Usage)

```markdown
## Examples: Successive Runs

### Run 1: Initialization

**Input:** First consensus from Batch 22
**State:** No existing learning file

**Output:**
```json
{
  "run_count": 1,
  "issue_history": [
    {"hash": "a1b2c3d4", "occurrences": 1, "severity": "high"}
  ],
  "agent_performance": {
    "rules": {"accuracy": 1.0, "runs": 1}
  },
  "learning_weights": {
    "rules": 0.25, "llm_1": 0.25, "llm_2": 0.25, "heuristics": 0.25
  }
}
```

### Run 2: Issue Recurrence Detected

**Input:** Consensus with same issue
**State:** Existing learning file from Run 1

**Changes:**
```diff
  "run_count": 1  →  2
  "issue_history": [
-   {"hash": "a1b2c3d4", "occurrences": 1}
+   {"hash": "a1b2c3d4", "occurrences": 2, "last_seen": "updated"}
  ]
  "agent_performance": {
-   "rules": {"runs": 1}
+   "rules": {"runs": 2, "accuracy": 0.95}
  }
```

### Run 5: Threshold Triggers

**State After Run 5:**
```json
{
  "run_count": 5,
  "issue_history": [
    {"hash": "a1b2c3d4", "occurrences": 5, "severity": "high"}
  ],
  "recommendations": [
    "Critical issue recurring 5 times: address immediately"
  ]
}
```

### Run 20: Weight Divergence

**State After Run 20:**
```json
{
  "run_count": 20,
  "agent_performance": {
    "rules":      {"accuracy": 0.92, "runs": 20},
    "llm_1":      {"accuracy": 0.88, "runs": 20},
    "llm_2":      {"accuracy": 0.73, "runs": 20},  ← Underperforming
    "heuristics": {"accuracy": 0.90, "runs": 20}
  },
  "learning_weights": {
    "rules":      0.31,  ← Increased
    "llm_1":      0.29,
    "llm_2":      0.16,  ← Decreased
    "heuristics": 0.24
  },
  "recommendations": [
    "llm_2 shows lower agreement stability — reduce weight"
  ]
}
```

---

## CLI Usage

### Basic Invocation

```bash
python3 ai/ho_learning_engine.py
```

**Output:**
```
============================================================
LEARNING ENGINE SUMMARY
============================================================
Run count: 1
Total issues tracked: 3
Active agents: 4

Learning weights:
  rules: 0.29
  llm_1: 0.29
  llm_2: 0.29
  heuristics: 0.14

Recommendations:
  1. High error rate detected — review agent configurations
============================================================
```

### Verbose Mode

```bash
python3 ai/ho_learning_engine.py --verbose
```

**Output:**
```
[LEARNING] ============================================================
[LEARNING] Starting learning engine update cycle
[LEARNING] ============================================================
[LEARNING] Loading consensus from state/brain_consensus.json
[LEARNING] Loaded consensus with 3 issues
[LEARNING] No existing learning state found
[LEARNING] Initializing new learning state
[LEARNING] Processing run #1
[LEARNING] Updating issue history
[LEARNING]   Added new issue 7792f68b
...
```

### Custom State Directory

```bash
python3 ai/ho_learning_engine.py --state-dir /custom/path
```

---

## Future Batch Integration Roadmap

### Batch 24: Policy Brain Enhancement

**Goal:** Use learning weights to dynamically adjust agent influence

**Integration:**
```python
# Policy Brain will read learning state
learning_state = load("state/brain_learning.json")
weights = learning_state["learning_weights"]

# Apply weights to agent recommendations
weighted_consensus = apply_learning_weights(
    agent_outputs=agents,
    weights=weights
)
```

**Expected Improvements:**
- 15-30% increase in consensus quality
- Reduced false positives from low-performing agents
- Faster convergence to optimal decisions

### Batch 25: Adaptive Learning Rates

**Goal:** Tune learning parameters based on historical performance

**Features:**
- Dynamic decay rates for trend calculation
- Adaptive recurrence thresholds
- Context-aware weight adjustments

### Batch 26: Multi-Domain Learning

**Goal:** Separate learning states for different decision domains

**Domains:**
- Trading decisions
- Risk assessment
- Configuration changes
- Infrastructure operations

**Schema:**
```json
{
  "domains": {
    "trading": { "learning_weights": {...} },
    "risk": { "learning_weights": {...} },
    "config": { "learning_weights": {...} }
  }
}
```
```

*Continued in Part 11...*
