# Fault-Tolerant Infrastructure

This directory contains the fault-tolerant, self-healing infrastructure for the Hands-Off Engine, designed to enable 24/7 autonomous operation with minimal user intervention.

## Quick Start

```bash
# Install everything
cd /home/user/hands-off-engine/infrastructure
./install.sh

# Check health
python3 health_monitor.py

# View self-healing status
python3 selfheal.py --status

# Create backup
python3 backup_manager.py --create
```

## Components

### 1. Resilience Patterns (`resilience.py`)

Provides decorators and utilities for fault-tolerant operations:

- **Retry with exponential backoff**: Automatically retry failed operations
- **Circuit breaker**: Prevent cascading failures
- **Timeout guards**: Enforce timeouts on operations
- **Rate limiting**: Control request rates

**Example Usage:**

```python
from infrastructure.resilience import retry, circuit_breaker, timeout

@retry(max_attempts=4, backoff=[2, 4, 8, 16])
@circuit_breaker("polymarket_api", failure_threshold=5, cooldown=300)
@timeout(30)
def fetch_polymarket_data():
    return api.get_markets()
```

**Features:**
- ✅ Automatic retry with configurable backoff
- ✅ Circuit breaker with CLOSED/OPEN/HALF_OPEN states
- ✅ Thread-based timeout enforcement
- ✅ Token bucket rate limiting
- ✅ Structured logging for all actions
- ✅ Global circuit breaker registry

**Testing:**
```bash
python3 resilience.py
```

### 2. Self-Healing Controller (`selfheal.py`)

Automatically detects and remediates failures:

- **Service monitoring**: Checks for stale state files
- **Automatic restarts**: Restarts failed services
- **Disk cleanup**: Removes old files when space is low
- **State recovery**: Restores corrupted files from backups
- **Lock cleanup**: Removes stale lock files

**Built-in Healing Actions:**

| Action | Check | Heal | Cooldown |
|--------|-------|------|----------|
| restart_stale_orchestrator | master.json age > 45 min | Restart orchestrator | 15 min |
| restart_stale_finance_watcher | finance.json age > 60 min | Restart finance watcher | 15 min |
| restart_stale_executor | execution_plan.json age > 30 min | Restart executor | 30 min |
| cleanup_disk_space | Free space < 5 GB | Delete old files | 60 min |
| fix_corrupted_state | Invalid JSON files | Restore from backup | 10 min |
| clear_stale_locks | Lock files > 60 min old | Remove locks | 5 min |

**Usage:**

```bash
# Run continuously (daemon mode)
python3 selfheal.py

# Run once and exit
python3 selfheal.py --once

# Show status
python3 selfheal.py --status

# Force heal specific service (ignore cooldown)
python3 selfheal.py --force --service=orchestrator

# Use custom config
python3 selfheal.py --config=/path/to/config.json
```

**Configuration:**

Create `selfheal_config.json`:

```json
{
  "check_interval": 60,
  "staleness_thresholds": {
    "master_json": 2700,
    "finance_json": 3600,
    "execution_plan": 1800
  },
  "restart_commands": {
    "orchestrator": "systemctl restart hands-off-orchestrator"
  },
  "disk_cleanup": {
    "min_free_gb": 5,
    "cleanup_patterns": ["/var/log/*.old"],
    "max_backup_age_days": 30
  }
}
```

### 3. Health Monitor (`health_monitor.py`)

Comprehensive system health monitoring:

- **Service checks**: State file freshness, cron jobs
- **Resource checks**: CPU, memory, disk usage
- **API checks**: Admin server, Polymarket API, network
- **Log analysis**: Recent errors and warnings

**Health Checks:**

| Check | Status Levels | Description |
|-------|--------------|-------------|
| master_json | HEALTHY / DEGRADED / UNHEALTHY | Orchestrator state freshness |
| finance_json | HEALTHY / DEGRADED / UNHEALTHY | Finance watcher freshness |
| execution_plan | HEALTHY / DEGRADED / UNHEALTHY | Executor plan freshness |
| cron_jobs | HEALTHY / DEGRADED / UNHEALTHY | Cron configuration |
| cpu_usage | HEALTHY / DEGRADED | CPU utilization |
| memory_usage | HEALTHY / DEGRADED | Memory utilization |
| disk_usage | HEALTHY / UNHEALTHY | Disk space |
| admin_server | HEALTHY / DEGRADED / UNHEALTHY | HTTP endpoint health |
| polymarket_api | HEALTHY / DEGRADED / UNHEALTHY | External API health |
| network_connectivity | HEALTHY / UNHEALTHY | General network |
| recent_errors | HEALTHY / DEGRADED / UNHEALTHY | Log error count |

**Usage:**

```bash
# Single check
python3 health_monitor.py

# Watch mode (updates every 60 seconds)
python3 health_monitor.py --watch 60

# JSON output
python3 health_monitor.py --json

# Custom config
python3 health_monitor.py --config=/path/to/config.json
```

