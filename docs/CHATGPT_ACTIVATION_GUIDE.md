# ChatGPT Integration Activation Guide

**Quick Start:** 5-minute setup to activate ChatGPT functionality

---

## Prerequisites

1. OpenAI account with API access
2. API key from https://platform.openai.com/api-keys
3. Credit/billing configured in OpenAI account

---

## Step 1: Configure API Key (2 minutes)

### Local/Termux Setup

```bash
# Navigate to repo root
cd ~/hands-off-engine

# Add to .env file
echo "OPENAI_API_KEY=sk-proj-your-actual-key-here" >> .env

# Verify
grep OPENAI_API_KEY .env
```

### Droplet Setup

```bash
# SSH to droplet
ssh your-droplet

# Add to .env
cd ~/hands-off-engine
echo "OPENAI_API_KEY=sk-proj-your-actual-key-here" >> .env

# Verify
grep OPENAI_API_KEY .env
```

### GitHub Actions

```bash
# Already configured in repository secrets
# Verify at: https://github.com/yaya1738/hands-off-engine/settings/secrets/actions
# Should see: OPENAI_API_KEY
```

---

## Step 2: Smoke Test (2 minutes)

```bash
# Test basic functionality
python3 -c "
from ai.integration import ChatGPTAdapter
adapter = ChatGPTAdapter()

# Verify API key loaded
print(f'API Key configured: {adapter.api_key is not None}')

# Test simple query
result = adapter.send_query('What is 2+2?')
print(f'Success: {result[\"success\"]}')
print(f'Response: {result.get(\"response\", \"ERROR\")}')
"
```

**Expected Output:**
```
API Key configured: True
Success: True
Response: 4
```

---

## Step 3: Test Market Analysis (1 minute)

```bash
# Test market analysis function
python3 -c "
from ai.integration import ChatGPTAdapter
adapter = ChatGPTAdapter()

result = adapter.analyze_market(
    'will-bitcoin-reach-100000-by-december-31-2025',
    current_price=0.49
)

print(f'Success: {result[\"success\"]}')
print(f'Analysis preview: {result.get(\"response\", \"\")[:200]}...')
"
```

---

## Step 4: Verify Logging (1 minute)

```bash
# Check that logs are being created
ls -la ai/integration/chatgpt_log.jsonl

# View recent entries
tail -n 5 ai/integration/chatgpt_log.jsonl | python3 -m json.tool
```

**Expected:** JSON log entries with timestamps and response previews

---

## Step 5: Test CLI Interface (Optional)

```bash
# Query
python3 ai/integration/chatgpt_adapter.py query \
  --prompt "What are the key factors affecting Bitcoin price?"

# Research
python3 ai/integration/chatgpt_adapter.py research \
  --topic "Polymarket trading strategies"

# Analyze
python3 ai/integration/chatgpt_adapter.py analyze \
  --market "will-bitcoin-reach-100000" \
  --price 0.49

# View history
python3 ai/integration/chatgpt_adapter.py history
```

---

## Troubleshooting

### "No OpenAI API key configured"

**Problem:** API key not loaded

**Solution:**
```bash
# Check .env exists
ls -la .env

# Check key is in file
grep OPENAI_API_KEY .env

# Check no quotes/spaces
cat .env | grep OPENAI_API_KEY
```

### "API error: 401"

**Problem:** Invalid API key

**Solution:**
1. Verify key at https://platform.openai.com/api-keys
2. Check key hasn't been revoked
3. Ensure no extra spaces in .env file

### "API error: 429"

**Problem:** Rate limit or quota exceeded

**Solution:**
1. Check OpenAI usage at https://platform.openai.com/usage
2. Verify billing is active
3. Check rate limits for your tier

### Import errors

**Problem:** Missing dependencies

**Solution:**
```bash
pip install openai requests python-dotenv
```

---

## Cost Monitoring

### Check Today's Usage

