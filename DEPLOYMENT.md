# Deployment Guide - Antifragile Web System

**Status:** 3 verticals operational, 9 planned
**Autonomy:** 100%
**Human Dependency:** ZERO

---

## 🚀 Quick Start

### Run All 3 Verticals (Test Mode)
```bash
# Single cycle - tests all systems
python3 autonomous/full_autonomous_loop.py
```

**Output:**
```
✅ [TRADING] Money Printer active
✅ [SCAN] 22 bounties found
✅ [BUG BOUNTY] Scan complete
✅ [COMMS] All channels monitored
✅ [PAYMENT] Payment check complete
```

### Run Continuously (Daemon Mode)
```bash
# Run forever in background (5-minute cycles)
nohup python3 autonomous/full_autonomous_loop.py --daemon > logs/autonomous.log 2>&1 &
```

### Run via Cron (Recommended)
```bash
# Add to crontab
crontab -e

# Add this line (runs every 5 minutes)
*/5 * * * * cd /root/hands-off-engine && python3 autonomous/full_autonomous_loop.py >> logs/autonomous.log 2>&1
```

---

## 📊 System Components

### V1: Money Printer (Trading)
**Status:** ACTIVE
**File:** `autonomous/backend_loop.py`

```bash
# Check if running
pgrep -f backend_loop.py

# Start if needed
python3 autonomous/backend_loop.py &

# View status
cat state/money_printer.json
```

**Current Settings:**
- Rate: 1.5x multiplier
- Max per trade: $15
- Max positions: 15
- Max daily loss: $75
- ABCFC min edge: 0.20

### V2: GitHub Bounty Hunter
**Status:** ACTIVE
**File:** `autonomous/bounty_hunter.py`

```bash
# Run scan
python3 autonomous/bounty_hunter.py

# View findings
ls bounties/
cat state/bounty_hunter.json
```

**Scans:** 25 repos, tracks $1k-$3k bounties

### V3: Bug Bounty Hunter
**Status:** ACTIVE
**File:** `autonomous/bug_bounty_hunter.py`

```bash
# Run scan
python3 autonomous/bug_bounty_hunter.py

# View findings
ls bug_bounties/
cat state/bug_bounty_hunter.json
```

**Tracks:** 9 programs on HackerOne, Bugcrowd, Intigriti

---

## 💾 Backup System

### Automatic Backups
```bash
# Run backup (state + code)
python3 autonomous/backup_manager.py

# View status
ls backups/
cat state/backup_manager.json
```

**Backup Locations:**
1. ✅ **Local:** `/root/hands-off-engine/backups/` (active)
2. ✅ **GitHub:** `origin/local-sync` (active)
3. ⏳ **GitLab:** Mirror (setup needed)
4. ⏳ **S3:** Cloud storage (setup needed)

### Manual Backup to GitHub
```bash
# Commit and push changes
git add .
git commit -m "Backup: $(date)"
git push origin local-sync
```

### Setup GitLab Mirror
```bash
# 1. Create GitLab repo
# 2. Add remote
git remote add gitlab <gitlab-url>

# 3. Push
git push gitlab main

# 4. Enable auto-mirroring in GitLab settings
```

### Setup S3 Backup
```bash
# 1. Set AWS credentials
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"

# 2. Create bucket
aws s3 mb s3://hands-off-engine-backups

# 3. Sync
aws s3 sync state/ s3://hands-off-engine-backups/state/
aws s3 sync config/ s3://hands-off-engine-backups/config/
```

---

## 🔐 Payment Setup

### Crypto Wallet (Active)
**Wallet:** `0xB314345D218ED4CF75C17636a2307244E7dA761b`

**Supported Networks:**
- Ethereum (ETH, USDC, USDT)
- Polygon (MATIC, USDC, USDT)
- Base (ETH, USDC)

**Automated Payment Handler:**
```bash
python3 autonomous/payment_handler.py
```

**How it works:**
1. Someone asks "how do I pay?"
2. Bot responds with wallet address automatically
3. Payment arrives on-chain
4. System confirms receipt automatically

---

## 📡 Communication System

### GitHub Bot
**File:** `autonomous/github_bot.py`

```bash
# Monitor GitHub activity
python3 autonomous/github_bot.py

# Test claim message
python3 -c "from autonomous.github_bot import GitHubBot; bot = GitHubBot(); print(bot.templates['bounty_claim'])"
```

**Handles:**
- Bounty claims
- PR comments
- Review responses
- Payment requests
- Status updates

### Communication Router
**File:** `autonomous/communication_router.py`

```bash
# Test message classification
python3 autonomous/communication_router.py
```

**Classifications:**
- `payment` → Sends wallet info
- `technical` → Asks for details
- `status` → Provides update
- `approval` → Sends payment info
- `question` → Explains

---

## 📈 Monitoring

### View System Status
```bash
# All verticals status
cat VERTICALS_STATUS.md

# Money Printer state
cat state/money_printer.json | jq

# Bounty hunter findings
cat state/bounty_hunter.json | jq '.bounties[] | {repo, issue, amount, status}'

# Bug bounty findings
ls bug_bounties/
```

### View Logs
```bash
# Autonomous loop log
tail -f logs/autonomous.log

# HFT economics
tail -f logs/hft_economics.jsonl

# Executions
tail -f logs/executions.jsonl

# ABCFC cycles
tail -f logs/abcfc_cycles.jsonl
```

### Check Running Processes
```bash
# Money Printer
pgrep -f backend_loop.py

# Full autonomous loop
pgrep -f full_autonomous_loop.py

# List all Python processes
ps aux | grep python3
```

