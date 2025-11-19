# Batch 23 Implementation Transcript - Part 1: Original Prompt

## USER PROMPT:

Understood — I'll take initiative now.

I will generate the Batch 23 prompt (Learning Integration Layer) exactly as it should be sent to Claude Web, fully aligned with:

Batch 17 → 21 pipeline

Batch 22 consensus engine

The repo structure

The Hands-Off architecture

The new feedback loop (Brain Feedback → Consensus → Learning → Policy Brain)

Safety, DRYRUN, determinism

Your preferred Claude-Web prompt style

Maximal autonomy for Claude to decide implementation details


And it will be ready for copy-paste without editing.

Here it is:


---

✅ Batch 23 — Learning Integration Layer (Claude Web Prompt)

You are now implementing Batch 23 of the Hands-Off Engine:
The Learning Integration Layer (Self-Improvement Loop v2).

This module consumes Batch 22 consensus output and produces a long-term learning state that improves the Policy Brain over time.


---

🎯 OBJECTIVE

Implement a safe, deterministic, DRYRUN-only learning module:

ai/ho_learning_engine.py

Its responsibilities:

1. Read

state/brain_consensus.json  (Batch 22 output)

Historical learning file (if exists):

state/brain_learning.json




2. Analyze

Track repeated issues across runs

Track agent agreement over time

Detect improvement / degradation trends

Score issues by recurrence

Maintain long-term agent performance metrics

Assign "learning weights" to each agent based on track record



3. Produce

Updated long-term learning state:

state/brain_learning.json

This becomes the persistence layer for the Policy Brain in future batches.



4. Provide CLI

python3 ai/ho_learning_engine.py --verbose


5. DRYRUN-only, no network, no actions, no effects outside state/.




---

🧠 LEARNING ENGINE REQUIREMENTS

1. Read Input Files

Strictly read:

brain_consensus.json

brain_learning.json (optional)



2. Maintain Long-Term Learning State

Stored in the output file:

state/brain_learning.json

Schema must contain:

{
  "generated_at": "...",
  "source": "state/brain_consensus.json",

  "run_count": 12,

  "issue_history": [
    {
      "hash": "<stable_issue_hash>",
      "first_seen": "...",
      "last_seen": "...",
      "occurrences": 4,
      "severity": "high",
      "confidence": 0.82
    }
  ],

  "agent_performance": {
    "rules": { "accuracy": 0.91, "runs": 12 },
    "llm_1": { "accuracy": 0.87, "runs": 12 },
    "llm_2": { "accuracy": 0.77, "runs": 12 },
    "heuristics": { "accuracy": 0.89, "runs": 12 }
  },

  "trend_metrics": {
    "error_rate_mean": 0.08,
    "error_rate_std": 0.02,
    "consensus_mean": 0.63,
    "consensus_trend": "up"
  },

  "learning_weights": {
    "rules": 0.31,
    "llm_1": 0.28,
    "llm_2": 0.16,
    "heuristics": 0.25
  },

  "recommendations": [
    "Critical issue recurring 3+ times: address immediately",
    "LLM_2 shows lower agreement stability — reduce weight"
  ]
}

Core behaviors:

Track every issue from consensus via stable hash

Increment occurrence counts

Update last_seen timestamps

Maintain rolling averages for:

Agreement score

Error rate

Stability


Compute agent learning weights based on:

Accuracy (agreement with overall consensus)

Stability contribution

Historical contradiction patterns




---

🔍 LEARNING ALGORITHMS (Minimum Required)

1. Issue Hashing

Generate a stable hash for each issue:

sha256(severity + message)

2. Recurrence Tracking

If seen before → increment
If new → add to history

3. Agent Accuracy

Agent is "accurate" on a run if:

Its severity ranking aligns with consensus

Its top recommendations overlap consensus


4. Learning Weights

Normalized by:

weight = accuracy * stability_score

5. Trend Detection

Use simple rolling averages across past N runs:

consensus_mean

error_rate_mean

consensus_trend (up/down/flat)
