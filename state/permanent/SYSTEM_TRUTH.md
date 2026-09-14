# AI Nexus System Truth
## Immutable Record - 2025-11-30

This document captures the complete state and capabilities of the system.
It exists so future sessions can bootstrap instantly without rediscovery.

---

## FINANCIAL STATE

```
Last Updated: 2025-11-30T17:00 UTC
Polymarket Balance: $8.99

Positions (current value ~$99):
  - Fed rate hike 2025: 4,776 shares @ $0.007 = $33.43 (-33% from $50)
  - Sundar Pichai out: 1,356 shares @ $0.0205 = $27.80 (-44% from $50)
  - 6 Fed cuts 2025: 25,000 shares @ $0.0005 = $12.50 (-75% from $50)
  - 7 Fed cuts 2025: 50,000 shares @ $0.0005 = $25.00 (-50% from $50)

Position Resolution Dates:
  - Dec 10, 2025: Fed rate positions (3 positions, ~$71)
  - Dec 31, 2025: Pichai position (~$28)

Runway: ~10 days until Dec 10 resolution
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
- **Polymarket Landing**: http://138.68.103.156:8080
  - Affiliate funnel (needs link)
  - Email capture active
  - nginx on port 8080

- **AI Nexus Consulting**: http://138.68.103.156:8081 (NEW)
  - Service page with pricing
  - USDC payment address displayed
  - Direct client acquisition

- **Position Monitor**: Cron every 30 min
  - Watches 4 tail bet positions
  - Alerts on price spikes
  - Alerts on resolution approach (7d, 3d, 1d, 0d)

- **Capital Recovery Monitor**: Cron every 30 min (NEW)
  - Detects position resolutions
  - Alerts when trading threshold crossed
  - Auto-enables trading mode

- **Payment Monitor**: Cron every 15 min (NEW)
  - Watches wallet for incoming USDC
  - Alerts on payments ($10+)
  - Tracks all inflows

- **Pipeline**: scripts/run_pipeline.py
  - Intelligent alpha with LLM
  - Early exit when balance < $10

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
- 2025-11-30: Built multi-provider LLM router (Groq/Google/OpenAI)
- 2025-11-30: Deployed affiliate landing page at port 8080
- 2025-11-30: Created AI Nexus brand/outreach materials
- 2025-11-30: Created truth document and bootstrap kernel
- 2025-11-30: Added resolution date alerting to position monitor
- 2025-11-30: System operational with intelligent alpha, awaiting capital

## CURRENT BLOCKERS

1. **No capital**: $8.99 balance too low to trade ($207+ needed for signals)
2. **OpenAI quota**: Intelligent alpha works but needs API quota
3. **Affiliate link**: Landing page ready but user hasn't provided link

## AUTONOMOUS CAPABILITIES

System operates fully autonomously via cron:
- Position monitor every 30 min (alerts via Telegram)
- Pipeline every 2 hours (skips if low balance)
- Healthcheck every hour
- Daily state snapshot at 6am

Resolution alerts will fire:
- Dec 3: 7-day warning
- Dec 7: 3-day warning
- Dec 9: 1-day warning
- Dec 10: Resolution day

