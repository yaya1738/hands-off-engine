# Autonomous Trading System Status

**Status:** READY (live-capable, initially paused)
**Mode File:** `state/trading_mode.json`
**Risk File:** `state/risk_profile.json`
**Hard Limits:** `config/hard_limits.json`

---

## What Exists

### 1. State Management

- `state/trading_mode.json`
  - System-managed on/off switch for live trading
  - Tracks:
    - `live_trading_enabled`: `true` / `false`
    - `reason`: human-readable explanation
    - `auto_paused`: `true` if system auto-paused (can auto-resume)
    - `pause_count_today`: circuit breaker counter
    - `last_resume`: timestamp of last resume

- `state/risk_profile.json`
  - Auto-tuned risk parameters, including:
    - `max_position_usd`
    - `max_daily_loss_usd`
    - `confidence_threshold`
    - `scale_factor`
    - `phase`: `baby_mode` / `scale_up` / `full_deployment`
    - `phase_entry_time`: when current phase started

- **`config/hard_limits.json` ✨ NEW**
  - **NEVER auto-tuned** - human-edited only
  - Absolute caps that recalibration cannot exceed:
    - `MAX_ABSOLUTE_POSITION_USD`: $200 (no trade larger)
    - `MAX_ABSOLUTE_DAILY_LOSS_USD`: $400 (circuit breaker)
    - `MAX_ABSOLUTE_OPEN_RISK_USD`: $1000 (total exposure)
    - `MIN_CONFIDENCE_THRESHOLD`: 40% (never trade below)
    - `MAX_ABSOLUTE_TRADES_PER_HOUR`: 20 (rate limit)

---

### 2. Auto-Pause / Auto-Resume Safeguards

**File:** `executor/trading_safeguards.py`

Core functions:

- `load_mode()` / `save_mode()`
  - Read/write `state/trading_mode.json`
  - Ensure atomic, crash-safe updates

- `maybe_auto_pause(reason: str)`
  - Circuit breaker
  - Switches mode to `disabled` when limits are hit
  - Records `reason` and timestamp
  - Sends notification

- `maybe_auto_resume(reason: str)`
  - Recovery logic
  - Only re-enables trading when:
    - Auto-paused previously, and
    - Health/performance conditions are satisfied
  - Records `reason` and timestamp
  - Sends notification

- **`check_trading_health()` ✨ NEW**
  - Checks before allowing live trades:
    1. Performance log freshness (< 48h since last log)
    2. Error rate (< 30% failures in last 24h)
    3. Risk profile freshness (< 36h since recalibration)
    4. No long auto-pause (< 72h paused)
  - Returns `(is_healthy, issues)`
  - Advisory gate - doesn't auto-pause, just blocks live trading

- **`enforce_hard_limits(profile)` ✨ NEW**
  - Enforces absolute caps on risk profile
  - Called when loading risk profile
  - Ensures recalibration can never exceed hard limits
  - Logs warnings when capping occurs

Current auto triggers:

- Daily loss limit hit → Auto-pause
- Rate limit exceeded (API safety) → Auto-pause
- Health check failure → Block live trading (advisory)

---

### 3. Executor Integration

**File:** `executor/ho_executor_plan.py`

- `is_live_trading_enabled()` ✨ UPDATED
  - Combines:
    - Environment flag: `LIVE_TRADING_ENABLED`
    - State file: `state/trading_mode.json`
    - **Health check: system must be healthy**
  - Returns `False` if:
    - Env not set
    - Mode is disabled
    - Manual override is active
    - **Health check fails**

- Dynamic risk parameters:
  - Executor reads `state/risk_profile.json`
  - **Hard limits enforced** via `enforce_hard_limits()`
  - Uses fields for:
    - Max position size (capped by hard limits)
    - Max daily loss (capped by hard limits)
    - Confidence threshold (bounded by hard limits)
    - Scaling factor

No trade is sent unless:
1. Live trading is enabled, and
2. **System health check passes**, and
3. Trade fits within the current risk profile and safeguards, and
4. **Trade doesn't exceed hard limits**

---

### 4. Recalibration Engine

**File:** `scripts/recalibrate_engine.py`
**Schedule:** Daily at 08:00 (cron)

