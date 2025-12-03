# Integration Roadmap: Wiring the Islands

**Status:** Active Implementation Plan  
**Date:** 2025-12-03  
**Purpose:** Connect all existing components into a functioning whole

---

## The Problem (Visualized)

**We have islands of capability without bridges between them.**

### Current State: 6 Disconnected Layers

1. **Hardware/Location**: 3 locations (local, GitHub, Termux) with no sync
2. **Code Components**: 4 engines built but not called
3. **Processes**: 5 running, 6 not running, no coordination
4. **Trading Pipeline**: Potential exists, always returns edge=0
5. **AI Systems**: 4 AI agents, no memory/coordination
6. **Cron/Automation**: 18 jobs scheduled, not coordinated

### The Numbers
- **690,322 lines written** → ~1% active
- **170+ branches** → 0 merged recently
- **87 "executed" trades** → 0 outcomes recorded
- **18 cron jobs** → 0 coordination

**Problem:** Everything exists. Nothing is connected.

---

## Integration Strategy: Build the Bridges

### Phase 1: Single Entry Point (Week 1)

**Goal:** One command that runs the complete pipeline

**Create:** `bin/run_integrated_pipeline.py`

```python
#!/usr/bin/env python3
"""
Integrated Pipeline Entry Point
Connects all components in correct order
"""

def run_pipeline():
    # 1. Fetch market data
    from fetchers import fetch_all_markets
    markets = fetch_all_markets()
    
    # 2. Calculate edge (connect wisdom engine)
    from alpha.wisdom_engine import calculate_edge
    edges = calculate_edge(markets)
    
    # 3. Calibrate probabilities (connect calibrator)
    from decider.probability_calibrator import calibrate
    calibrated = calibrate(edges)
    
    # 4. Make decisions (connect decider)
    from decider import make_decisions
    decisions = make_decisions(calibrated)
    
    # 5. Execute orders (connect executor)
    from executor.concrete_executor import execute_orders
    results = execute_orders(decisions)
    
    # 6. Record outcomes (connect recorder)
    from audit.outcome_recorder import record_outcomes
    record_outcomes(results)
    
    return results
```

**Actions:**
- [ ] Create unified entry point
- [ ] Wire all 6 components in sequence
- [ ] Add error handling at each step
- [ ] Log progress through pipeline

### Phase 2: Fix the Trading Pipeline (Week 1-2)

**Problem:** Edge always returns 0 → no trades executed

**Root Cause Analysis Needed:**
1. Check `alpha/wisdom_engine.py` - is edge calculation working?
2. Check market data - is it being fetched correctly?
3. Check thresholds - are they too high?

**Actions:**
- [ ] Audit edge calculation logic
- [ ] Add debug logging to see intermediate values
- [ ] Lower thresholds temporarily to verify flow
- [ ] Test with known-good market

### Phase 3: Process Coordination (Week 2)

**Problem:** 5 processes running, 6 not running, no coordination

**Solution:** Process registry + coordinator

**Create:** `state/process_registry.json`
```json
{
  "processes": {
    "backend_loop": {"status": "running", "pid": 1234, "purpose": "..."},
    "hardware_brain": {"status": "running", "pid": 1235, "purpose": "..."},
    "concrete_executor": {"status": "not_started", "reason": "not_integrated"}
  },
  "dependencies": {
    "concrete_executor": ["wisdom_engine", "probability_calibrator"]
  }
}
```

**Actions:**
- [ ] Create process registry
- [ ] Document what each process does
- [ ] Identify dependencies between processes
- [ ] Create process launcher that respects dependencies
- [ ] Add health checks for each process

### Phase 4: AI Memory & Continuity (Week 2-3)

**Problem:** 170+ sessions, 0 memory retained

**Solution:** Use existing memory kernels + session ordering

**Connect:**
- `ai_nexus/memory_kernels.py` (already exists)
- `ai_nexus/session_ordering.py` (already exists)
- `ai_nexus/cross_session_learning.py` (already exists)

**Actions:**
- [ ] Activate memory kernel system
- [ ] Store session outputs to kernels
- [ ] Load kernels at session start
- [ ] Test memory continuity across sessions

### Phase 5: Location Sync (Week 3)

**Problem:** 2 state directories, 0 synced

**Solution:** Designated primary + sync protocol

**Primary:** `/root/hands-off-engine/state/` (local server)
**Secondary:** GitHub repo `state/`
**Sync:** Termux mirrors primary

**Sync Protocol:**
```bash
# Every 15 minutes via cron
rsync -av /root/hands-off-engine/state/ github:repo/state/
# Commit and push changes
git -C /root/hands-off-engine add state/
git -C /root/hands-off-engine commit -m "State sync $(date)"
git -C /root/hands-off-engine push
```

**Actions:**
- [ ] Designate primary state location
- [ ] Set up automated sync to GitHub
- [ ] Configure Termux to pull from GitHub
- [ ] Add conflict resolution strategy

### Phase 6: Cron Coordination (Week 3-4)

**Problem:** 18 jobs scheduled, not coordinated

**Solution:** Cron orchestrator

**Create:** `bin/cron_orchestrator.py`
```python
# Manages all cron jobs with dependencies
# Ensures jobs don't conflict
# Provides centralized logging
```