**Exit Codes:**
- `0`: HEALTHY
- `1`: DEGRADED
- `2`: UNHEALTHY

**Example Output:**

```
Health Check - 2025-11-21T10:30:45
Overall Status: HEALTHY

  master_json: healthy - Fresh: 12 minutes old
  finance_json: healthy - Fresh: 25 minutes old
  execution_plan: healthy - Fresh: 15 minutes old, 3 orders
  cron_jobs: healthy - All 3 cron jobs configured
  cpu_usage: healthy - CPU usage: 23.5%
  memory_usage: healthy - Memory usage: 45.2%
  disk_usage: healthy - Disk usage: 42.1% (28 GB free)
  admin_server: healthy - Admin server responding (200)
  polymarket_api: healthy - Polymarket API reachable (200)
  network_connectivity: healthy - Network connectivity OK
  recent_errors: healthy - No recent errors (2 warnings)

Summary: {'total_checks': 11, 'healthy': 11, 'degraded': 0, 'unhealthy': 0}
```

### 4. Backup Manager (`backup_manager.py`)

Automated backup and recovery system:

- **Automatic backups**: Scheduled state file backups
- **Verification**: Checksum validation
- **Retention policies**: Hourly, daily, weekly, monthly
- **Cloud upload**: S3, Backblaze B2, rsync
- **Point-in-time recovery**: Restore any backup

**Features:**
- ✅ Incremental and full backups
- ✅ SHA256 checksum verification
- ✅ Automatic cleanup by retention policy
- ✅ Cloud storage integration
- ✅ Dry-run restore mode
- ✅ Backup metadata tracking

**Usage:**

```bash
# Create backup
python3 backup_manager.py --create

# List backups
python3 backup_manager.py --list

# Verify backup
python3 backup_manager.py --verify 20251121_103045

# Restore backup (dry run)
python3 backup_manager.py --restore 20251121_103045 --dry-run

# Restore backup (actual)
python3 backup_manager.py --restore 20251121_103045

# Clean up old backups
python3 backup_manager.py --cleanup

# Show backup status
python3 backup_manager.py --status
```

**Retention Policy:**

| Period | Count | Interval |
|--------|-------|----------|
| Hourly | 24 | Every 1 hour |
| Daily | 30 | Every 1 day |
| Weekly | 12 | Every 7 days |
| Monthly | 12 | Every 30 days |

## Deployment Options

### Option A: Systemd Services

**Pros:**
- Native Linux integration
- Automatic startup
- Resource management
- Integrated logging

**Installation:**
```bash
sudo cp systemd/*.service /etc/systemd/system/
sudo cp systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hands-off-selfheal hands-off-health-monitor
sudo systemctl enable --now hands-off-pipeline.timer
```

**Management:**
```bash
# Status
sudo systemctl status hands-off-selfheal
sudo systemctl status hands-off-health-monitor

# Logs
sudo journalctl -u hands-off-selfheal -f
sudo journalctl -u hands-off-health-monitor -f

# Restart
sudo systemctl restart hands-off-selfheal

# Stop
sudo systemctl stop hands-off-selfheal
```

### Option B: Docker Compose

**Pros:**
- Containerized isolation
- Easy scaling
- Portable deployment
- Consistent environment

**Installation:**
```bash
cd infrastructure
docker-compose build
docker-compose up -d
```

**Management:**
```bash
# Status
docker-compose ps

# Logs
docker-compose logs -f selfheal
docker-compose logs -f health-monitor

# Restart
docker-compose restart selfheal

# Stop
docker-compose down
```

**Optional Monitoring Stack:**
```bash
# Start Prometheus + Grafana + Loki
docker-compose --profile monitoring up -d
```

Access:
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Admin API: http://localhost:8787

### Option C: Hybrid

Add infrastructure to existing setup without changing deployment:

```bash
# Install monitoring only
sudo systemctl enable --now hands-off-selfheal hands-off-health-monitor

# Keep existing cron jobs
# Self-healing will monitor and restart as needed
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Docker     │  │   systemd    │  │  Supervisor  │      │
│  │  Compose     │  │   Services   │  │    (PM)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Self-Healing Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Health     │  │   Self-Heal  │  │   Circuit    │     │
│  │   Monitor    │  │  Controller  │  │   Breakers   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Application Services                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │   Alpha    │  │  Decider   │  │  Executor  │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

See `docs/FAULT_TOLERANT_ARCHITECTURE.md` for detailed architecture.

## Configuration Files

### `selfheal_config.json`
```json
{
  "check_interval": 60,
  "staleness_thresholds": {...},
  "restart_commands": {...},
  "disk_cleanup": {...}
}
```

### `health_config.json`
```json
{
  "staleness_thresholds": {...},
  "resource_thresholds": {...},
  "api_endpoints": {...}
}
```

### `.env`
```bash
ADMIN_TOKEN=your-secure-token
GRAFANA_PASSWORD=your-password
TELEGRAM_BOT_TOKEN=your-bot-token
```

## Monitoring & Alerts

### Built-in Alerts

Self-healing controller sends alerts on:
- Service restarts
- Disk cleanup
- State recovery
- Emergency pause

Configure alert channels in existing notification system (Telegram, IFTTT).

### External Monitoring

Integrate with external services:

**Healthchecks.io:**
```bash
# Add to cron or systemd timer
curl -fsS --retry 3 https://hc-ping.com/YOUR-UUID-HERE
```

**UptimeRobot:**
- Monitor: http://your-server:8787/health
- Check interval: 5 minutes

**Custom Webhook:**
```python
import requests
health = monitor.run_all_checks()
requests.post("https://your-webhook.com", json=health)
```

## Performance Tuning

### Reduce Check Frequency

For lower-resource systems:

```json
{
  "check_interval": 120,  // 2 minutes instead of 1
}
```

### Adjust Thresholds

Allow longer staleness:

```json
{
  "staleness_thresholds": {
    "master_json": 5400,  // 90 minutes instead of 45
  }
}
```

### Disable Specific Checks

Comment out checks in `health_monitor.py` or `selfheal.py`.

## Troubleshooting

### Services Keep Restarting

**Symptom**: Self-heal restarts service repeatedly

**Solution:**
```bash
# Check why service is failing
sudo journalctl -u hands-off-orchestrator -n 100

# Temporarily increase threshold
# Edit selfheal_config.json, increase staleness_thresholds

# Or disable that healing action
python3 selfheal.py --status
# Edit selfheal.py to comment out the problematic action
```

### High False Alert Rate

**Symptom**: Too many alerts for normal operation

**Solution:**
```bash
# Tune thresholds in health_config.json
# Increase staleness_thresholds
# Increase resource_thresholds

# Or increase cooldown periods in selfheal_config.json
```

### Backups Filling Disk

**Symptom**: Backup directory growing too large

**Solution:**
```bash
# Run cleanup
python3 backup_manager.py --cleanup

# Adjust retention policy
# Edit backup_config.json, reduce retention counts

# Enable cloud backup to offload old backups
```

### Circuit Breaker Always Open

**Symptom**: API calls always fail with "Circuit breaker OPEN"

**Solution:**
```bash
# Check if API is actually down
curl -I https://clob.polymarket.com/

# Restart service to reset circuit breakers
sudo systemctl restart hands-off-orchestrator

# Adjust circuit breaker thresholds in code
# Edit failure_threshold or cooldown in resilience.py decorators
```

## Testing

### Test Self-Healing

```bash
# Simulate stale service (stop updating master.json)
sudo systemctl stop hands-off-orchestrator

# Wait 2-3 minutes
# Self-heal should detect and restart

# Check logs
sudo journalctl -u hands-off-selfheal -n 20
```

### Test Health Monitoring

```bash
# Run single check
python3 health_monitor.py

# Should show any issues

# Simulate disk full
# Self-heal should trigger cleanup
```

### Test Backups

```bash
# Create test backup
python3 backup_manager.py --create

# Verify it
python3 backup_manager.py --verify $(python3 backup_manager.py --list | head -1 | cut -d' ' -f1)

# Test restore (dry run)
python3 backup_manager.py --restore BACKUP_ID --dry-run
```

## Security

### Credentials

Store sensitive data securely:
- Use environment variables in `.env`
- Never commit secrets to git
- Use encrypted storage for API keys

### Access Control

- Restrict access to admin API (token-based auth)
- Use firewall rules for ports
- Run services as non-root user
- Enable systemd security features (PrivateTmp, ProtectSystem)

### Audit Logs

All actions are logged:
```bash
# View self-healing actions
sudo journalctl -u hands-off-selfheal | grep healing_action

# View backup operations
python3 backup_manager.py --list
```

## Maintenance

### Daily
- Quick health check: `python3 health_monitor.py`
- Review alerts: Check Telegram/email

### Weekly
- Review logs: `sudo journalctl -u hands-off-selfheal -n 500`
- Check disk usage: `df -h`
- Verify latest backup: `python3 backup_manager.py --status`

### Monthly
- Update dependencies: `pip3 install --upgrade -r requirements.txt`
- Review performance: Check resource usage trends
- Test restore: Restore a backup to test directory
- Rotate logs: `sudo journalctl --vacuum-time=30d`

## Documentation

- **Architecture**: `docs/FAULT_TOLERANT_ARCHITECTURE.md`
- **Installation**: `INSTALLATION.md`
- **API Reference**: Code docstrings
- **Examples**: See code comments

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u hands-off-*`
2. Review configuration
3. See troubleshooting section above
4. Check main project README

---

**Version**: 1.0.0
**Last Updated**: 2025-11-21
**License**: Same as main project