Responsibilities:

1. Read last 7 days from `logs/trading_performance.jsonl`
2. Compute metrics:
   - Hit rate
   - PnL
   - Max drawdown
   - Volume / number of trades
3. Adjust `state/risk_profile.json`:
   - Good performance → cautiously scale up
   - Poor performance → scale down or keep small
   - **✨ CONSERVATIVE PHASE PROGRESSION:**
     - `baby_mode → scale_up`: Requires 30+ trades, 7+ days, 52%+ hit rate
     - `scale_up → full_deployment`: Requires 50+ trades, 14+ days, 53%+ hit rate
   - **✨ HARD LIMITS ENFORCED:** Profile capped before saving
4. Manage deployment phases:
   - `baby_mode` → `scale_up` → `full_deployment`
   - Phase promotion only when metrics are healthy AND time requirements met

If the system was auto-paused and metrics look good, the engine can trigger `maybe_auto_resume()`.

---

### 5. Manual Overrides

**Files:**

- `scripts/pause_trading.py`
  - Sets trading mode to `disabled`
  - Sets `manual_override = true` (blocks auto-resume)
  - Prevents auto-resume until explicitly cleared

- `scripts/resume_trading.py`
  - Re-enables trading (`manual_override = false`)
  - Resets / updates mode with a human-specified reason

Human control always wins over automation.

---

### 6. Smart Notifications

Notifications are sent on:

- Mode changes (pause / resume)
- Phase upgrades (e.g. `baby_mode → scale_up`)
- Recalibration results and major risk changes
- Critical errors in safeguards or recalibration
- **✨ Hard limit violations** (when capping occurs)

Noise is minimized: only **material** events are pushed.

---

## Safety Layers (Defense in Depth)

### Layer 1: Hard Limits (Outer Shell)
- **File:** `config/hard_limits.json`
- **Human-edited only** - never touched by automation
- Absolute caps that can NEVER be exceeded:
  - Max position: $200
  - Max daily loss: $400
  - Min confidence: 40%
- Enforced at safeguards initialization
- Protects against:
  - Recalibration bugs
  - Phase progression errors
  - Configuration mistakes

### Layer 2: Risk Profile (Adaptive Layer)
- **File:** `state/risk_profile.json`
- **Auto-tuned daily** by recalibration engine
- Conservative phase progression:
  - Minimum trades per phase (30-50)
  - Minimum days per phase (7-14)
  - Minimum performance metrics
- Always capped by Layer 1 hard limits
- Protects against:
  - Lucky short streaks
  - Premature scaling
  - Market regime changes

### Layer 3: Health Check Gate
- **Function:** `check_trading_health()`
- **Checks before every trade:**
  - Data freshness
  - Error rate
  - Recalibration status
- Blocks live trading if unhealthy
- Doesn't auto-pause (advisory only)
- Protects against:
  - Stale data
  - High error rates
  - System degradation

### Layer 4: Real-Time Safeguards
- **Class:** `TradingSafeguards`
- **Per-trade validation:**
  - Position size check
  - Daily loss limit
  - Rate limiting
  - Confidence threshold
- Auto-pauses if limits hit
- Protects against:
  - Single large losses
  - Cascading failures
  - API rate limits

### Layer 5: Executor Validation
- **File:** `executor/ho_executor_plan.py`
- **Final gate before API call:**
  - All previous layers passed
  - Market ID valid
  - Side valid (YES/NO)
  - Amount positive
- Protects against:
  - Malformed trades
  - API errors
  - Logic bugs

---

## Current Configuration

- **Trading Mode:** `DISABLED` (`initial_setup`)
- **Phase:** `baby_mode`
- **Max Position:** `$50` (hard limit: `$200`)
- **Max Daily Loss:** `$200` (hard limit: `$400`)
- **Confidence Threshold:** `45%` (hard min: `40%`)
- **Scale Factor:** `1.0x`

- **Integration:** ✅ All components wired into the executor pipeline
- **Testing:** ✅ All safety layers verified
- **Recalibration:** ✅ Scheduled daily at 08:00
- **Hard Limits:** ✅ Enforced and tested

---

## Runtime Cycle

### Hourly (or per pipeline run)