**Actions:**
- [ ] List all 18 cron jobs with purposes
- [ ] Identify conflicts and dependencies
- [ ] Create execution order
- [ ] Replace individual cron jobs with orchestrator
- [ ] Add coordination logging

### Phase 7: Branch Consolidation (Week 4)

**Problem:** 170+ branches, 0 merged

**Solution:** Systematic merge plan

**Actions:**
- [ ] Categorize branches (feature/fix/experiment/dead)
- [ ] Identify valuable completed work
- [ ] Merge foundational branches first
- [ ] Archive or delete dead branches
- [ ] Update to main branch regularly

---

## Implementation Order

### Week 1: Get One Trade Through
```
Day 1-2: Create unified entry point
Day 3-4: Debug edge=0 issue
Day 5-7: Test complete pipeline end-to-end
Goal: Execute 1 real trade (DRYRUN) with outcome recorded
```

### Week 2: Connect Processes
```
Day 1-3: Process registry and dependencies
Day 4-5: Launch coordinator
Day 6-7: AI memory activation
Goal: All processes running and coordinated
```

### Week 3: Sync Locations
```
Day 1-3: State sync protocol
Day 4-5: Termux integration
Day 6-7: Cron orchestration
Goal: All locations in sync
```

### Week 4: Consolidate
```
Day 1-3: Branch merge plan
Day 4-5: Execute merges
Day 6-7: Verify integration complete
Goal: Clean main branch with integrated system
```

---

## Success Metrics

**Week 1 Success:**
- [ ] One command runs complete pipeline
- [ ] Edge != 0 for at least one market
- [ ] One trade executed (DRYRUN)
- [ ] One outcome recorded

**Week 2 Success:**
- [ ] All critical processes running
- [ ] Process health dashboard shows green
- [ ] AI sessions retain memory
- [ ] Session N can reference session N-1

**Week 3 Success:**
- [ ] State synced across all locations
- [ ] Cron jobs coordinated
- [ ] No conflicts or race conditions
- [ ] Centralized logging working

**Week 4 Success:**
- [ ] Main branch represents current system
- [ ] <20 active branches
- [ ] Documentation reflects reality
- [ ] New agent can onboard in <2 hours

---

## Critical Path: First Week Priority

**The Most Important Bridge:** Entry Point → Trading Pipeline

```
PRIORITY 1: Make edge calculation work
├─ Debug wisdom_engine.py
├─ Verify market data quality
├─ Test with known-good scenarios
└─ Document working thresholds

PRIORITY 2: Connect all 6 components
├─ Entry point calls wisdom_engine
├─ Wisdom_engine calls calibrator
├─ Calibrator calls decider
├─ Decider calls executor
├─ Executor calls recorder
└─ End-to-end test passes

PRIORITY 3: Record one outcome
├─ Execute one DRYRUN trade
├─ Record to outcome log
├─ Verify learning_engine can read it
└─ Prove the loop closes
```

**Once this works, everything else follows.**

---

## Concrete Next Actions

### Immediate (Today)
1. Create `bin/run_integrated_pipeline.py` skeleton
2. Wire up first 3 components (fetch → edge → calibrate)
3. Add extensive debug logging
4. Run and capture output

### This Week
1. Debug edge=0 issue
2. Complete all 6 component wirings
3. Execute first end-to-end test
4. Document working configuration

### Next Week
1. Implement process coordination
2. Activate AI memory system
3. Begin state sync setup

---

## The Fix Isn't More Code

**The fix is:**
1. One entry point that calls everything in order
2. Debug logging to see where it breaks
3. Fix each break systematically
4. Verify end-to-end flow
5. Repeat for each subsystem

**We don't need new components. We need to call the existing ones.**

---

## Tracking Progress

**Integration Dashboard:** `state/integration_status.json`

```json
{
  "last_updated": "2025-12-03T14:37:00Z",
  "bridges_built": {
    "entry_point": "in_progress",
    "edge_calculation": "blocked",
    "process_coordination": "not_started",
    "ai_memory": "not_started",
    "location_sync": "not_started",
    "cron_coordination": "not_started",
    "branch_consolidation": "not_started"
  },
  "pipeline_tests": {
    "fetch_data": "passing",
    "calculate_edge": "failing",
    "make_decision": "not_tested",
    "execute_order": "not_tested",
    "record_outcome": "not_tested",
    "end_to_end": "not_tested"
  },
  "success_criteria": {
    "one_trade_executed": false,
    "one_outcome_recorded": false,
    "processes_coordinated": false,
    "locations_synced": false,
    "memory_working": false
  }
}
```

---

## Summary

**The Islands:**
- Entry point ← → Components
- Running processes ← → Not running processes  
- Local state ← → GitHub state
- AI sessions ← → Memory persistence
- Cron jobs ← → Coordination
- Branches ← → Main

**The Bridges to Build:**
1. **Week 1:** Entry point + pipeline integration
2. **Week 2:** Process coordination + AI memory
3. **Week 3:** Location sync + cron orchestration
4. **Week 4:** Branch consolidation + verification

**Success:** Execute one trade end-to-end with outcome recorded and learned from.

**Then scale from there.**

---

*This is the integrafix: systematically building bridges between existing islands until they form a connected continent.*
