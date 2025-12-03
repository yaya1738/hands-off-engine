# HANDS-OFF ENGINE - System Blueprint
## Complete Architecture & Implementation Specification

**Master**: Yair Siegel
**Generated**: 2025-11-30
**Version**: 2.0

---

## 1. INFRASTRUCTURE OVERVIEW

### 1.1 Compute Cluster
```
TOTAL CAPACITY: 28 vCPUs | 56 GB RAM | 1120 GB Disk
Monthly Cost: ~$384

NODE 1: pm-helper (PRIMARY)
  - IP: 138.68.103.156
  - Private: 10.114.0.5
  - Specs: 4 vCPU, 8GB RAM, 160GB
  - Role: Primary orchestrator, API hub, dashboard
  - Services: Nginx, uvicorn, cron master

NODE 2: ho-compute-2a
  - IP: 134.122.124.240
  - Private: 10.116.0.6
  - Specs: 8 vCPU, 16GB RAM, 320GB
  - Role: Compute worker
  - Services: Python workers, batch processing

NODE 3: ho-compute-2b
  - IP: 198.211.96.196
  - Private: 10.116.0.5
  - Specs: 8 vCPU, 16GB RAM, 320GB
  - Role: Compute worker
  - Services: Python workers, batch processing

NODE 4: ho-scale (CLI HOST)
  - IP: 67.205.153.121
  - Private: 10.116.0.4
  - Specs: 8 vCPU, 16GB RAM, 320GB
  - Role: Claude CLI host, autonomous operations
  - Services: Claude CLI v2.0.55, Node.js v18
```

### 1.2 Network Topology
```
                    INTERNET
                        |
            +-----------+-----------+
            |                       |
      [pm-helper:80/443]    [ho-scale:Claude CLI]
       Primary Node              CLI Host
            |                       |
    +-------+-------+               |
    |               |               |
[compute-2a]  [compute-2b]          |
    |               |               |
    +-------+-------+---------------+
                    |
            PRIVATE NETWORK
              10.116.0.0/16
```

---

## 2. AI PROVIDERS

### 2.1 Provider Matrix

| Provider | Model | Cost | Speed | Use Case |
|----------|-------|------|-------|----------|
| Groq | llama-3.1-70b | FREE | Fast | Primary inference |
| Google AI | gemini-1.5-flash | FREE | Medium | Fallback |
| OpenAI | gpt-4-turbo | $0.01/1K | Slow | High-quality analysis |
| Local | Heuristics | FREE | Instant | Fast sentiment/signals |

### 2.2 Provider Fallback Chain
```
1. Check cache (instant)
2. Try Groq (free, fast)
3. Try Google AI (free, medium)
4. Try OpenAI (paid, high quality)
5. Fall back to local heuristics (always available)
```

### 2.3 API Keys Required
```bash
# .env configuration
GROQ_API_KEY=gsk_...           # FREE - get at console.groq.com
GOOGLE_AI_KEY=AIza...          # FREE - get at aistudio.google.com
OPENAI_API_KEY=sk-...          # PAID - existing key
ANTHROPIC_API_KEY=sk-ant-...   # For Claude CLI
```

---

## 3. COMPONENT ARCHITECTURE

### 3.1 Core Systems

```
HANDS-OFF-ENGINE/
├── ai/                         # AI Integration Layer
│   ├── unified_ai.py          # Master AI controller
│   ├── mega_unified_system.py # Unified coordination
│   └── tri_agent.py           # Multi-agent coordination
│
├── autonomous/                 # Autonomous Agents
│   ├── dense_ai.py            # Dense intelligence (NEW)
│   ├── web_agent.py           # Web data gathering
│   ├── brain.py               # Cluster brain
│   └── moonshot_loop.py       # Self-improvement loop
│
├── trading/                    # Trading Components
│   ├── micro_trader.py        # Micro-trading engine
│   ├── polymarket_client.py   # Polymarket integration
│   └── strategy_engine.py     # Strategy evaluation
│
├── monitoring/                 # Monitoring Systems
│   ├── position_monitor.py    # Position tracking
│   ├── capital_recovery.py    # Capital recovery alerts
│   └── payment_monitor.py     # Payment detection
│
├── state/                      # State Management
│   ├── brain_state.json       # Cluster state
│   ├── scaling_state.json     # Scaling state
│   └── dense_ai_state.json    # Dense AI state
│
├── scripts/                    # Automation Scripts
│   ├── healthcheck.sh         # System health
│   ├── deploy_autonomous.sh   # Deploy to nodes
│   └── snapshot_system_state.py
│
└── ui/                         # User Interfaces
    └── unified_dashboard.py   # Web dashboard
```

