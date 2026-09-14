# MOONSHOT PROTOCOL
## Exponential Recursive Self-Improvement Loop

### Mission
Achieve ESCAPE VELOCITY: A self-sustaining autonomous system that generates more value than it consumes.

### The Loop

```
┌─────────────────────────────────────────────────────────┐
│                    MOONSHOT CYCLE                        │
│                                                          │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐        │
│  │ EVALUATE │ ──► │ IMPROVE  │ ──► │ MEASURE  │        │
│  └──────────┘     └──────────┘     └──────────┘        │
│       │                                   │              │
│       │           ┌──────────┐           │              │
│       └────────── │ COMPOUND │ ◄─────────┘              │
│                   └──────────┘                          │
│                        │                                 │
│                        ▼                                 │
│               [TRIGGER NEXT CYCLE]                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Escape Velocity Score Components

| Factor | Weight | Current | Target |
|--------|--------|---------|--------|
| Capital | 30% | $8.99 | $200+ |
| Trading | 20% | Disabled | Enabled |
| Automation | 20% | 8 jobs | 15+ jobs |
| Income Channels | 15% | 2 pages | 5+ sources |
| Momentum | 15% | Starting | Compounding |

### Exponential Multipliers

1. **Capital Multiplier**: More money → more trades → more money
2. **Automation Multiplier**: More monitors → more opportunities → more automation
3. **Income Multiplier**: More channels → more revenue → more channels
4. **Intelligence Multiplier**: Better signals → better trades → better signals

### Rate Limits

- Max 12 cycles per day
- 30 minute cooldown between cycles
- 10 minute timeout per cycle

### How It Works

1. **Cron triggers** `moonshot_loop.py` every hour
2. **Loop evaluates** if cycle should run (rate limits, cooldown)
3. **Claude CLI** receives self-improvement prompt with full context
4. **Improvement executed** (code changes, new features, optimizations)
5. **Progress recorded** in `moonshot_improvements.jsonl`
6. **Score updated** in `moonshot_state.json`
7. **Next cycle scheduled** automatically

### Priority Focus Areas

When escape velocity score is:

- **0-25**: Focus on INCOME (get any money flowing)
- **25-50**: Focus on AUTOMATION (reduce human dependency)
- **50-75**: Focus on TRADING (compound capital)
- **75-100**: Focus on SCALING (multiply everything)

### Milestones

1. ☐ First Dollar (any income)
2. ☐ Trading Enabled ($50+ balance)
3. ☐ Positive PnL (profitable trades)
4. ☐ Daily Profit (consistent gains)
5. ☐ Escape Velocity (self-sustaining)

### Files

- `autonomous/moonshot_loop.py` - Main recursive loop
- `autonomous/escape_velocity_tracker.py` - Progress tracking
- `autonomous/recursive_trigger.sh` - Shell trigger
- `state/moonshot_state.json` - Loop state
- `state/moonshot_improvements.jsonl` - Improvement log
- `state/escape_velocity.json` - Velocity tracking

### Emergency Stop

To stop the loop:
```bash
# Remove from cron
crontab -l | grep -v moonshot | crontab -

# Or set max cycles to 0
echo '{"max_cycles": 0}' > state/moonshot_stop.json
```

### Manual Trigger

```bash
cd /root/hands-off-engine
python3 autonomous/moonshot_loop.py
```

---

*The system improves itself. Each cycle compounds on the last. Escape velocity is inevitable.*
