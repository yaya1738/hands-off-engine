# Scripts Directory

Executable scripts for running and testing the Hands-Off Engine pipeline.

## Main Scripts

### `system_audit.py` - System Health Check ⭐

Run a comprehensive audit of the entire Hands-Off Engine system:

```bash
# Basic audit (generates report in reports/)
python3 scripts/system_audit.py

# Verbose mode (see all checks in real-time)
python3 scripts/system_audit.py --verbose

# Custom output file
python3 scripts/system_audit.py -o my_audit.md
```

**Checks:**
- ✅ Core components (alpha, decider, executor, fetchers, audit, AI)
- ✅ Configuration and state files
- ✅ Safety settings (DRYRUN enforcement, credentials)
- ✅ Audit trails and logging
- ✅ Documentation completeness
- ✅ Test infrastructure
- ✅ Dependencies
- ✅ AI coordination status
- ✅ Financial ledger

**Output:**
- Console summary with pass/warn/error counts
- Markdown report with detailed findings
- Recommendations for improvements

**Use Cases:**
- Pre-deployment health check
- Regular system validation
- Compliance verification
- Debugging system issues

See [README_SYSTEM_AUDIT.md](README_SYSTEM_AUDIT.md) for complete documentation.

---

### `run_pipeline.py` - Full Pipeline Runner ⭐

Run the complete end-to-end pipeline (Sync → Decider → Executor):

```bash
# DRYRUN mode (safe, no real money)
python3 scripts/run_pipeline.py

# With custom bankroll
python3 scripts/run_pipeline.py --bankroll 5000

# Save execution log
python3 scripts/run_pipeline.py --save-log

# Quiet mode (minimal output)
python3 scripts/run_pipeline.py --quiet --save-log

# LIVE mode (REAL MONEY - use with extreme caution!)
python3 scripts/run_pipeline.py --live
```

**Use Cases:**
- Manual pipeline execution
- Cron job automation
- Production monitoring
- Testing and validation

**Output:**
- Logs to stdout (unless --quiet)
- Optionally saves JSON log to `state/pipeline_logs/`

---

### `integration_demo_realdata.py` - Real Data Demo

Comprehensive demo showing the full pipeline with real market data:

```bash
python3 scripts/integration_demo_realdata.py
```

**Shows:**
- Model metadata (generation time, market counts)
- Top alpha signals with edge/confidence
- Planned actions with Kelly sizing
- Execution results with safety checks
- Summary statistics

**Use Cases:**
- Testing after changes
- Demonstrating the system
- Understanding the data flow

---

### `integration_demo.py` - Mock Data Demo

Legacy demo using mock/hardcoded data (no real market data required):

```bash
python3 scripts/integration_demo.py
```

**Use Cases:**
- Quick testing without market data
- CI/CD validation
- Demo when polymarket-compact.json unavailable

---

## Automation Examples

### Cron Job Setup

Run pipeline every 15 minutes:

```bash
# Edit crontab
crontab -e

# Add line:
*/15 * * * * cd /path/to/hands-off-engine && python3 scripts/run_pipeline.py --quiet --save-log
```

### Systemd Timer (Linux)

Create `/etc/systemd/system/hands-off-pipeline.service`:

```ini
[Unit]
Description=Hands-Off Engine Pipeline

[Service]
Type=oneshot
WorkingDirectory=/path/to/hands-off-engine
ExecStart=/usr/bin/python3 scripts/run_pipeline.py --quiet --save-log
User=your-user
```

Create `/etc/systemd/system/hands-off-pipeline.timer`:

```ini
[Unit]
Description=Run Hands-Off Engine Pipeline every 15 minutes

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable hands-off-pipeline.timer
sudo systemctl start hands-off-pipeline.timer
```

---

## Development Workflow

### Testing Changes

After making changes to Alpha, Decider, or Executor:

```bash
# 1. Run tests
python3 tests/test_alpha_pipeline.py

# 2. Run integration demo
python3 scripts/integration_demo_realdata.py

# 3. Dry-run full pipeline
python3 scripts/run_pipeline.py --save-log
```

### Before Going Live

Before switching to `--live` mode:

1. ✅ Ensure all tests pass
2. ✅ Review multiple DRYRUN executions
3. ✅ Verify safety reflexes are working (rejecting risky trades)
4. ✅ Check position sizing is reasonable
5. ✅ Have monitoring and alerts set up
6. ✅ Start with small bankroll
7. ✅ Have emergency stop mechanism ready

---

## Monitoring

### Check Pipeline Logs

```bash
# View latest log
ls -t state/pipeline_logs/*.json | head -1 | xargs cat | python3 -m json.tool

# Count successes/failures in last 24h
find state/pipeline_logs -name "*.json" -mtime -1 -exec jq -r '.success' {} \; | sort | uniq -c
```

### Alerts

Set up alerts for:
- Pipeline failures (`success: false` in log)
- No execution in expected timeframe
- Unusually high/low execution counts
- Safety reflex rejection rate changes

Example with Telegram:
```bash
# In run_pipeline.py or wrapper script
if ! python3 scripts/run_pipeline.py --quiet --save-log; then
    curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
        -d chat_id=<CHAT_ID> \
        -d text="⚠️ Hands-Off Pipeline failed!"
fi
```

---

## Safety Notes

🔴 **NEVER** run `--live` mode without:
- Extensive DRYRUN testing
- Understanding the code and risk model
- Monitoring and alerts in place
- Emergency stop procedure
- Starting with small amounts

🟡 **ALWAYS** use `--save-log` for:
- Production runs
- Troubleshooting
- Performance analysis
- Audit trail

🟢 **DEFAULT** is DRYRUN (safe) - no real money at risk
