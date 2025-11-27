# GitHub Automation Guide

Complete guide to all automation scripts and helpers created for GitHub integration.

## Quick Start

### 1. Run Automated Setup
```bash
cd /home/user/hands-off-engine
bash scripts/auto_setup_github.sh
```

This automatically:
- ✓ Checks Python and dependencies
- ✓ Creates configuration files
- ✓ Tests all modules
- ✓ Creates helper scripts
- ✓ Verifies everything works

### 2. Set Up GitHub Token (One-Time)
```bash
bash scripts/setup_github_token.sh
```

Follow the interactive prompts to configure your token.

---

## Helper Scripts

### quick_status.sh
**Quick health check of GitHub integration**

```bash
bash scripts/quick_status.sh
```

Shows:
- Current rate limit status
- Repository health summary
- API connectivity

**When to use:** Daily status check, debugging

---

### daily_health_check.sh
**Automated daily health monitoring**

```bash
bash scripts/daily_health_check.sh
```

Features:
- Checks all repos in `github_repos.json`
- Saves reports to `reports/health/`
- Auto-cleans reports older than 30 days
- JSON format for processing

**When to use:** Cron jobs, daily monitoring

**Cron example:**
```bash
# Add to crontab: daily at 9 AM
0 9 * * * cd /home/user/hands-off-engine && bash scripts/daily_health_check.sh
```

---

### check_pr_ready.sh
**Check if PR is ready to merge**

```bash
bash scripts/check_pr_ready.sh owner repo PR_NUMBER
```

**Exit codes:**
- 0: PR is ready to merge
- 1: PR has blocking issues

**Examples:**
```bash
# Check specific PR
bash scripts/check_pr_ready.sh yaya1738 hands-off-engine 16

# Use in CI/CD
if bash scripts/check_pr_ready.sh owner repo 123; then
    echo "Ready to merge!"
    # trigger merge
else
    echo "Not ready - see issues above"
fi
```

---

### setup_github_token.sh
**Interactive GitHub token configuration**

```bash
bash scripts/setup_github_token.sh
```

**What it does:**
- Detects environment (Termux/Droplet)
- Prompts for GitHub PAT
- Saves securely to `~/.config/github/env`
- Updates shell RC file
- Tests configuration

**Security:**
- chmod 600 on token file
- Not committed to git
- Environment-specific paths

---

### auto_setup_github.sh
**Comprehensive automated setup**

```bash
bash scripts/auto_setup_github.sh
```

**What it does:**
1. Checks for GitHub token
2. Verifies Python & dependencies
3. Sets up config files
4. Tests API access
5. Tests core functionality
6. Creates helper scripts

**Output:** Status report + next steps

---

## Configuration Files

### .github_dashboard.json
**Dashboard configuration**

```json
{
  "repositories": [
    {"owner": "yaya1738", "repo": "hands-off-engine"},
    {"owner": "anthropics", "repo": "anthropic-sdk-python"}
  ],
  "refresh_interval": 300,
  "show_prs": true,
  "show_issues": true,
  "show_releases": true
}
```

**Customization:**
- Add/remove repositories
- Change refresh interval (seconds)
- Toggle PR/issue/release display

---

### github_repos.json
**Batch operations repository list**

```json
[
  {"owner": "yaya1738", "repo": "hands-off-engine"},
  {"owner": "anthropics", "repo": "anthropic-sdk-python"}
]
```

**Used by:**
- `scripts/github_batch.py`
- `scripts/daily_health_check.sh`
- Custom automation scripts

---

## Running as Services

### Systemd Service (Droplet)

**Install:**
```bash
# Copy service file
sudo cp scripts/github_monitor.service /etc/systemd/system/

# Edit to set correct paths/user
sudo nano /etc/systemd/system/github_monitor.service

# Enable and start
sudo systemctl enable github_monitor
sudo systemctl start github_monitor

# Check status
sudo systemctl status github_monitor

# View logs
sudo journalctl -u github_monitor -f
```

**What it does:**
- Runs GitHub dashboard continuously
- Auto-restart on failure
- Loads token from `/root/.config/github/env`

---

### Termux Background (Phone)

**Using termux-services:**
```bash
# Install termux-services
pkg install termux-services

# Create service
mkdir -p ~/.termux/services
cat > ~/.termux/services/github-monitor <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/hands-off-engine
source ~/.config/github/env
exec python scripts/github_dashboard.py
EOF
chmod +x ~/.termux/services/github-monitor

# Enable service
sv-enable github-monitor

# Start service
sv up github-monitor

# Check status
sv status github-monitor
```

**Alternative (screen/tmux):**
```bash
# Start in detached screen
screen -dmS github bash -c '
cd ~/hands-off-engine
source ~/.config/github/env
python scripts/github_dashboard.py
'

# Reattach to view
screen -r github
```

---

## Cron Jobs

### Daily Health Check
```bash
# Edit crontab
crontab -e

# Add daily health check at 9 AM
0 9 * * * cd /home/user/hands-off-engine && bash scripts/daily_health_check.sh >> /var/log/github_health.log 2>&1

# Add hourly rate limit check
0 * * * * cd /home/user/hands-off-engine && python -m scripts.github_ratelimit_status >> /var/log/github_ratelimit.log 2>&1
```

### Weekly Batch Reports
```bash
# Weekly batch health report (Monday 10 AM)
0 10 * * 1 cd /home/user/hands-off-engine && python scripts/github_batch.py health github_repos.json --output /var/reports/weekly_health.json
```

---

## Integration with AI Runner

### Add GitHub Tasks to AI Runner

