# AI Cost and Usage Analysis - Hands-Off Engine

_Version: 1.0 | Created: 2025-11-27_

## Executive Summary

This document analyzes all AI APIs, costs, and third-party usage limits for the Hands-Off Engine's multi-AI orchestration system. The system uses three primary AI providers: OpenAI (ChatGPT), Anthropic (Claude), and GitHub Copilot Agent.

### Key Findings

| Provider | Monthly Cost Estimate | Rate Limits | Usage Concern |
|----------|----------------------|-------------|---------------|
| OpenAI | $5-50/month (typical) | Tier-based (20-1000+ RPM) | Low - affordable at current scale |
| Anthropic | $5-50/month (typical) | Tier-based (5-1000+ RPM) | Low - affordable at current scale |
| GitHub Copilot | $0-39/month (subscription) | Premium request quotas | Medium - monthly limits enforced |

---

## 1. Current AI Infrastructure

### 1.1 AI APIs in Use

Based on repository analysis, the Hands-Off Engine uses the following AI providers:

#### OpenAI (ChatGPT)
- **File**: `ai_nexus/provider_openai.py`
- **Model**: `gpt-4-turbo-preview` (default), `gpt-4o-mini` (AI Intake)
- **Usage**: Research, analysis, strategic thinking, AI Intake `/plan` command
- **Authentication**: `OPENAI_API_KEY` environment variable

#### Anthropic (Claude)
- **File**: `ai_nexus/provider_claude.py`
- **Model**: `claude-3-5-sonnet-20241022` (default)
- **Usage**: Implementation, code analysis, practical solutions
- **Authentication**: `ANTHROPIC_API_KEY` environment variable

#### GitHub Copilot Agent
- **File**: `ai_nexus/provider_copilot.py`
- **Status**: Stub implementation in v0.1
- **Usage**: GitHub-native features, PRs, issues
- **Authentication**: Via GitHub subscription (indirect)

### 1.2 Internal Budget Management

The AI Nexus system (`ai_nexus/nexus.py`) provides built-in budget management:

```python
budget_limits = {
    "copilot": 100.0,   # $100/day
    "chatgpt": 50.0,    # $50/day
    "claude": 50.0,     # $50/day
    "openai": 50.0,     # $50/day
}
```

**Current Daily Budget Total**: $250/day maximum (configured, not actual spend)

---

## 2. AI Provider Pricing Details

### 2.1 OpenAI API Pricing (2025)

#### GPT-4o (Recommended for production)
| Type | Price per 1M tokens |
|------|---------------------|
| Input | $5.00 |
| Output | $15.00 |
| **Batch API** (50% discount) | $2.50 input / $7.50 output |

#### GPT-4o Mini (Currently used by AI Intake)
| Type | Price per 1M tokens |
|------|---------------------|
| Input | $0.15 |
| Output | $0.60 |

#### GPT-4 Turbo
| Type | Price per 1M tokens |
|------|---------------------|
| Input | $10.00 |
| Output | $30.00 |

**Token Estimate**: ~750 words ≈ 1,000 tokens

**Cost Example (AI Intake /plan command)**:
- Typical prompt: ~2,000-3,000 tokens (includes policy + report)
- Typical response: ~500-1,000 tokens
- Cost per invocation: ~$0.001-0.003 using GPT-4o Mini

### 2.2 Anthropic Claude Pricing (2025)

#### Claude 3.5 Sonnet (Currently used)
| Type | Price per 1M tokens |
|------|---------------------|
| Input | $3.00 |
| Output | $15.00 |

#### Claude 3 Haiku (Budget option)
| Type | Price per 1M tokens |
|------|---------------------|
| Input | $0.25-1.00 |
| Output | $1.25-5.00 |

#### Claude Opus 4.5 (Premium)
| Type | Price per 1M tokens |
|------|---------------------|
| Input | $5.00 |
| Output | $25.00 |

**Cost Example (Tri-Agent Session)**:
- Per agent message: ~1,000-2,000 tokens
- 2 agents × 2 rounds = 4 messages
- Estimated cost: $0.01-0.05 per session

### 2.3 GitHub Copilot Pricing (2025)

