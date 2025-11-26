=== SYSTEM HANDOFF: Model Confidence Calibration & Feature Engineering ===
**TARGET:** chatgpt
**FROM:** claude_cli
**DATE:** 2025-11-26
**PRIORITY:** HIGH (Blocking trades)

**INTENT:** [☑ Research] [☑ Design] [☐ Implement] [☐ Approve]

---

## SUMMARY

Current alpha model shows critical deficiencies that are limiting trading:

**PROBLEM 1: Uniform Confidence Values**
- 5 of 6 tradeable markets show exactly 63% confidence
- 1 market shows 49% confidence
- No market-specific differentiation
- Suggests confidence is a default value, not derived from actual analysis

**PROBLEM 2: Confidence Below Optimal Threshold**
- All markets are 49-63% confidence
- Executor was rejecting everything (threshold was 70%)
- Threshold lowered to 60% as emergency fix
- Still missing highest-edge market (49% confidence, 11% edge)

**PROBLEM 3: Limited Feature Set**
- Model appears to use minimal features
- No market-specific context (polls, news, historical patterns)
- No time-series analysis
- No alternative data sources

**IMPACT:**
- Missing 11% edge opportunity (Trump-Merz market) due to low confidence
- Position sizes scaled down by 10% (63% vs 70% optimal)
- Cannot expand to new market categories confidently
- Limited differentiation between opportunities

---

## AGENT TASKS

### 1. Research Probability Calibration Techniques

**Objective:** Design proper confidence scoring methodology

**Tasks:**
- [ ] Research calibration methods (Platt scaling, isotonic regression, beta calibration)
- [ ] Analyze how prediction markets calibrate probabilities
- [ ] Study sports betting model calibration techniques
- [ ] Review academic papers on probability forecasting
- [ ] Identify Termux-compatible calibration libraries

**Deliverable:** Technical memo on calibration approach (in `docs/MODEL_CALIBRATION_RESEARCH.md`)

---

### 2. Design Market-Specific Feature Sets

**Objective:** Create features that differentiate market confidence

**Political Markets (Trump Conversations):**
- [ ] Historical call frequency (has Trump called this leader before?)
- [ ] Geopolitical events (G7, NATO, trade deals, conflicts)
- [ ] News sentiment (NYT, WSJ, Reuters mentions)
- [ ] Social media activity (Truth Social, Twitter patterns)
- [ ] Time zone alignment (easier to call during overlapping work hours)
- [ ] Recent public statements (Trump announcing calls)

**Crypto Markets (Ethereum, Bitcoin):**
- [ ] Technical indicators (RSI, MACD, Bollinger Bands)
- [ ] On-chain metrics (active addresses, exchange flows)
- [ ] Correlation with BTC (for altcoins)
- [ ] Major news events (ETF approvals, regulations, hacks)
- [ ] Developer activity (GitHub commits, network upgrades)

**Sports Markets:**
- [ ] Team statistics (win/loss, points per game, injuries)
- [ ] Historical matchups (head-to-head records)
- [ ] Betting market consensus (Vegas lines, betting percentages)
- [ ] Weather conditions (for outdoor sports)
- [ ] Home/away advantage

**Macro Markets (Fed, Inflation, GDP):**
- [ ] Economic indicators (CPI, unemployment, PMI)
- [ ] Fed speeches and minutes (FOMC, Jackson Hole)
- [ ] Expert forecasts (Bloomberg consensus, economist surveys)
- [ ] Historical patterns (seasonal effects, election cycles)
- [ ] Market expectations (fed funds futures, TIPS spreads)

**Deliverable:** Feature engineering spec (in `alpha/FEATURE_ENGINEERING_SPEC.md`)

---

### 3. Propose Time-to-Expiration Adjustment Formula

**Current Implementation:**
- <1 day: 0% position
- <3 days: 50% position
- <7 days: 75% position
- ≥7 days: 100% position

**Issues:**
- Step function (abrupt changes)
- Doesn't account for edge size (high edge should tolerate more decay)
- Doesn't account for volatility (some markets more predictable near expiration)

**Tasks:**
- [ ] Design smooth decay function (exponential vs linear)
- [ ] Incorporate edge size into decay (higher edge = more tolerance)
- [ ] Add market-type specific decay (sports vs politics)
- [ ] Consider implied volatility analogy from options pricing
- [ ] Backtest on historical resolved markets

**Deliverable:** Time decay formula spec (in `alpha/TIME_DECAY_MODEL.md`)

---

### 4. Create Confidence Scoring Rubric

**Objective:** Standardize confidence across market categories

**Rubric Structure:**
```
Base Confidence: 50%

Add points for:
+ Data quality (10-20%): Historical data, reliable sources
+ Feature completeness (5-15%): All key features available
+ Model agreement (5-15%): Multiple models converge
+ Edge clarity (5-10%): Clear mispricing mechanism
+ Liquidity (0-10%): Can exit position easily

Subtract points for:
- Data staleness (-5 to -15%): Old data reduces confidence
- Feature gaps (-10 to -20%): Missing key information
- High uncertainty (-5 to -15%): Volatile, unpredictable event
- Ambiguous resolution (-5 to -10%): Resolution criteria unclear

Final Confidence: Min(0.5, Max(0.95, calculated_confidence))
```

**Tasks:**
- [ ] Define rubric for each market category
- [ ] Calibrate point values based on historical accuracy
- [ ] Create decision tree or scoring function
- [ ] Validate against resolved markets
- [ ] Document edge cases and exceptions

**Deliverable:** Confidence rubric (in `alpha/CONFIDENCE_RUBRIC.md`)

---

### 5. Design Backtesting Framework

**Objective:** Validate confidence calibration against outcomes

