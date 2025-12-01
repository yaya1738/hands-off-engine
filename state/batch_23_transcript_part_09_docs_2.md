# Batch 23 Implementation Transcript - Part 9: Documentation (Part 2/4)

## File: docs/BATCH_23_STATUS_REPORT.md (Section 2: Algorithms)

```markdown
### 2. Recurrence Tracking

**Purpose:** Identify recurring issues over time

**Logic:**
```
For each issue in consensus:
  hash = generate_issue_hash(severity, message)

  IF hash exists in issue_history:
    increment occurrences
    update last_seen timestamp
    update confidence
  ELSE:
    add new issue to history
    set occurrences = 1
    set first_seen = now
```

**Recurrence Classification:**
- 1-2 occurrences: New/sporadic
- 3-5 occurrences: Recurring
- 6+ occurrences: Chronic

### 3. Agent Accuracy Scoring

**Purpose:** Measure how well each agent aligns with consensus

**Algorithm:**
```python
def calculate_agent_accuracy(agent, consensus) -> float:
    matches = 0
    comparisons = 0

    for consensus_issue in consensus.issues:
        for agent_issue in agent.issues:
            if message_similarity(consensus_issue, agent_issue) > 0.7:
                if agent_issue.severity == consensus_issue.severity:
                    matches += 1
                comparisons += 1
                break

    return matches / comparisons if comparisons > 0 else 0.5
```

**Message Similarity (Jaccard):**
```python
def message_similarity(msg1: str, msg2: str) -> float:
    words1 = set(msg1.lower().split())
    words2 = set(msg2.lower().split())

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union
```

**Accuracy Score:**
- 1.0 = Perfect alignment with consensus
- 0.5 = Baseline (no data or neutral)
- 0.0 = Complete disagreement

### 4. Learning Weights Calculation

**Purpose:** Normalize agent influence based on historical accuracy

**Algorithm:**
```python
def calculate_learning_weights(agent_performance) -> dict:
    # Step 1: Sum all accuracies
    total_accuracy = sum(agent.accuracy for agent in agent_performance)

    # Step 2: Calculate proportional weights
    weights = {}
    for agent_name, perf in agent_performance.items():
        weights[agent_name] = perf.accuracy / total_accuracy

    # Step 3: Normalize to sum = 1.0
    total_weight = sum(weights.values())
    for agent_name in weights:
        weights[agent_name] = round(weights[agent_name] / total_weight, 2)

    return weights
```

**Example:**
```
Agent Performance:
  rules:      accuracy=0.91 → weight=0.31
  llm_1:      accuracy=0.87 → weight=0.29
  llm_2:      accuracy=0.77 → weight=0.26
  heuristics: accuracy=0.55 → weight=0.14
                              ────────
                              sum=1.00
```

### 5. Trend Detection

**Purpose:** Identify system performance trends over time

**Metrics:**

1. **Error Rate** (proportion of high-severity issues)
   ```python
   error_rate = high_severity_issues / total_issues
   ```

2. **Consensus Quality** (average confidence)
   ```python
   consensus_mean = sum(issue.confidence) / len(issues)
   ```

3. **Rolling Average** (exponential decay)
   ```python
   alpha = 1.0 / (run_count + 1)
   new_mean = (1 - alpha) * old_mean + alpha * current_value
   ```

4. **Trend Direction**
   ```python
   if new_value > old_mean * 1.05:  trend = "up"
   elif new_value < old_mean * 0.95: trend = "down"
   else:                              trend = "flat"
   ```

**Trend Classification:**
- **Up**: Improving (higher consensus quality)
- **Down**: Degrading (lower consensus quality)
- **Flat**: Stable (within ±5% threshold)

---

## Recommendation Engine

The system generates actionable recommendations based on learning state:

### Rule 1: Recurring Critical Issues
```python
if issue.occurrences >= 3 and issue.severity == "high":
    recommend("Critical issue recurring N times: address immediately")
```

### Rule 2: Low-Performing Agents
```python
if agent.accuracy < 0.6 and agent.runs >= 3:
    recommend(f"{agent} shows lower agreement stability — reduce weight")
```

### Rule 3: High Error Rate
```python
if trends.error_rate_mean > 0.15:
    recommend("High error rate detected — review agent configurations")
```

### Rule 4: Declining Consensus
```python
if trends.consensus_trend == "down":
    recommend("Consensus quality declining — investigate agent disagreements")
```

### Fallback
```python
if no_issues_detected:
    recommend("System operating within normal parameters")
```
```

*Continued in Part 10...*