1. Pipeline generates candidate trades.
2. **Executor calls `is_live_trading_enabled()`:**
   - Checks environment variable
   - Checks state file
   - **✨ Runs health check**
3. Executor loads `state/risk_profile.json`.
4. **✨ Hard limits enforced** via `enforce_hard_limits()`.
5. Safeguards validate:
   - Max position per trade (vs hard limits)
   - Daily loss (vs hard limits)
   - Rate limit
   - Confidence threshold
6. If limits are breached:
   - `maybe_auto_pause(reason)` triggers
   - Trading stops
   - Notification is sent
7. All trades and outcomes are appended to `logs/trading_performance.jsonl`.

### Daily at 08:00

1. `recalibrate_engine.py` runs.
2. Reads last 7 days of performance.
3. **✨ Applies conservative phase progression rules:**
   - Checks minimum trades
   - Checks minimum days in phase
   - Checks performance metrics
4. Updates `state/risk_profile.json`.
5. **✨ Enforces hard limits before saving.**
6. Logs recalibration decisions.
7. If the system is auto-paused and metrics are healthy:
   - Calls `maybe_auto_resume(reason)`.

---

## Activation Checklist

1. **Add credentials** to `.env.polymarket`:

   ```bash
   POLYMARKET_PRIVATE_KEY=0x...
   POLYMARKET_FUNDER_ADDRESS=0x...
   LIVE_TRADING_ENABLED=1
   ```

2. **Review hard limits** in `config/hard_limits.json`:

   ```json
   {
     "MAX_ABSOLUTE_POSITION_USD": 200,
     "MAX_ABSOLUTE_DAILY_LOSS_USD": 400,
     ...
   }
   ```

3. **Enable trading:**

   ```bash
   python3 scripts/resume_trading.py
   ```

4. **Monitor the first live cycles:**

   ```bash
   ./scripts/run_and_notify.sh --bankroll 500
   ```

5. Confirm:

   * Safeguards fire correctly (test forced errors / loss).
   * Health checks pass.
   * Hard limits are enforced.
   * Recalibration runs at 08:00 and logs updates.
   * Notifications arrive as expected.

Once this is verified, the system can be left to operate autonomously.

---

## Why This Is Autonomous (and Safe)

* **Self-Monitoring** – Tracks its own performance and limits.
* **Self-Tuning** – Adjusts risk parameters based on real results.
* **Self-Protecting** – Auto-pauses when limits or health checks fail.
* **Self-Recovering** – Auto-resumes only when conditions improve.
* **Self-Progressing** – Gradually scales from `baby_mode` toward `full_deployment`.
* **Smart Communication** – Notifies only on meaningful changes.
* **✨ Hard Bounded** – Can NEVER exceed absolute human-set caps.
* **✨ Conservatively Progresses** – Requires time + performance to upgrade phases.
* **✨ Health-Aware** – Blocks trading if system is degraded.

With 5 layers of defense and conservative progression rules, the system is ready to transition from DRYRUN to live trading in a controlled, incremental way.

---

## Executor Modes

The system supports three execution modes:

### 1. `dryrun` (Default)
- **Purpose:** Low-level debugging and testing
- **Behavior:** Runs planning logic, no API calls, minimal logging
- **Use case:** Initial development, quick smoke tests
- **Set via:** `HANDS_OFF_EXECUTOR_MODE=dryrun` or default (no env var)

### 2. `shadow` (Recommended for Pre-Live Testing)
- **Purpose:** Full pipeline execution without real money at risk
- **Behavior:**
  - Executes complete decision pipeline
  - Applies all risk profile and safeguards
  - Runs health checks and hard limit enforcement
  - Logs would-be trades to `state/shadow_trades.jsonl`
  - **Never calls real trading API**
- **Use case:** Validate safety layers, observe would-be performance
- **Set via:** `HANDS_OFF_EXECUTOR_MODE=shadow`

### 3. `live` (Production)
- **Purpose:** Real trades with real money
- **Behavior:**
  - Full safety pipeline (health, safeguards, hard limits)
  - Calls actual Polymarket API
  - Requires all safety gates to pass
- **Use case:** Production trading
- **Set via:** `HANDS_OFF_EXECUTOR_MODE=live` OR `LIVE_TRADING_ENABLED=1`