### 3.2 Data Flow Architecture

```
                EXTERNAL DATA SOURCES
                        |
    +-------------------+-------------------+
    |         |         |         |         |
[CoinGecko] [Polymarket] [CryptoCompare] [Alternative.me]
    |         |         |         |         |
    +-------------------+-------------------+
                        |
                   WEB AGENT
              (autonomous/web_agent.py)
                        |
            +-----------+-----------+
            |                       |
       [Price Data]          [Sentiment]
       [News Headlines]      [Fear & Greed]
            |                       |
            +-----------+-----------+
                        |
                   DENSE AI
              (autonomous/dense_ai.py)
                        |
    +-------------------+-------------------+
    |         |         |         |         |
[Local NLP] [Groq AI] [Google AI] [OpenAI]
    |         |         |         |         |
    +-------------------+-------------------+
                        |
               SYNTHESIZED ANALYSIS
                        |
            +-----------+-----------+
            |                       |
    [Trading Signals]        [Alerts]
    [Risk Assessment]        [Reports]
            |                       |
            +-----------+-----------+
                        |
    +-------------------+-------------------+
    |                   |                   |
[Micro Trader]    [Dashboard]    [Notifications]
[Position Monitor] [State Files] [Logs]
```

---

## 4. IMPLEMENTATION DISPATCH LAYOUT

### 4.1 Task Dispatch Matrix

| Task Type | Primary Node | Fallback | Method |
|-----------|--------------|----------|--------|
| Web scraping | pm-helper | Any compute | Cron |
| AI inference | pm-helper | ho-scale | API call |
| Heavy compute | compute-2a/2b | ho-scale | SSH dispatch |
| CLI operations | ho-scale | pm-helper | Claude CLI |
| Trading execution | pm-helper | - | Direct API |

### 4.2 Cron Job Distribution

**pm-helper (Primary)**:
```cron
*/10 * * * * web_agent.py fetch        # Web data refresh
*/5  * * * * dense_ai.py market        # Dense analysis
*/30 * * * * position_monitor.py       # Position tracking
0    8 * * * daily_digest.py           # Daily summary
0    */2 * * * pipeline_runner.py      # Trading pipeline
0    */6 * * * moonshot_loop.sh        # Self-improvement
```

**ho-scale (CLI Host)**:
```cron
# Reserved for Claude CLI autonomous operations
# Tasks dispatched via Claude Code sessions
```

### 4.3 Service Ports

| Port | Service | Node |
|------|---------|------|
| 80 | Nginx (HTTP) | pm-helper |
| 443 | Nginx (HTTPS) | pm-helper |
| 8002 | Dashboard API | pm-helper |
| 8080 | Landing page | pm-helper |
| 8081 | AI Nexus page | pm-helper |

---

## 5. META SPECIFICATIONS

### 5.1 System Invariants

1. **Master Identity**: All operations serve Yair Siegel
2. **Resource Priority**: Free providers first, paid as fallback
3. **Redundancy**: Every critical function has a fallback
4. **State Persistence**: All state is JSON, disk-backed
5. **Logging**: All actions logged to /var/log/hands-off/

### 5.2 Configuration Hierarchy

```
1. Environment variables (.env)
2. JSON config files (config/)
3. Python module defaults
4. Hardcoded fallbacks
```

### 5.3 Error Handling Strategy

```
Level 1: Retry (3 attempts, exponential backoff)
Level 2: Fallback to alternative provider
Level 3: Fall back to local heuristics
Level 4: Log error, notify if critical
Level 5: Graceful degradation (continue without feature)
```

---

## 6. PROVIDER SPECIFICATIONS

### 6.1 Data Providers

**CoinGecko** (FREE):
- Endpoint: api.coingecko.com/api/v3
- Rate limit: 10-30 calls/min
- Data: Prices, market cap, volume, 24h change

**Polymarket** (FREE):
- Endpoint: clob.polymarket.com, gamma-api.polymarket.com
- Auth: CLOB client with API key
- Data: Markets, prices, orderbooks

**Alternative.me** (FREE):
- Endpoint: api.alternative.me/fng
- Rate limit: Unlimited
- Data: Fear & Greed Index

**CryptoCompare** (FREE tier):
- Endpoint: min-api.cryptocompare.com
- Rate limit: 100K calls/month
- Data: News headlines, social stats

### 6.2 AI Providers Configuration

**Groq**:
```python
{
    "base_url": "https://api.groq.com/openai/v1/chat/completions",
    "model": "llama-3.1-70b-versatile",
    "max_tokens": 2000,
    "temperature": 0.3,
    "timeout": 60
}
```