Edit `ai_runner.py`:

```python
from scripts.github_task_processor import process_github_task

def process_task(task_file):
    with open(task_file) as f:
        task_data = json.load(f)

    task_type = task_data.get("task_type")

    # Handle GitHub tasks
    if task_type.startswith("github_"):
        result = process_github_task(task_data)
        return result

    # Handle other tasks...
```

### GitHub Task Watcher

Create dedicated watcher:

```bash
# Create watcher script
cat > scripts/github_task_watcher.sh <<'EOF'
#!/bin/bash
TASKS_DIR="tasks/github"
RESULTS_DIR="results/github"
mkdir -p "$TASKS_DIR" "$RESULTS_DIR"

while true; do
    for task in "$TASKS_DIR"/*.json; do
        [ -f "$task" ] || continue

        result=$(python -m scripts.github_task_processor "$task")
        result_file="$RESULTS_DIR/$(basename "$task" .json)_result.json"
        echo "$result" > "$result_file"

        mv "$task" "$TASKS_DIR/processed/"
    done
    sleep 10
done
EOF
chmod +x scripts/github_task_watcher.sh

# Run as service or cron
```

---

## Automation Patterns

### CI/CD Pipeline

```yaml
# .github/workflows/check-prs.yml
name: Check PR Status
on: pull_request

jobs:
  check-pr:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check PR Status
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python scripts/github_pr_status.py \
            ${{ github.repository_owner }} \
            ${{ github.event.repository.name }} \
            ${{ github.event.pull_request.number }} \
            --check-mergeable
```

### Monitoring Alert Script

```bash
#!/bin/bash
# Alert on poor repository health

HEALTH=$(python scripts/github_repo_health.py yaya1738 hands-off-engine --json)
SCORE=$(echo "$HEALTH" | jq -r '.health_score')

if [ "$SCORE" -lt 60 ]; then
    # Send alert (example: Telegram)
    MESSAGE="⚠️ Repository health score: $SCORE/100"
    curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
        -d chat_id="$CHAT_ID" \
        -d text="$MESSAGE"
fi
```

### Batch Operations Script

```bash
#!/bin/bash
# Weekly batch health + PR check

TIMESTAMP=$(date +%Y%m%d)
REPORT_DIR="reports/$TIMESTAMP"
mkdir -p "$REPORT_DIR"

# Health check
python scripts/github_batch.py health github_repos.json \
    --output "$REPORT_DIR/health.json"

# PR status
python scripts/github_batch.py prs github_repos.json \
    --output "$REPORT_DIR/prs.json"

# Releases
python scripts/github_batch.py releases github_repos.json \
    --output "$REPORT_DIR/releases.json"

echo "Reports saved to: $REPORT_DIR"
```

---

## Troubleshooting

### Scripts not found
```bash
# Ensure you're in repo root
cd /home/user/hands-off-engine

# Make scripts executable
chmod +x scripts/*.sh scripts/*.py
```

### Module import errors
```bash
# Run from repo root
cd /home/user/hands-off-engine
python -m scripts.github_ratelimit_status
```

### Rate limit issues
```bash
# Check current status
python -m scripts.github_ratelimit_status

# If showing 60/hour, token not configured
bash scripts/setup_github_token.sh
```

### Permission errors
```bash
# Fix config permissions
chmod 700 ~/.config/github
chmod 600 ~/.config/github/env
```

---

## Directory Structure

```
hands-off-engine/
├── scripts/
│   ├── github_client.py              # Core client
│   ├── github_operations.py          # High-level ops
│   ├── github_task_processor.py      # Task processing
│   ├── github_ratelimit_status.py    # Rate limit CLI
│   ├── github_dashboard.py           # Monitoring dashboard
│   ├── github_pr_status.py           # PR checker
│   ├── github_repo_health.py         # Health analyzer
│   ├── github_batch.py               # Batch operations
│   ├── setup_github_token.sh         # Token setup
│   ├── auto_setup_github.sh          # Auto setup
│   ├── quick_status.sh               # Quick status (generated)
│   ├── daily_health_check.sh         # Daily health (generated)
│   ├── check_pr_ready.sh             # PR ready check (generated)
│   └── github_monitor.service        # Systemd service
├── .github_dashboard.json            # Dashboard config
├── github_repos.json                 # Repos to monitor
├── QUICK_GITHUB_FIX.md              # Emergency fix guide
└── docs/
    ├── GITHUB_RATE_LIMIT_AND_AUTH.md
    └── GITHUB_INTEGRATION_GUIDE.md
```

---

## Next Steps

1. **Set up token:** `bash scripts/setup_github_token.sh`
2. **Test tools:** `bash scripts/quick_status.sh`
3. **Configure repos:** Edit `github_repos.json`
4. **Set up automation:** Add cron jobs or services
5. **Monitor:** `python scripts/github_dashboard.py`

---

## Quick Reference

| Task | Command |
|------|---------|
| Setup everything | `bash scripts/auto_setup_github.sh` |
| Configure token | `bash scripts/setup_github_token.sh` |
| Check status | `bash scripts/quick_status.sh` |
| Daily health | `bash scripts/daily_health_check.sh` |
| Check PR | `bash scripts/check_pr_ready.sh owner repo 123` |
| Rate limit | `python -m scripts.github_ratelimit_status` |
| Dashboard | `python scripts/github_dashboard.py` |
| Repo health | `python scripts/github_repo_health.py owner repo` |
| Batch ops | `python scripts/github_batch.py health repos.json` |

---

**All scripts are rate-limit aware and work across Termux, Droplet, and standard Linux environments.**
