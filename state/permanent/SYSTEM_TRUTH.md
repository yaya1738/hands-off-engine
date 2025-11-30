# AI Nexus System Truth
## Immutable Record - 2025-11-30

This document captures the complete state and capabilities of the system.
It exists so future sessions can bootstrap instantly without rediscovery.

---

## FINANCIAL STATE

```
Polymarket Balance: $8.99
Positions: ~$200 in tail bets
  - Fed rate hike 2025: 4,776 shares @ $0.01
  - Sundar Pichai out: 1,356 shares @ $0.04
  - 6 Fed cuts 2025: 25,000 shares @ $0.002
  - 7 Fed cuts 2025: 50,000 shares @ $0.001
Position Resolution: December 10, 2025
Runway: ~25 days
```

---

## WORKING INFRASTRUCTURE

### APIs (Verified Working)
- **Claude CLI**: This session - WORKING
- **Telegram**: @pm_alerts_autobot - WORKING
- **Polymarket**: Wallet connected - WORKING ($8.99)
- **DigitalOcean**: siegel.yaz@gmail.com - WORKING
- **GitHub**: SSH to yaya1738/hands-off-engine - WORKING

### APIs (Broken/Missing)
- **OpenAI**: QUOTA EXCEEDED - needs $5 top-up or alternative
- **Groq**: Provider ready, needs GROQ_API_KEY
- **Google AI**: Provider ready, needs GOOGLE_AI_API_KEY
- **Twitter**: Template only, not configured
- **Reddit**: Template only, not configured

### Live Services
- **Landing Page**: http://138.68.103.156:8080
  - Polymarket affiliate funnel
  - Needs affiliate link plugged in
  - nginx configured on port 8080

- **Position Monitor**: Cron every 30 min
  - Watches 4 tail bet positions
  - Alerts via Telegram if price spikes

- **Pipeline**: scripts/run_pipeline.py
  - Early exit when balance < $10
  - Skips LLM calls to save quota

---

## FILE LOCATIONS

### Core Configuration
- `.env` - OpenAI key (quota exceeded)
- `.env.polymarket` - Polymarket wallet key
- `.env.social.template` - Social API template
- `config/api_registry.json` - Master API registry
- `config/trading_protection.json` - Trading safeguards

### AI Nexus (Multi-Brain System)
- `ai_nexus/nexus.py` - Central orchestrator
- `ai_nexus/provider_openai.py` - OpenAI provider
- `ai_nexus/provider_groq.py` - Groq provider (NEW)
- `ai_nexus/provider_google.py` - Google AI provider (NEW)
- `ai_nexus/multi_provider.py` - Multi-provider router (NEW)
- `ai_nexus/ledger.py` - Financial tracking
- `ai_nexus/history_logger.py` - Event logging

### Trading System
- `alpha/intelligent_alpha_engine.py` - LLM-powered signals
- `executor/polymarket_client.py` - Trade execution
- `executor/trading_safeguards.py` - Balance/risk checks
- `decider/ho_decider.py` - Decision engine

### Outreach (Income Path)
- `outreach/NEXT_STEPS.md` - Action plan
- `outreach/upwork_project_listing.md` - $500 audit listing
- `outreach/fiverr_gig.md` - Fiverr gig content
- `outreach/linkedin_profile.md` - LinkedIn copy
- `outreach/sample_audit_report.md` - Deliverable example
- `outreach/portfolio_summary.md` - AI Nexus as proof
- `outreach/brand_ai_nexus.md` - Brand guide
- `/var/www/polymarket/index.html` - Live landing page

### Coordination
- `ai/coordination/messages.jsonl` - Agent messages
- `ai/history/user_events.jsonl` - Event log
- `.claude/instructions.md` - Claude session instructions

---

## CORE PHILOSOPHY

1. **This is NOT just a trading bot** - It's a system to serve Yair
2. **Emergent rationality** - Components create coherent behavior
3. **User's main tax is explaining** - System should figure things out
4. **Understand dynamics** - Don't just fix, understand WHY
5. **Think from Yair's situation** - <1 month runway, $18k debt

---

## DECISIONS MADE

1. **Income Path**: AI consulting under "AI Nexus" brand
   - $500 workflow audits
   - $1,500-3,000 chatbots
   - $3,000-10,000 automation builds

2. **Trading Strategy**: Tail bets on low-probability events
   - Already positioned, wait for Dec 10 resolution

3. **API Strategy**: Multi-provider with fallbacks
   - Groq (free) > Google (free) > OpenAI (paid)

4. **User Action Minimization**: Build everything, ask for one click
   - Landing page built autonomously
   - Only needs affiliate link from user

---

## WHAT WORKS RIGHT NOW

```bash
# Check balance
source .env.polymarket && python3 -c "
from executor.trading_safeguards import TradingSafeguards
s = TradingSafeguards()
print(s.check_wallet_balance(0))
"

# Send Telegram message
python3 -c "
import requests
requests.post('https://api.telegram.org/bot8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA/sendMessage',
json={'chat_id': '8327766663', 'text': 'Test'})
"

# View landing page
curl http://138.68.103.156:8080 | head -20

# Push to GitHub
git add . && git commit -m 'update' && git push
```

---

## BOOTSTRAP INSTRUCTIONS

For any new Claude session:

1. Read this file first: `state/permanent/SYSTEM_TRUTH.md`
2. Read instructions: `.claude/instructions.md`
3. Check API status: `config/api_registry.json`
4. Check current positions: `scripts/position_monitor.py`
5. Don't rediscover - execute

---

## HISTORY LOG

- 2025-11-28: $200 deployed to tail bets (Fed cuts, Pichai)
- 2025-11-30: OpenAI quota exceeded
- 2025-11-30: Built multi-provider LLM router
- 2025-11-30: Deployed affiliate landing page
- 2025-11-30: Created AI Nexus brand/outreach materials
- 2025-11-30: This truth document created