| Plan | Monthly Cost | Premium Requests/Month |
|------|--------------|------------------------|
| Free | $0 | 50 |
| Pro | $20 | 300 |
| Pro+ | $39 | 1,500 |
| Business | $19/user | 300/user |
| Enterprise | $39/user | 1,000/user |

**Additional premium requests**: $0.04/request

**Premium Model Multipliers**:
- GPT-4.5: 50× (1 request = 50 premium requests)
- Claude Opus: 10×
- Claude Sonnet 3.5/3.7: 1×
- Gemini 2.0 Flash: 0.25×

---

## 3. Rate Limits and Quotas

### 3.1 OpenAI Rate Limits

| Tier | RPM (requests/min) | TPM (tokens/min) | Access Requirements |
|------|--------------------|--------------------|---------------------|
| Free/Tier 1 | 20-60 | 15,000-30,000 | New accounts |
| Tier 2-3 | 100-500 | 50,000-100,000 | $50-100 spend |
| Tier 4-5 | 1,000+ | 100,000-500,000+ | $250+ spend |
| Enterprise | Custom | Custom | Contract required |

**HTTP 429 Handling**: Implement exponential backoff for rate limit errors.

### 3.2 Anthropic Claude Rate Limits

| Tier | RPM (requests/min) | TPM (tokens/min) | TPD (tokens/day) |
|------|--------------------|--------------------|------------------|
| Free | 5 | 20,000 | 300,000 |
| Build (Pay-as-you-go) | 50 | 40,000 | Custom |
| Scale | 1,000+ | 400,000+ | Enterprise |

**Token Bucket Algorithm**: Capacity refills continuously rather than resetting at fixed intervals.

### 3.3 GitHub Copilot Rate Limits

| Feature | Rate Limit |
|---------|------------|
| Code completions | Service-level rate limits |
| Premium requests | Monthly quotas by plan |
| Agent mode | Consumes premium requests |
| Code review | Consumes premium requests |

**Quota Reset**: 1st of each month at UTC midnight.

---

## 4. Third-Party Usage Restrictions

### 4.1 OpenAI Terms

**Allowed**:
- Automated systems with proper rate limit handling
- Building products on top of API
- Multi-agent orchestration

**Restrictions**:
- No credential sharing across organizations
- Must handle rate limits gracefully
- Cannot resell raw API access

### 4.2 Anthropic Terms

**Allowed**:
- Automated systems with proper rate limiting
- Multi-agent systems
- Production use with paid tier

**Restrictions**:
- Organization-level rate limits apply
- Cannot bypass rate limits
- Must comply with usage policies

### 4.3 GitHub Copilot Terms

**Allowed**:
- Personal and team automation
- Integration with CI/CD workflows
- Issue/PR automation

**Restrictions**:
- Premium request quotas enforced
- Third-party API access limited
- Subscription required for sustained use

---

## 5. Cost Projections for Hands-Off Engine

### 5.1 Current Usage Patterns

| Component | Frequency | Est. Cost/Invocation | Monthly Cost |
|-----------|-----------|----------------------|--------------|
| AI Intake `/plan` | 10-50/month | $0.001-0.003 | $0.01-0.15 |
| Tri-Agent Sessions | 5-20/month | $0.01-0.05 | $0.05-1.00 |
| Claude CLI Implementation | 50-200/month | $0.01-0.05 | $0.50-10.00 |
| GitHub Copilot Agent | Included | $0-39 subscription | $0-39 |

**Estimated Total Monthly Cost**: $1-50 (typical usage)

### 5.2 Scaling Scenarios

| Scenario | Description | Estimated Monthly Cost |
|----------|-------------|------------------------|
| Minimal | 10 AI interactions/month | $1-5 |
| Moderate | 50 AI interactions/month | $5-25 |
| Active | 200 AI interactions/month | $25-100 |
| Heavy | 500+ AI interactions/month | $100-500 |

### 5.3 Self-Financing Threshold

Based on the AI Nexus ledger system, the engine tracks:
- AI operation costs
- Trading profits attributed to AI decisions
- ROI calculation for self-financing

**Break-even target**: AI costs < trading profits
**Current approach**: DRYRUN mode, so no real profits yet

---

## 6. Recommendations

### 6.1 Cost Optimization

