# Self-Monitoring & Self-Improvement System v1.0

Comprehensive autonomous improvement system for the CLM AI Nexus business intelligence platform.

## Overview

This document describes the integrated self-monitoring and self-improvement infrastructure added to address critical gaps in the system's ability to:

1. **Monitor itself** - Centralized health aggregation
2. **Detect anomalies** - Statistical pattern detection
3. **Learn automatically** - Auto-apply kernel updates
4. **Close feedback loops** - Metrics → learnings
5. **Persist learning** - Cross-session continuity
6. **Attribute performance** - Decision → outcome linking
7. **Maintain consistency** - Cross-kernel validation

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 SELF-IMPROVEMENT ORCHESTRATOR                    │
│              (ai_nexus/self_improvement_orchestrator.py)         │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌──────────────────┐
│ Self-Monitor  │   │    Anomaly      │   │   Feedback       │
│     Hub       │   │   Detection     │   │     Loop         │
└───────────────┘   └─────────────────┘   └──────────────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌──────────────────┐
│   Kernel      │   │  Performance    │   │  Cross-Session   │
│   Updater     │   │  Attribution    │   │    Learning      │
└───────────────┘   └─────────────────┘   └──────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MEMORY KERNELS (Part 2)                        │
│                    ai/memory/kernels/*.json                      │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Self-Monitoring Hub
**File:** `ai_nexus/self_monitoring_hub.py`

Centralized system health aggregator providing unified visibility into all components.

**Features:**
- Real-time system health aggregation
- Component status tracking (AI agents, kernels, infrastructure, pipelines)
- Health score computation (0-100%)
- Alert generation for degraded states
- Integration with existing monitoring systems

**CLI:**
```bash
# Get full system health status
python -m ai_nexus.self_monitoring_hub status

# Get health score
python -m ai_nexus.self_monitoring_hub health-score

# Check for anomalies
python -m ai_nexus.self_monitoring_hub anomalies
```

### 2. Anomaly Detection Engine
**File:** `ai_nexus/anomaly_detection.py`

Statistical anomaly detection using multiple methods.

**Methods:**
- Z-Score: Detect values outside N standard deviations
- IQR: Interquartile range for robust outlier detection
- Moving Average Deviation: Detect trend changes
- Baseline Drift: Detect gradual degradation

**CLI:**
```bash
# Detect anomalies
python -m ai_nexus.anomaly_detection detect

# Generate full report
python -m ai_nexus.anomaly_detection report

# Train baselines from historical data
python -m ai_nexus.anomaly_detection train-baseline
```

### 3. Automatic Kernel Update Applier
**File:** `ai_nexus/kernel_update_applier.py`

Automatically extracts and applies kernel updates from CPU session outputs.

**Features:**
- Parses CPU session threads to extract update suggestions
- Uses pattern matching to identify decisions, lessons, questions
- Validates updates before application
- Maintains audit trail

**CLI:**
```bash
# Extract updates from a session
python -m ai_nexus.kernel_update_applier extract --session-id <id>

# Apply updates
python -m ai_nexus.kernel_update_applier apply --session-id <id>

# Auto extract and apply
python -m ai_nexus.kernel_update_applier auto --session-id <id>
```

### 4. Feedback Loop Closure
**File:** `ai_nexus/feedback_loop.py`

Automatically generates kernel updates from performance metrics.

**Flow:**
1. Load performance metrics history
2. Identify significant trends (improvements/degradations)
3. Correlate with recent decisions
4. Generate lessons learned
5. Apply updates to relevant kernels

**CLI:**
```bash
# Analyze performance trends
python -m ai_nexus.feedback_loop analyze

# Generate kernel updates
python -m ai_nexus.feedback_loop generate

# Close the full loop
python -m ai_nexus.feedback_loop close
```

### 5. Cross-Session Learning
**File:** `ai_nexus/cross_session_learning.py`

Ensures learning persists and accumulates across CPU sessions.

**Features:**
- Automatic kernel context injection
- Cross-session decision synthesis
- Learning continuity tracking
- Session outcome correlation

**CLI:**
```bash
# Prepare context for a new session
python -m ai_nexus.cross_session_learning prepare --session-id <id>

# Record session outcome
python -m ai_nexus.cross_session_learning record --session-id <id> --outcome successful

# Synthesize learnings
python -m ai_nexus.cross_session_learning synthesize
```

### 6. Performance Attribution
**File:** `ai_nexus/performance_attribution.py`

Links decisions to their outcomes to understand effectiveness.

**Features:**
- Tracks decisions with expected outcomes
- Correlates with performance changes
- Identifies high/low impact decisions
- Generates effectiveness reports

**CLI:**
```bash
# Record a decision
python -m ai_nexus.performance_attribution record \
    --decision "Use Kelly fraction 0.15" \
    --expected "Reduce drawdown risk" \
    --kernel risk_model_v2

# Attribute outcomes
python -m ai_nexus.performance_attribution attribute

# Generate report
python -m ai_nexus.performance_attribution report
```

### 7. Kernel Consistency Validator
**File:** `ai_nexus/kernel_consistency.py`

Ensures kernels don't contain conflicting or outdated information.

**Checks:**
- Conflicting decisions across kernels
- Outdated content (>30 days)
- Duplicate content
- Orphaned references
- Topic overlaps

**CLI:**
```bash
# Validate all kernels
python -m ai_nexus.kernel_consistency validate

# Generate report
python -m ai_nexus.kernel_consistency report

# Check specific kernel health
python -m ai_nexus.kernel_consistency health --kernel risk_model_v2
```

### 8. Self-Improvement Orchestrator
**File:** `ai_nexus/self_improvement_orchestrator.py`

Master coordinator for all self-improvement systems.

**Phases:**
1. **Monitoring** - Check system health
2. **Anomaly Detection** - Identify unusual patterns
3. **Performance Analysis** - Analyze metrics trends
4. **Learning Extraction** - Extract from sessions
5. **Update Application** - Apply improvements
6. **Synthesis** - Consolidate learnings

**CLI:**
```bash
# Run single improvement cycle
python -m ai_nexus.self_improvement_orchestrator run

# Dry-run (no changes)
python -m ai_nexus.self_improvement_orchestrator run --dry-run

# Check status
python -m ai_nexus.self_improvement_orchestrator status

# Generate improvement report
python -m ai_nexus.self_improvement_orchestrator report

# Run as daemon (continuous improvement)
python -m ai_nexus.self_improvement_orchestrator daemon --interval 3600
```

## Gaps Addressed

| Gap | Solution | Component |
|-----|----------|-----------|
| No unified monitoring | Centralized health aggregation | Self-Monitoring Hub |
| No predictive detection | Statistical anomaly detection | Anomaly Detection |
| Kernel updates not auto-applied | Pattern extraction + auto-apply | Kernel Update Applier |
| Metrics not feeding back | Performance → kernel updates | Feedback Loop |
| Learning not persistent | Cross-session context | Cross-Session Learning |
| No decision attribution | Decision → outcome tracking | Performance Attribution |
| No kernel validation | Multi-kernel consistency checks | Kernel Consistency |
| No coordination | Master orchestrator | Self-Improvement Orchestrator |

## Quick Start

### Run a Full Improvement Cycle

```bash
# Run improvement cycle (dry-run first)
python -m ai_nexus.self_improvement_orchestrator run --dry-run

# If looks good, run for real
python -m ai_nexus.self_improvement_orchestrator run
```

### Start Continuous Improvement Daemon

```bash
# Run every hour
python -m ai_nexus.self_improvement_orchestrator daemon --interval 3600

# Run every 30 minutes, max 24 cycles
python -m ai_nexus.self_improvement_orchestrator daemon --interval 1800 --max-cycles 24
```

### Check System Health

```bash
python -m ai_nexus.self_monitoring_hub status
```

### Generate Reports

```bash
# System improvement report
python -m ai_nexus.self_improvement_orchestrator report --days 7

# Anomaly detection report
python -m ai_nexus.anomaly_detection report

# Kernel consistency report
python -m ai_nexus.kernel_consistency report

# Decision effectiveness report
python -m ai_nexus.performance_attribution report
```

## Data Flow

```
Performance Metrics ─────┐
     (state/performance_metrics.jsonl)
                         │
                         ▼
              ┌──────────────────┐
              │  Feedback Loop   │──── Generates Updates ────┐
              └──────────────────┘                           │
                                                             │
CPU Sessions ────────────┐                                   │
     (ai/intercom/*/thread.jsonl)                           │
                         │                                   │
                         ▼                                   │
              ┌──────────────────┐                           │
              │  Kernel Updater  │──── Extracts Updates ─────┤
              └──────────────────┘                           │
                                                             │
                                                             ▼
                                                    ┌────────────────┐
                                                    │ Memory Kernels │
                                                    │ (Part 2)       │
                                                    └────────────────┘
                                                             │
                                                             ▼
                                                    ┌────────────────┐
                                                    │ CPU Sessions   │
                                                    │ (Part 1)       │
                                                    └────────────────┘
