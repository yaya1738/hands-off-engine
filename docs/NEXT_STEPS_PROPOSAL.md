# Next Steps Proposal for Hands-Off Engine
_Date: 2025-11-20_
_Status: Draft for Review_

## Executive Summary

This document proposes a concrete path forward for the Hands-Off Engine based on:
- Current repository state (5 open draft PRs)
- Roadmap priorities from `HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`
- AI-driven development model

**Recommendation**: Focus on merging existing PRs in priority order, then tackle Tier 1 roadmap items to establish a trustworthy, production-ready foundation.

---

## Current State Analysis

### Open Pull Requests (All Draft)

1. **PR #10** (This PR): Proposal document
2. **PR #8**: Real alpha signals pipeline - MCP servers + Alpha→Decider
3. **PR #7**: Comprehensive audit logging + AI Nexus orchestration
4. **PR #3**: Branch documentation
5. **PR #2**: README updates with roadmap
6. **PR #1**: Claude editing capabilities demo

### Repository Status

- ✅ Core modules exist: `alpha/`, `decider/`, `executor/`, `state/`
- ✅ Termux integration present: `termux-hands-off/`
- ✅ Roadmap documented: `HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`
- ✅ AI policy established: `AI_POLICY.md`
- ⚠️ Multiple features in draft PRs, not yet integrated
- ⚠️ DRYRUN-only execution (no live trading)

---

## Proposed Action Plan

### Phase 1: Consolidate Existing Work (Week 1)

**Goal**: Merge completed PRs to establish clean baseline

#### Priority Order

1. **Merge PR #2 & #3** (Documentation)
   - Low risk, high value
   - Establishes clear branch strategy
   - No code changes, pure documentation
   - **Action**: Review and merge immediately

2. **Merge PR #7** (Audit Logging + AI Nexus)
   - **Critical infrastructure** for Tier 1 goal: "trustworthy system"
   - Provides audit trail for all decisions and actions
   - Enables AI Nexus orchestration and cost tracking
   - Self-financing capability through ROI tracking
   - **Action**: 
     - Review audit system integration points
     - Verify no conflicts with other PRs
     - Merge to `main`
     - **Estimated effort**: 1-2 days review + testing

3. **Merge PR #8** (Real Alpha Signals)
   - Implements end-to-end Alpha→Decider pipeline
   - Replaces mock data with real Polymarket signals
   - MCP server infrastructure for GitHub + Playwright
   - **Dependencies**: Should merge after audit logging
   - **Action**:
     - Ensure compatibility with audit system
     - Verify test coverage (4/4 tests passing noted)
     - Merge to `main`
     - **Estimated effort**: 2-3 days review + integration testing

4. **Close PR #1** (Claude demo)
   - Purpose fulfilled: demonstrated editing capability
   - Changes already represented in other PRs
   - **Action**: Close without merge, acknowledge demonstration value