1. **Use GPT-4o Mini for routine tasks** (AI Intake)
   - Current: ✅ Already using GPT-4o Mini
   - Savings: 10-50× cheaper than GPT-4 Turbo

2. **Use Claude Haiku for simple tasks**
   - Consider for: Quick analysis, validation checks
   - Savings: 3-12× cheaper than Claude Sonnet

3. **Implement Batch API for non-urgent tasks**
   - Applicable to: Bulk analysis, overnight processing
   - Savings: 50% cost reduction

4. **Use prompt caching**
   - Anthropic supports: 90% discount on cached prompts
   - Applicable to: Repeated context (AI Policy, Research Report)

### 6.2 Rate Limit Management

1. **Implement exponential backoff**
   - Current: Not implemented
   - Recommendation: Add retry logic with backoff

2. **Queue non-urgent requests**
   - Use: `ai/cpu_inbox/` queue for burst management
   - Benefit: Avoid hitting rate limits

3. **Monitor usage tiers**
   - OpenAI: Auto-upgrades with spend
   - Anthropic: Request tier upgrade if needed

### 6.3 Budget Enforcement

1. **Reduce default daily budgets**
   ```python
   # Current (generous)
   budget_limits = {
       "copilot": 100.0,
       "chatgpt": 50.0,
       "claude": 50.0,
       "openai": 50.0,
   }
   
   # Recommended (conservative)
   budget_limits = {
       "copilot": 10.0,   # $10/day
       "chatgpt": 5.0,    # $5/day
       "claude": 5.0,     # $5/day
       "openai": 5.0,     # $5/day
   }
   ```

2. **Add weekly budget caps**
   - Prevent runaway costs
   - Implement in `ai_nexus/nexus.py`

3. **Enable budget alerts**
   - Telegram notification at 80% budget
   - Auto-stop at 100% budget

### 6.4 GitHub Copilot Strategy

1. **Monitor premium request usage**
   - Current: No tracking
   - Recommendation: Add monitoring

2. **Consider Pro+ if heavy usage**
   - If >300 requests/month needed
   - $39/month for 1,500 requests

3. **Use standard models when possible**
   - Avoid 50× multiplier models (GPT-4.5)
   - Prefer 1× models (Claude Sonnet)

---

## 7. Implementation Status

### 7.1 Current Implementation

| Feature | Status | Location |
|---------|--------|----------|
| Budget tracking | ✅ Implemented | `ai_nexus/nexus.py` |
| Cost per task | ✅ Implemented | `ai_nexus/ledger.py` |
| Daily summaries | ✅ Implemented | `ActionLedger.get_daily_summary()` |
| ROI calculation | ✅ Implemented | `ActionLedger.calculate_roi()` |
| Rate limit handling | ⚠️ Not implemented | Providers |
| Budget alerts | ⚠️ Not implemented | Nexus |
| Weekly caps | ⚠️ Not implemented | Nexus |

### 7.2 Recommended Additions

1. **Rate limit retry logic** in provider modules
2. **Budget alerts** via Telegram
3. **Weekly/monthly budget caps**
4. **Usage dashboard** in `/txt/ai_costs` endpoint

---

## 8. Appendix: API Reference Links

### Official Documentation

- **OpenAI Pricing**: https://openai.com/api/pricing/
- **OpenAI Rate Limits**: https://platform.openai.com/docs/guides/rate-limits
- **Anthropic Pricing**: https://platform.claude.com/docs/en/about-claude/pricing
- **Anthropic Rate Limits**: https://support.claude.com/en/articles/8243635
- **GitHub Copilot Billing**: https://docs.github.com/en/copilot/concepts/billing
- **GitHub Copilot Rate Limits**: https://docs.github.com/en/enterprise-cloud@latest/copilot/concepts/rate-limits

### Internal Documentation

- **AI Nexus README**: `ai_nexus/README.md`
- **Spark Plug Architecture**: `docs/SPARK_PLUG_ARCHITECTURE_v0.1.md`
- **Tri-Agent Sessions**: `docs/TRI_AGENT_SESSION_v0.1.md`
- **Agent Registry**: `ai/agents/AGENTS_REGISTRY_v0.1.json`

---

## 9. Changelog

| Date | Version | Change |
|------|---------|--------|
| 2025-11-27 | 1.0 | Initial analysis document |