```

## Configuration

### State Files Created

- `state/health_history.jsonl` - Health report history
- `state/anomaly_baselines.json` - Statistical baselines
- `state/detected_anomalies.jsonl` - Anomaly log
- `state/kernel_update_log.jsonl` - Update application log
- `state/feedback_loop_log.jsonl` - Feedback loop history
- `state/session_learnings.jsonl` - Session outcomes
- `state/session_contexts.jsonl` - Context preparation log
- `state/learning_synthesis.json` - Synthesized learnings
- `state/tracked_decisions.jsonl` - Decision tracking
- `state/improvement_cycles.jsonl` - Cycle history
- `state/orchestrator_config.json` - Orchestrator state

### Thresholds (Configurable)

| Component | Parameter | Default |
|-----------|-----------|---------|
| Anomaly Detection | ZSCORE_WARNING | 2.0 |
| Anomaly Detection | ZSCORE_CRITICAL | 3.0 |
| Feedback Loop | IMPROVEMENT_THRESHOLD | 15% |
| Feedback Loop | DEGRADATION_THRESHOLD | -15% |
| Kernel Consistency | STALENESS_THRESHOLD | 30 days |
| Orchestrator | CYCLE_INTERVAL | 3600s |

## Future Enhancements

1. **ML-Based Anomaly Detection** - Replace statistical methods with learned models
2. **Automatic Parameter Optimization** - Self-tune system parameters
3. **Natural Language Insights** - Generate human-readable improvement reports
4. **Predictive Maintenance** - Anticipate issues before they occur
5. **Multi-Objective Optimization** - Balance ROI, risk, and cost automatically

## Related Documents

- `docs/SPARK_PLUG_ARCHITECTURE_v0.2.md` - Core Spark Plug architecture
- `docs/TRI_AGENT_INTERCOM_v0.1.md` - Agent communication protocol
- `AI_POLICY.md` - AI governance policies