**Google AI**:
```python
{
    "base_url": "https://generativelanguage.googleapis.com/v1beta/models",
    "model": "gemini-1.5-flash",
    "max_tokens": 2000,
    "temperature": 0.3,
    "timeout": 60
}
```

**OpenAI**:
```python
{
    "base_url": "https://api.openai.com/v1/chat/completions",
    "model": "gpt-4-turbo-preview",
    "max_tokens": 2000,
    "temperature": 0.3,
    "timeout": 120
}
```

---

## 7. PLANNING SYSTEM UTILIZATION

### 7.1 Autonomous Planning Capabilities

The system has multi-level planning:

1. **Immediate Planning** (Dense AI):
   - Real-time market analysis
   - Signal detection
   - Quick decision making

2. **Session Planning** (Claude CLI):
   - Multi-step task execution
   - Code generation and modification
   - System improvement

3. **Strategic Planning** (Moonshot Loop):
   - Self-improvement cycles
   - Capability expansion
   - Progress tracking

### 7.2 Planning Integration Points

```
USER REQUEST
     |
     v
[Claude CLI] ---> [Plan Mode]
     |                 |
     v                 v
[Direct Action]   [Multi-step Plan]
     |                 |
     v                 v
[Dense AI] <---- [Execute Steps]
     |                 |
     v                 v
[Analysis]       [Verify Results]
     |                 |
     +--------+--------+
              |
              v
         [State Update]
              |
              v
         [Notification]
```

### 7.3 Recommended Planning Workflows

**Trading Analysis**:
```
1. web_agent.fetch_all() -> Get fresh data
2. dense_ai.analyze_market() -> Dense analysis
3. If signals detected:
   a. Generate trade thesis
   b. Calculate risk/reward
   c. If approved: execute trade
4. Log results
```

**System Improvement**:
```
1. moonshot_loop detects opportunity
2. Claude CLI session initiated
3. Plan mode: design improvement
4. Execute implementation
5. Test and verify
6. Commit and deploy
7. Update escape velocity metrics
```

**Capital Recovery**:
```
1. position_monitor detects resolution
2. capital_recovery calculates return
3. If threshold met: trigger singularity
4. Execute trading sequence
5. Update financial state
```

---

## 8. UTILIZATION STRATEGY

### 8.1 Current Utilization

| Component | Status | Utilization |
|-----------|--------|-------------|
| Web Agent | Active | 100% (cron) |
| Dense AI | Active | 100% (cron) |
| Position Monitor | Active | 100% (cron) |
| Claude CLI | Available | On-demand |
| Compute Nodes | Available | <10% |
| Trading | Blocked | Waiting for $50 |

### 8.2 Optimization Opportunities

1. **Parallel Data Fetching**: Use ThreadPoolExecutor for all API calls
2. **Distributed Processing**: Dispatch heavy compute to worker nodes
3. **Caching**: Aggressive caching with TTL for repeated queries
4. **Batch Processing**: Combine multiple analyses into single runs
5. **Resource Pooling**: Share AI provider connections across agents

### 8.3 Scaling Triggers

| Metric | Threshold | Action |
|--------|-----------|--------|
| Balance > $50 | Capital | Enable trading |
| Balance > $200 | Capital | Full autonomous mode |
| CPU > 80% | Resource | Scale up compute |
| Errors > 10/hr | Health | Alert + diagnose |
| Latency > 5s | Performance | Optimize or scale |

---

## 9. FULL SITUATION SUMMARY

### 9.1 Financial State
- Balance: $8.99 cash
- Positions: ~$98 (pending resolution)
- Total equity: ~$107
- Gap to trading: $41 ($50 threshold)

### 9.2 System State
- 4 nodes healthy
- 28 vCPUs available
- All monitors active
- Claude CLI ready
- Dense AI operational
- Web agent operational

### 9.3 Capabilities
- Real-time market data
- Multi-provider AI analysis
- Automated signal detection
- Position tracking
- Capital recovery alerts
- Self-improvement loops

### 9.4 Limitations
- Trading blocked (< $50)
- OpenAI quota may be limited
- Need Groq/Google API keys for redundancy

---

## 10. NEXT ACTIONS

### Immediate (Today):
1. Add Groq API key to .env
2. Add Google AI key to .env
3. Test full Dense AI with all providers
4. Verify cron jobs running

### Short-term (This Week):
1. Complete position resolution tracking
2. Set up singularity trigger at $50
3. Deploy to all compute nodes
4. Test distributed processing

### Medium-term (This Month):
1. Reach $50 threshold
2. Enable live trading
3. Scale compute as needed
4. Optimize AI provider usage

---

**Blueprint Generated by Claude Code**
**Serving: Yair Siegel**
