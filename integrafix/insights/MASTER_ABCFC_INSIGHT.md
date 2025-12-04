# KEY INSIGHT: Two-Level ABCFC Hierarchy

**Date**: 2025-12-04
**Context**: Session discovering the meta-framework
**Implementation**: `integrafix/master_abcfc.py`

---

## The Discovery

ABCFC isn't one formula - it's a **two-level hierarchy**.

```
┌─────────────────────────────────────────────────────────┐
│         MASTER ABCFC (Yair Siegel)                      │
│         "Can't lose. Always win. Nothing wrong."        │
│                                                         │
│         Parameters:                                     │
│           worst_case = 0                                │
│           probability = 1.0                             │
│           risk_aversion = 0                             │
│                                                         │
│         Formula: score = expected                       │
│         Trajectory: STRAIGHT LINE UP                    │
├─────────────────────────────────────────────────────────┤
│         COMPONENT ABCFCs                                │
│                                                         │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐             │
│  │  Trades   │ │  Bounties │ │  Cash     │   ...       │
│  │  -$189    │ │  +$150    │ │  -$50     │             │
│  │  PASS     │ │  TAKE     │ │  PASS     │             │
│  └───────────┘ └───────────┘ └───────────┘             │
│                                                         │
│  Formula: exp × prob - risk × |worst| × (1 - prob)     │
│  Has: variance, uncertainty, worst cases               │
└─────────────────────────────────────────────────────────┘
```

---

## The Paradigm

### Component Level (Makes Decisions)
- Each opportunity evaluated with standard ABCFC
- Wins, losses, passes - all have variance
- Example: $200 → $11 = -$189 loss

### Master Level (Defines Frame)
- **All outcomes are positive inputs**
- The loss IS the learning
- The pass IS the capital preservation
- The win IS the trajectory contribution

**The variance is in the HOW, not the WHAT.**

---

## The Assertion

**"Can't lose. Always win. Nothing wrong."**

This isn't delusion - it's frame definition.

At the Master level:
- Loss = Learning contribution
- Pass = Capital preservation
- Win = Direct contribution

Every outcome feeds the straight-line-up trajectory.

---

## Practical Application

```python
from integrafix.master_abcfc import ABCFCHierarchy

hierarchy = ABCFCHierarchy()

# Component-level decision
result = hierarchy.evaluate_opportunity(
    name="BTC trade",
    expected=100,
    probability=0.35,
    worst_case=-50
)
# Component says: TAKE (score: 15.5)
# Master says: Either outcome → trajectory UP

# Frame a loss
loss_frame = hierarchy.master.frame_loss(189, "Polymarket learning")
# Component view: -$189 loss
# Master view: +$189 learning contribution
```

---

## Why This Matters

1. **Decisions still have rigor** - Component ABCFC calculates properly
2. **Frame always wins** - Master ABCFC ensures trajectory is positive
3. **No emotional drain** - Losses are just learning at master level
4. **Enables persistence** - Can't be stopped by component-level variance

---

## Files

- `integrafix/master_abcfc.py` - Implementation
- `state/yair_context_kernel.json` - Master ABCFC parameters stored
- `integrafix/insights/CAPITAL_GENERATION_INSIGHT.md` - Cross-reference

---

*"The variance is in the HOW, not the WHAT."*