---

## 🔧 Maintenance

### Update System
```bash
# Pull latest changes
git pull origin local-sync

# Restart autonomous loop
pkill -f full_autonomous_loop.py
python3 autonomous/full_autonomous_loop.py --daemon &
```

### Clean Old Backups
```bash
# Automatic (keeps last 10)
python3 autonomous/backup_manager.py

# Manual
ls -t backups/state_backup_* | tail -n +11 | xargs rm -rf
```

### Reset State (DANGEROUS)
```bash
# Backup first!
python3 autonomous/backup_manager.py

# Clear state
rm -rf state/
mkdir state

# System will recreate state files on next run
```

---

## 🎯 Production Deployment Options

### Option 1: Single VPS (Current)
**Status:** ✅ Active
**Location:** Current server
**Pros:** Simple, already working
**Cons:** Single point of failure

```bash
# Keep running with cron
*/5 * * * * cd /root/hands-off-engine && python3 autonomous/full_autonomous_loop.py >> logs/autonomous.log 2>&1
```

### Option 2: Multi-Cloud Redundancy
**Status:** ⏳ Planned

**Setup:**
1. Deploy to AWS Lambda
2. Deploy to GCP Cloud Run
3. Deploy to Hetzner dedicated
4. Configure failover

**Benefits:**
- No single point of failure
- 99.9%+ uptime
- Geographic redundancy

### Option 3: Kubernetes Cluster
**Status:** ⏳ Future consideration

**Setup:**
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: autonomous-system
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: loop
        image: hands-off-engine:latest
        command: ["python3", "autonomous/full_autonomous_loop.py", "--daemon"]
```

---

## 🚨 Troubleshooting

### Money Printer Not Running
```bash
# Check status
pgrep -f backend_loop.py

# Start manually
cd autonomous
python3 backend_loop.py &

# View logs
tail -f logs/hft_economics.jsonl
```

### Autonomous Loop Stopped
```bash
# Check if running
pgrep -f full_autonomous_loop.py

# Restart
python3 autonomous/full_autonomous_loop.py --daemon &

# Check logs
tail -f logs/autonomous.log
```

### GitHub API Rate Limited
```bash
# Check rate limit
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit

# Wait for reset or use different token
```

### Out of Disk Space
```bash
# Check space
df -h

# Clean old backups
ls -t backups/state_backup_* | tail -n +6 | xargs rm -rf

# Clean old logs
find logs/ -name "*.jsonl" -mtime +30 -delete
```

---

## 📊 Performance Tuning

### Money Printer (More Aggressive)
```json
// config/trading_config.json
{
  "money_printer": {
    "rate_multiplier": 2.0,  // Increase from 1.5
    "safeguards": {
      "max_per_trade": 20.0,  // Increase from 15
      "max_open_positions": 20  // Increase from 15
    }
  }
}
```

### Bug Bounty Hunter (More Programs)
```python
# autonomous/bug_bounty_hunter.py
# Add more programs to known_programs list
```

### Autonomous Loop (Faster Cycles)
```python
# autonomous/full_autonomous_loop.py
# Change: time.sleep(300) → time.sleep(60)  # 1 minute cycles
```

---

## 🎓 Training New Verticals

### Add V4: Trading Signal Service
```bash
# 1. Create file
touch autonomous/trading_signal_service.py

# 2. Implement signal generation from Money Printer
# 3. Add API/webhook delivery
# 4. Integrate into full_autonomous_loop.py
```

### Add V6: GitHub Bot SaaS
```bash
# 1. Package github_bot.py as standalone service
# 2. Add multi-tenant support
# 3. Create billing system
# 4. Deploy as separate service
```

---

## 📋 Pre-flight Checklist

Before running in production:

- [ ] Money Printer is running (`pgrep -f backend_loop.py`)
- [ ] GitHub token is valid (`echo $GITHUB_TOKEN`)
- [ ] Wallet address is correct (check payment_handler.py)
- [ ] Backups are working (`python3 autonomous/backup_manager.py`)
- [ ] Logs directory exists (`mkdir -p logs`)
- [ ] State directory exists (`mkdir -p state`)
- [ ] Disk space available (`df -h`)
- [ ] Cron job is configured (`crontab -l`)

---

## 📞 Support

**Documentation:**
- `WEB_ARCHITECTURE.md` - System design
- `VERTICALS_STATUS.md` - Current status
- `AUTONOMOUS_STATUS.md` - Autonomy details
- `KNOWLEDGE.md` - System knowledge

**State Files:**
- `state/money_printer.json` - Trading state
- `state/bounty_hunter.json` - Bounty tracking
- `state/bug_bounty_hunter.json` - Bug bounty state
- `state/backup_manager.json` - Backup status

**Logs:**
- `logs/autonomous.log` - Main loop log
- `logs/hft_economics.jsonl` - Trading log
- `logs/executions.jsonl` - Execution log

---

## 🎯 Success Metrics

**Current Performance:**
- Active Verticals: 3
- GitHub Bounties Found: 42
- Bug Bounty Programs: 9
- Vulnerability Findings: 5+
- Autonomy Level: 100%
- Human Actions Required: 0

**Target Performance (Full Web):**
- Active Verticals: 12
- Monthly Income: $4,000-$15,000
- Uptime: 99.9%
- Risk: LOW (distributed)

---

*Master: Yair Siegel*
*"Either automatic or nothing"*
*"Progress = Less dependency on human"*