5. **This PR (#10)**
   - Merge once proposal is approved and other PRs are merged
   - Update with final status before merge

---

### Phase 2: Tier 1 Priorities - Trustworthy System (Weeks 2-4)

From roadmap Section 4.1, focus on making the system trustworthy:

#### 2.1 Lock a Minimal, Safe Risk Model (Week 2)

**Goal**: Document and implement a simple, conservative risk formula

- [ ] Create `docs/RISK_MODEL_V1.md`
- [ ] Define risk parameters:
  - Bankroll caps (e.g., max 10% per position)
  - Per-market caps (e.g., max $100 per market)
  - Daily exposure limits (e.g., max $500 total risk per day)
  - Kelly fraction (e.g., 0.25x Kelly for safety)
- [ ] Implement in `decider/ho_decider.py`
- [ ] Add unit tests for risk calculations
- [ ] Integrate with audit logging

**Deliverable**: Production-ready risk model with clear documentation

#### 2.2 Define Simple Decider V1 (Week 2-3)

**Goal**: Clear decision logic for alpha signals → actions

- [ ] Document decision rules in `docs/DECIDER_V1.md`
- [ ] Implement 3-tier system:
  - No bet: edge < 3% or confidence < 70%
  - Small bet: 3% ≤ edge < 8%, confidence ≥ 70%
  - Medium bet: edge ≥ 8%, confidence ≥ 85%
- [ ] Output structured DRYRUN orders (JSON format)
- [ ] Add integration tests
- [ ] Ensure audit logging of all decisions

**Deliverable**: Documented, tested decision engine

#### 2.3 Harden Infrastructure Safety (Week 3-4)

**Goal**: Multiple safety layers for DRYRUN/LIVE modes

- [ ] Implement clear DRYRUN vs LIVE toggle
  - Environment variable: `HO_MODE=DRYRUN|LIVE`
  - Hard-coded default: `DRYRUN`
  - Require explicit confirmation for LIVE mode
- [ ] Add circuit breakers:
  - Maximum daily loss threshold
  - Maximum number of orders per day
  - Unusual pattern detection (e.g., too many orders in short time)
- [ ] Implement safety checks in executor
- [ ] Add comprehensive logging of all safety decisions
- [ ] Create safety dashboard or summary view

**Deliverable**: Production-ready safety infrastructure

#### 2.4 AI Intake Stability (Week 4)

**Goal**: Ensure `/plan` and other AI commands work reliably

- [ ] Verify end-to-end `/plan` workflow
- [ ] Add error handling and retry logic
- [ ] Implement structured logging for all AI operations
- [ ] Add monitoring for AI API failures
- [ ] Document AI command usage

**Deliverable**: Stable, reliable AI Intake system

---

### Phase 3: Tier 2 Priorities - Intelligence & Coverage (Weeks 5-8)

Only proceed once Tier 1 is complete and stable.

#### 3.1 Improve Alpha Quality

- Better feature engineering for Polymarket signals
- Integrate additional data sources (if available)
- Backtest alpha models against historical data
- Calibrate confidence scores

#### 3.2 Better State and Finance Reporting

- Enhance `/txt/finance` endpoint
- Add balance reconciliation across accounts
- Implement exposure tracking by market/category
- Create daily/weekly summary reports

#### 3.3 Extend AI Intake Commands

- Implement `/status`, `/risk`, `/alpha`, `/todo` commands
- Standardize command response format
- Add help documentation

---

### Phase 4: Tier 3 Priorities - Scaling (Future)

Only when Tier 1 & 2 are solid:

- MBOL / AI Nexus V1 (multi-LLM orchestration)
- Cost tracking and governance
- Scale to more markets and capital

---

## Decision Points

### Should we go LIVE with real trading?

**Recommendation**: NOT YET

**Reasoning**:
- Tier 1 safety infrastructure not complete
- Risk model needs formal documentation and review
- No circuit breakers implemented yet
- Audit system needs production validation

**Criteria for going LIVE**:
1. ✅ All Tier 1 items complete
2. ✅ At least 2 weeks of successful DRYRUN operation
3. ✅ Manual review of 100+ DRYRUN decisions shows no errors
4. ✅ Safety infrastructure tested and validated
5. ✅ Risk model peer-reviewed
6. ✅ Start with very small capital (e.g., $100-500 total)

---

## Success Metrics

### Phase 1 (Consolidation)
- ✅ All priority PRs merged or closed
- ✅ Clean `main` branch with integrated features
- ✅ No merge conflicts or broken tests

### Phase 2 (Tier 1)
- ✅ Risk model documented and implemented
- ✅ Decider V1 producing consistent outputs
- ✅ Safety infrastructure with circuit breakers
- ✅ AI Intake 100% reliable for 2 weeks
- ✅ Audit logs capture all critical events

### Phase 3 (Tier 2)
- ✅ Alpha model improvements show measurable edge increase
- ✅ Finance reporting accurate and easy to understand
- ✅ Extended AI commands working reliably

---

## Resource Requirements

### Development Time
- Phase 1: 1 week (PR reviews and merges)
- Phase 2: 3 weeks (Tier 1 implementation)
- Phase 3: 4 weeks (Tier 2 improvements)

### AI/LLM Costs
- Estimated $50-100/week for development assistance
- Audit logging tracks all AI costs
- AI Nexus enforces budget limits

### Testing
- Automated: Expand test coverage to 80%+
- Manual: Daily review of DRYRUN outputs
- Integration: Weekly end-to-end pipeline runs

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| PR conflicts during merge | Medium | Medium | Merge in priority order, test after each |
| Risk model too conservative | Low | High | Acceptable - start conservative, tune later |
| AI Intake instability | High | Low | Already mostly working, add monitoring |
| Insufficient test coverage | High | Medium | Add tests as part of each phase |
| Alpha model accuracy | Medium | Medium | Start with simple models, improve in Tier 2 |

---

## Recommendation

**Proceed with the following immediate actions:**

1. **This week**: Review and approve this proposal
2. **Next week**: Execute Phase 1 (merge PRs #2, #3, #7, #8)
3. **Weeks 2-4**: Execute Phase 2 (Tier 1 roadmap items)
4. **Week 5+**: Re-evaluate and proceed to Phase 3

**Key principle**: Move fast but prioritize trustworthiness over features. A conservative, reliable system is better than a sophisticated, risky one.

---

## Next Steps for Human Review

- [ ] Review this proposal document
- [ ] Approve or request changes to action plan
- [ ] Confirm PR merge priority order
- [ ] Set timeline expectations
- [ ] Approve proceeding with Phase 1

Once approved, AI agents can execute the plan with clear guidance and priorities.
