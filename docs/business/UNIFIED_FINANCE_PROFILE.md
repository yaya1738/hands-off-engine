# Unified Finance & Business Profile

**Owner:** Yair Siegel (aka Froggy, aka Joseph Siegel)
**Last Updated:** 2025-11-27
**Document Version:** 1.0

---

## 1. Overview

This document serves as the **canonical reference** for all financial and business data in the Hands-Off Engine. It consolidates scattered financial information into a unified structure, providing a single source of truth for:

- Account balances and positions
- Credit card management
- Trading platforms (Polymarket, Robinhood)
- Payment processors (PayPal, Monzo)
- Risk parameters and guardrails

---

## 2. Financial Data Sources

### 2.1 Primary Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `external_accounts.json` | Consolidated account balances | `termux-hands-off/agents/` |
| `cards.json` | Credit card limits and balances | `termux-hands-off/agents/` |
| `balances_manual.yaml` | Manual balance inputs | `termux-hands-off/agent/` |
| `finance_sources.yaml` | Data source configuration | `termux-hands-off/agent/` |
| `finance_rules.json` | Alert thresholds and rules | `termux-hands-off/agents/` |
| `perf_inputs.json` | Performance tracking inputs | `termux-hands-off/agents/` |

### 2.2 State & Snapshot Files

| File/Directory | Purpose |
|----------------|---------|
| `termux-hands-off/data/finances/snapshots/` | Historical balance snapshots |
| `state/polymarket-model.json` | Polymarket model state |
| `state/performance_metrics.jsonl` | Performance metrics log |

---

## 3. Account Structure

### 3.1 Cash Accounts

| Account | Type | Purpose |
|---------|------|---------|
| PayPal Personal | Payment Processor | Personal transactions |
| PayPal Business | Payment Processor | Business transactions, cycling |
| Monzo | Debit/Banking | No-FX spending, Europe-friendly |
| Schwab | Checking/Brokerage | US banking, investment |
| Robinhood | Brokerage | Securities trading |

### 3.2 Trading Platforms

| Platform | Type | Primary Use |
|----------|------|-------------|
| Polymarket | Prediction Market | Event contracts trading |
| Robinhood | Stock/Options | Securities investment |
| OKX | Crypto Exchange | Crypto spot trading |
| Kraken | Crypto Exchange | Crypto spot trading |

### 3.3 Credit Accounts

| Card | Issuer | Features |
|------|--------|----------|
| Capital One | Capital One | Primary credit |
| PayPal Cashback | Synchrony | 3% at PayPal, 1.5% general |
| PayPal Credit | PayPal | PayPal financing |
| Avant | Avant | Building credit |

---

## 4. Financial Management Systems

### 4.1 Automated Scripts

| Script | Function | Schedule |
|--------|----------|----------|
| `finance_watcher.py` | Monitor balance changes | Continuous |
| `finance_bot.py` | Telegram finance bot | On-demand |
| `finance_alert.py` | Alert on threshold breaches | Event-driven |
| `finance_digest.py` | Generate daily summaries | Daily |
| `credit_utilization.py` | Track credit utilization | Periodic |
| `credit_guardrail.py` | Enforce spending limits | Continuous |
| `pnl_logger.py` | Log profit/loss | Per-trade |
| `pnl_delta.py` | Calculate PnL changes | Periodic |

### 4.2 Monitoring & Alerts

| Alert Type | Threshold | Action |
|------------|-----------|--------|
| Credit Utilization Warning | 45% | Heads-up notification |
| Credit Utilization Hard Stop | 50% | Pause card spending |
| Balance Anomaly | Configurable | Telegram notification |
| Position Change | Any change | Log + optional alert |

---

## 5. Risk Management

### 5.1 Credit Guardrails

```
ALERT_WARN = 45%   # Warning threshold
ALERT_HARD = 50%   # Hard stop threshold
MAX_PER_CARD = 50% # Per-card utilization limit
```

### 5.2 Trading Limits (DRYRUN Mode)

```
MAX_POSITION_SIZE = $100       # Per position
MAX_BANKROLL_PCT = 10%         # Max % of bankroll per bet
MIN_CONFIDENCE = 70%           # Confidence threshold
DEFAULT_MODE = DRYRUN          # Safety default
```

### 5.3 Cash Cycling Parameters

```
PP_BIZ_FEE = 3%           # PayPal Business merchant fee
PP_PAYPAL_REWARD = 3%     # Cashback on PayPal transactions
PP_GENERAL_REWARD = 1.5%  # General cashback rate
NET_COST_AT_PAYPAL = 0%   # Effective cost when cycling
NET_COST_GENERAL = 1.5%   # Effective cost general
```