```bash
# View API calls made today
python3 -c "
import json
from datetime import datetime, timezone
from pathlib import Path

log_file = Path('ai/integration/chatgpt_log.jsonl')
today = datetime.now(timezone.utc).date()

if log_file.exists():
    calls = []
    with open(log_file) as f:
        for line in f:
            entry = json.loads(line)
            ts = datetime.fromisoformat(entry['timestamp'])
            if ts.date() == today:
                calls.append(entry)
    
    print(f'API calls today: {len(calls)}')
    print(f'Models used: {set(c.get(\"model\", \"unknown\") for c in calls)}')
else:
    print('No log file yet')
"
```

### Estimate Costs

**Pricing (gpt-4o):**
- Input: $2.50 / 1M tokens
- Output: $10.00 / 1M tokens

**Typical usage:**
- Query: ~500 input + ~200 output tokens = ~$0.003/call
- Market analysis: ~1000 input + ~500 output tokens = ~$0.008/call
- Research: ~2000 input + ~1000 output tokens = ~$0.015/call

**Daily Budget Examples:**
- 10 queries/day = $0.03/day = $0.90/month
- 5 market analyses/day = $0.04/day = $1.20/month
- 2 research tasks/day = $0.03/day = $0.90/month

**Total: <$3/month for typical usage**

---

## Next Steps After Activation

### Week 1: Data Collection

```bash
# Run daily market analysis
python3 scripts/daily_chatgpt_analysis.py  # (to be created)

# Review logs
tail -n 20 ai/integration/chatgpt_log.jsonl
```

### Week 2: Add Cost Tracking

```bash
# Implement cost tracker (see audit report recommendations)
# Track daily spend
# Set alerts
```

### Month 1: Evaluation

After 30 days:
1. Review total cost
2. Measure quality vs manual research
3. Identify valuable use cases
4. Decide to scale up or deprecate

---

## Integration with Existing Systems

### Mega Unified System

```python
from ai.mega_unified_system import get_mega_system

system = get_mega_system()

# Should now show chatgpt as active
status = system.get_full_state()
print(status['component_status']['chatgpt'])  # Should be "ready"
```

### AI Nexus Hub

```python
from ai.integration import get_hub

hub = get_hub()
state = hub.get_shared_state()

# ChatGPT should be in active agents
print(hub.get_agent_status())
```

---

## Safety Checks

### Before Going Live

- [ ] API key configured correctly
- [ ] Smoke test passes
- [ ] Logs are being created
- [ ] Cost tracking planned
- [ ] Rate limits understood
- [ ] Billing alerts set in OpenAI dashboard

### Recommended Limits (Start Conservative)

```python
# In chatgpt_adapter.py (future enhancement)
MAX_CALLS_PER_HOUR = 20
MAX_CALLS_PER_DAY = 100
MAX_COST_PER_DAY = 5.00  # USD
```

---

## Success Criteria

**Activation Successful When:**
- ✅ Smoke test returns valid response
- ✅ Market analysis works
- ✅ Logs are created
- ✅ No import errors
- ✅ Cost is predictable

**Ready for Production When:**
- ✅ 1 week of successful testing
- ✅ Cost < $5/week
- ✅ Quality meets expectations
- ✅ Integration with trading pipeline works

---

## Support

**Issues:**
- Check logs: `ai/integration/chatgpt_log.jsonl`
- Review audit: `docs/CHATGPT_AUDIT_2025-12-01.md`
- See protocols: `docs/CHATGPT_COMMS_PROTOCOL_v0.5.md`

**Questions:**
- Documentation: `ai/integration/AI_NEXUS_PROTOCOL.md`
- Code: `ai/integration/chatgpt_adapter.py`

---

**Activation Status:**
- Infrastructure: ✅ Ready
- Configuration: ⏳ Your turn
- Testing: ⏳ After config
- Production: ⏳ After testing

**Time to activate:** 5 minutes
**Time to production:** 1 week