---

## Recommended Rollout Path

### Phase 0: Shadow Mode (1-2 weeks)
```bash
# Set shadow mode
export HANDS_OFF_EXECUTOR_MODE=shadow

# Run hourly (via cron or manual)
./scripts/run_and_notify.sh --bankroll 5000

# Monitor shadow log
tail -f state/shadow_trades.jsonl

# Analyze would-be performance
python3 -c "
import json
trades = [json.loads(line) for line in open('state/shadow_trades.jsonl')]
print(f'Total trades: {len(trades)}')
blocked = [t for t in trades if 'blocked' in t.get('message', '').lower()]
print(f'Blocked: {len(blocked)}')
passed = [t for t in trades if t.get('allowed_by_safeguards', {}).get('allowed', False)]
print(f'Would execute: {len(passed)}')
"
```

**Look for:**
- Safeguards triggering appropriately
- Health checks passing
- Hard limits never exceeded
- Reasonable hit rate in shadow logs

### Phase 1: Live (Baby Mode)
```bash
# Add Polymarket credentials
# Edit .env.polymarket:
#   POLYMARKET_PRIVATE_KEY=0x...
#   POLYMARKET_FUNDER_ADDRESS=0x...

# Enable live mode
export HANDS_OFF_EXECUTOR_MODE=live

# Enable trading
python3 scripts/resume_trading.py

# Run ONE manual cycle
./scripts/run_and_notify.sh --bankroll 500

# Verify trade on Polymarket.com
# Check logs
tail -f logs/trading_performance.jsonl
```

**Monitor for 48 hours** before allowing hourly automation.

### Phase 2: Scale Up
After successful Phase 1, recalibration will automatically handle scaling based on performance.

---

## Manual Operations

### Pause Trading
```bash
python3 scripts/pause_trading.py
```
Sets `manual_override=true` to prevent auto-resume.

### Resume Trading
```bash
python3 scripts/resume_trading.py
```
Overrides any pause (manual or auto).

### Check Status
```bash
# View trading mode
cat state/trading_mode.json

# View risk profile
cat state/risk_profile.json

# View hard limits
cat config/hard_limits.json

# View recent performance
tail -20 logs/trading_performance.jsonl
```

### Force Recalibration
```bash
python3 scripts/recalibrate_engine.py
```
Runs immediately instead of waiting for 08:00.

### Edit Hard Limits
1. Edit `config/hard_limits.json` manually
2. Restart executor (or wait for next hourly cycle)
3. Hard limits take effect immediately

---

## Testing Checklist

Before relying on autonomous operation:

1. **✅ Unit tests** for each safety layer
2. **✅ Hard limit enforcement** verified
3. **✅ Health check** triggers correctly
4. **✅ Phase progression** requires time + performance
5. **⏳ Replay/backtest** with historical data (recommended)
6. **⏳ Dry-run live** for several days (recommended)
7. **⏳ Smoke-test pause/resume** in production (recommended)

---

## Phase Progression Requirements

### Baby Mode → Scale Up
- **Minimum Trades:** 30
- **Minimum Days:** 7
- **Minimum Hit Rate:** 52%
- **Max Drawdown:** < 5% of bankroll
- **Result:** $50 → $250 position, 1.0x → 2.5x scale

### Scale Up → Full Deployment
- **Minimum Trades:** 50
- **Minimum Days:** 14
- **Minimum Hit Rate:** 53%
- **Max Drawdown:** < 8% of bankroll
- **Result:** $250 → $1000 position (capped at $200 by hard limits), 2.5x → 5.0x scale

Note: Even if performance is excellent, phase upgrades are locked until both time AND trade count requirements are met.

---

## Documentation

- **This File:** `state/AUTONOMOUS_SYSTEM_STATUS.md`
- **Trading Integration:** `docs/POLYMARKET_API_INTEGRATION.md`
- **Trading Status:** `state/TRADING_BUTTON_STATUS.md`
- **Build Summary:** `state/AUTONOMOUS_BUILD_SUMMARY.txt`

---

**System Status:** 🚀 READY FOR AUTONOMOUS OPERATION (WITH SAFETY LAYERS)