---

## 6. Integration Points

### 6.1 Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
├─────────────────────────────────────────────────────────────────┤
│  Manual Inputs ─────┐                                           │
│  (balances_manual.yaml)                                         │
│                     │                                           │
│  On-chain Data ─────┼───▶  finance_sources.yaml                 │
│  (addresses_eth.yaml)     (aggregates all sources)              │
│                     │              │                            │
│  Exchange APIs ─────┘              ▼                            │
│  (OKX, Kraken)          ┌──────────────────┐                   │
│                         │ Fetcher Scripts   │                   │
│                         └────────┬─────────┘                   │
│                                  ▼                              │
├─────────────────────────────────────────────────────────────────┤
│                        STATE LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │external_accounts │  │   cards.json     │                    │
│  │     .json        │  │                  │                    │
│  └────────┬─────────┘  └────────┬─────────┘                    │
│           │                     │                               │
│           └──────────┬──────────┘                               │
│                      ▼                                          │
│           ┌──────────────────┐                                  │
│           │  Unified State   │                                  │
│           │   (this doc)     │                                  │
│           └────────┬─────────┘                                  │
│                    ▼                                            │
├─────────────────────────────────────────────────────────────────┤
│                     PROCESSING LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │ Credit Utils   │  │   PnL Logger   │  │  Guardrails    │   │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘   │
│          │                   │                   │              │
│          └───────────────────┼───────────────────┘              │
│                              ▼                                  │
│                    ┌──────────────────┐                        │
│                    │   Dashboard      │                        │
│                    │   (viewer)       │                        │
│                    └────────┬─────────┘                        │
│                             ▼                                   │
├─────────────────────────────────────────────────────────────────┤
│                      OUTPUT LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │   Telegram     │  │    Logs/       │  │   API Viewer   │   │
│  │   Alerts       │  │   Snapshots    │  │   (/finance/)  │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 API Endpoints

| Endpoint | Purpose | Auth Required |
|----------|---------|---------------|
| `/finance/networth` | Get total net worth | X-Admin-Token |
| `/metrics` | Prometheus-style metrics | X-Admin-Token |
| `/txt/finance` | Human-readable summary | Optional |

---

## 7. Business Operations

### 7.1 Revenue Streams

| Stream | Platform | Status |
|--------|----------|--------|
| Prediction Market Trading | Polymarket | DRYRUN (testing) |
| Securities Trading | Robinhood | Active |
| Crypto Trading | OKX/Kraken | Configured |

### 7.2 Cost Centers

| Cost | Type | Management |
|------|------|------------|
| AI API Costs | Operational | Tracked in ai_nexus/ledger.py |
| Credit Interest | Financial | Minimized via cycling |
| Transaction Fees | Operational | Optimized via routing |

---

## 8. Compliance & Safety

### 8.1 Safety Principles

1. **DRYRUN is default** - No live trading without explicit approval
2. **Conservative sizing** - Max 10% bankroll per position
3. **Gradual progression** - Prove system before real money
4. **Multiple validation layers** - Safety at every step

### 8.2 Audit Trail

All financial operations are logged to:
- `logs/finance_*.log` - Finance operation logs
- `logs/guardrail_actions.log` - Guardrail decisions
- `audit/` directory - Formal audit trail (JSONL format)

---

## 9. Quick Reference

### 9.1 Key Commands

```bash
# View current balances
hofinance.sh

# Check credit utilization
python3 ~/hands-off/agents/credit_utilization.py

# Run credit guardrail
python3 ~/hands-off/agents/credit_guardrail.py

# Update all accounts
bash ~/hands-off/agents/update_everything.sh

# View net worth via API
curl -H "X-Admin-Token: $TOKEN" http://localhost:8787/finance/networth
```

### 9.2 Related Documents

- [RISK_MODEL_V1.md](../RISK_MODEL_V1.md) - Detailed risk model
- [HANDS_OFF_RESEARCH_REPORT_2025-11-20.md](../../termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md) - System status & roadmap
- [USER_PROFILE.md](../../.claude/USER_PROFILE.md) - User directives
- [AI_POLICY.md](../../AI_POLICY.md) - AI operation policy

---

## 10. Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-27 | 1.0 | Initial unified profile created |

---

*This document is maintained as part of the Hands-Off Engine and should be updated when significant financial or business changes occur.*