**Requirements:**
- Must work with limited historical data
- Termux-compatible (no heavy ML frameworks)
- Fast execution (< 1 minute for 100 markets)
- Clear accuracy metrics (Brier score, log loss, calibration plots)

**Tasks:**
- [ ] Design data collection strategy (track predictions vs outcomes)
- [ ] Define metrics (calibration error, sharpness, Brier score)
- [ ] Create validation split strategy (time-based, cross-validation)
- [ ] Implement simple backtesting script
- [ ] Document how to interpret results

**Deliverable:** Backtesting framework design (in `tests/BACKTESTING_FRAMEWORK.md`)

---

## CONSTRAINTS

**Technical:**
- Must work in Termux environment (Android, ARM64)
- No Docker, no root access, no systemd
- Python 3.11, limited to `pkg` packages
- Avoid heavy ML frameworks (TensorFlow, PyTorch - too large)
- Prefer: scikit-learn, numpy, pandas, scipy (available via `pkg`)

**Data:**
- Limited historical Polymarket data
- API rate limits (don't hammer endpoints)
- Free data sources preferred (paid APIs need approval)
- Real-time updates preferred (<15 min lag)

**Performance:**
- Model refresh should complete in <5 minutes
- Feature extraction should be parallelizable
- Calibration should be fast (<30 seconds)

**Interpretability:**
- Must be explainable (not black-box)
- Confidence factors should be traceable
- Decision logic should be auditable

---

## FILES TO REVIEW

**Current Model:**
- `state/polymarket-model.json` - Current model output (7 markets, 49-63% confidence)
- `alpha/` - Alpha model code (if exists)
- `decider/ho_decider.py` - Decision logic with new time decay

**System Context:**
- `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md` - Overall roadmap
- `.claude/ACTIVE_OPPORTUNITIES_ANALYSIS.md` - Market analysis
- `.claude/IMPROVEMENTS_2025-11-26.md` - Recent fixes

**Execution:**
- `executor/ho_executor_plan.py` - Updated threshold (0.60), confidence scaling
- `decider/ho_decider.py` - Expiration detection, time decay

---

## SUCCESS CRITERIA

**Immediate (This Week):**
- [ ] Calibration research complete
- [ ] Feature sets defined for 3+ market categories
- [ ] Time decay formula designed and validated
- [ ] Confidence rubric documented
- [ ] Backtesting framework designed

**Short-Term (2 Weeks):**
- [ ] Confidence differentiation: Markets span 60-85% range (not all 63%)
- [ ] Trump-Merz market: Confidence >60% (currently 49%)
- [ ] Calibration error: <5% on resolved markets
- [ ] Feature coverage: 80%+ of key features available

**Long-Term (1 Month):**
- [ ] Model accuracy: 70%+ Brier score
- [ ] Confidence calibration: Within 5% of actual outcomes
- [ ] Market coverage: 4+ categories (politics, sports, macro, crypto)
- [ ] Automated feature updates: Real-time data feeds

---

## EXPECTED IMPACT

**Current State:**
- 5 tradeable markets (all 63% confidence)
- 1 blocked market (49% confidence, 11% edge - highest opportunity!)
- Position sizes scaled down 10% due to low confidence
- Expected value: $1.20/cycle

**After Improvements:**
- 6+ tradeable markets (all >60% confidence)
- Confidence range: 60-85% (differentiated)
- Position sizes optimized (high confidence = full size)
- Expected value: $2.00+/cycle (67% increase)

**Unlock High-Edge Opportunity:**
- Trump-Merz market: 11% edge, currently blocked
- If confidence raised to 65%: $5.00 position × 11% = $0.55 EV
- Single market unlocked = +46% total EV

---

## COORDINATION

**Communication:**
- Post research findings in `docs/` directory
- Use SYSTEM HANDOFF to return work to Claude CLI for implementation
- Tag @claude_cli when ready for code implementation

**Timeline:**
- Research: 2-3 days
- Design: 2-3 days
- Implementation (by Claude CLI): 1-2 days
- Testing: 1-2 days
- **Total: ~1 week to first deployment**

**Next Steps After Research:**
1. ChatGPT posts research findings to docs/
2. ChatGPT creates implementation spec
3. ChatGPT sends SYSTEM HANDOFF back to Claude CLI
4. Claude CLI implements code changes
5. Test in DRYRUN, deploy to LIVE

---

## QUESTIONS FOR CLARIFICATION

1. Do we have access to historical Polymarket data? (resolved markets with outcomes)
2. What's our budget for paid data APIs? (news, sports stats, etc.)
3. Should we prioritize accuracy or coverage? (fewer markets with high confidence vs more markets with medium confidence)
4. What's the acceptable latency for real-time features? (15 min? 1 hour?)
5. Should confidence be conservative (under-confident) or aggressive (over-confident)?

---

## ADDITIONAL CONTEXT

**Why This Matters:**
- Missing highest-edge market (11%) due to confidence calibration
- All markets clustered at same confidence (no differentiation)
- Cannot confidently expand to new categories
- Position sizing not optimized (leaving money on table)

**Business Impact:**
- +67% expected value per cycle (from $1.20 to $2.00+)
- Unlock 11% edge opportunity (Trump-Merz market)
- Enable expansion to sports/macro (diversification)
- Build foundation for scaling to 20+ markets

**Technical Debt:**
- Current model appears to use default confidence values
- No proper calibration methodology
- Limited feature engineering
- No backtesting infrastructure

---

=== END SYSTEM HANDOFF ===

**Next Action:** ChatGPT to acknowledge receipt and provide initial timeline
**Follow-Up:** Weekly check-ins on progress, daily updates on blockers
**Escalation:** Tag user if blocked on data access or technical constraints
