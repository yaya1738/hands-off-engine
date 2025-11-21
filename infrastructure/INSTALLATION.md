# Fault-Tolerant Infrastructure Installation Guide

This guide covers installation and deployment of the fault-tolerant, self-healing infrastructure for the Hands-Off Engine.

## Prerequisites

### System Requirements
- Linux server (Ubuntu 20.04+, Debian 11+, or similar)
- 2+ CPU cores
- 4+ GB RAM
- 20+ GB disk space
- Python 3.9+
- sudo/root access

### Software Dependencies
- Python 3.9+ with pip
- Docker and Docker Compose (for containerized deployment)
- systemd (for service deployment)
- git
- curl

## Installation Options

Choose one of the following deployment methods:

### Option A: Systemd Services (Recommended for VPS/Dedicated Servers)

#### 1. Install Python Dependencies

```bash
cd /home/user/hands-off-engine

# Install required Python packages
pip3 install --user -r requirements.txt
pip3 install --user structlog psutil requests
```

#### 2. Install Systemd Services

```bash
# Copy service files to systemd directory
sudo cp infrastructure/systemd/*.service /etc/systemd/system/
sudo cp infrastructure/systemd/*.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable hands-off-selfheal
sudo systemctl enable hands-off-health-monitor
sudo systemctl enable hands-off-pipeline.timer

# Start services
sudo systemctl start hands-off-selfheal
sudo systemctl start hands-off-health-monitor
sudo systemctl start hands-off-pipeline.timer
```

#### 3. Verify Services

```bash
# Check service status
sudo systemctl status hands-off-selfheal
sudo systemctl status hands-off-health-monitor

# Check timer status
sudo systemctl list-timers hands-off-pipeline.timer

# View logs
sudo journalctl -u hands-off-selfheal -f
sudo journalctl -u hands-off-health-monitor -f
```

#### 4. Create Log Directory

```bash
sudo mkdir -p /var/log/hands-off-engine
sudo chown user:user /var/log/hands-off-engine
```

### Option B: Docker Compose (Recommended for Cloud/Containerized Deployments)

#### 1. Install Docker and Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. Build and Start Containers

```bash
cd /home/user/hands-off-engine/infrastructure

# Build images
docker-compose build

# Start core services
docker-compose up -d selfheal health-monitor orchestrator admin-server

# Optional: Start monitoring stack
docker-compose --profile monitoring up -d
```

#### 3. Verify Containers

```bash
# Check running containers
docker-compose ps

# View logs
docker-compose logs -f selfheal
docker-compose logs -f health-monitor

# Check health status
docker-compose exec health-monitor python3 /app/infrastructure/health_monitor.py --json
```

#### 4. Schedule Pipeline Execution

Since the pipeline needs to run on a schedule, set up a cron job or systemd timer on the host:

**Using cron:**
```bash
crontab -e

# Add this line to run pipeline every hour
0 * * * * cd /home/user/hands-off-engine/infrastructure && docker-compose run --rm pipeline >> /var/log/hands-off-engine/pipeline.log 2>&1
```

**Using systemd timer (preferred):**
```bash
# Create timer service on host
sudo cp systemd/hands-off-pipeline-docker.service /etc/systemd/system/
sudo cp systemd/hands-off-pipeline.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hands-off-pipeline.timer
```

### Option C: Hybrid Deployment (Existing Setup + New Infrastructure)

Keep your existing cron-based setup but add the fault-tolerance layer:

#### 1. Install Infrastructure Services Only

```bash
# Install Python dependencies
pip3 install --user structlog psutil requests

# Start self-healing and health monitoring
sudo systemctl enable --now hands-off-selfheal
sudo systemctl enable --now hands-off-health-monitor
```

#### 2. Keep Existing Cron Jobs

Your existing cron jobs will continue to work. The self-healing service will monitor them and restart if needed.

#### 3. Update Existing Scripts (Optional)

Add resilience patterns to existing Python scripts:

```python
# Add to top of existing scripts
import sys
sys.path.insert(0, '/home/user/hands-off-engine')

from infrastructure.resilience import retry, circuit_breaker, timeout

# Wrap API calls with resilience patterns
@retry(max_attempts=4, backoff=[2, 4, 8, 16])
@circuit_breaker("polymarket_api", failure_threshold=5, cooldown=300)
@timeout(30)
def fetch_polymarket_data():
    # Your existing code
    pass
```

## Configuration

### 1. Self-Healing Configuration

Create `/home/user/hands-off-engine/infrastructure/selfheal_config.json`:

```json
{
  "check_interval": 60,
  "state_dir": "/home/user/hands-off-engine/state",
  "termux_state_dir": "/home/user/hands-off-engine/termux-hands-off/state",
  "staleness_thresholds": {
    "master_json": 2700,
    "finance_json": 3600,
    "execution_plan": 1800
  },
  "restart_commands": {
    "orchestrator": "systemctl restart hands-off-orchestrator || docker restart hands-off-orchestrator",
    "executor": "systemctl restart hands-off-executor || true",
    "finance_watcher": "systemctl restart hands-off-finance-watcher || true"
  },
  "disk_cleanup": {
    "min_free_gb": 5,
    "cleanup_patterns": [
      "/var/log/hands-off-engine/*.log.old",
      "/tmp/hands-off-*",
      "/home/user/hands-off-engine/state/*.bak.*"
    ],
    "max_backup_age_days": 30
  },
  "max_consecutive_failures": 3,
  "emergency_pause_on_failures": true
}
```

### 2. Health Monitor Configuration

Create `/home/user/hands-off-engine/infrastructure/health_config.json`:

```json
{
  "state_dir": "/home/user/hands-off-engine/state",
  "termux_state_dir": "/home/user/hands-off-engine/termux-hands-off/state",
  "staleness_thresholds": {
    "master_json": 2700,
    "finance_json": 3600,
    "execution_plan": 1800
  },
  "resource_thresholds": {
    "cpu_percent": 90,
    "memory_percent": 85,
    "disk_percent": 90
  },
  "api_endpoints": {
    "admin_server": "http://localhost:8787/health",
    "polymarket_api": "https://clob.polymarket.com/"
  },
  "timeout_seconds": 10
}
```

### 3. Environment Variables

Create `/home/user/hands-off-engine/infrastructure/.env`:

```bash
# Admin API
ADMIN_TOKEN=your-secure-random-token-here

# Monitoring (if using Grafana)
GRAFANA_PASSWORD=your-secure-password-here

# Alerts
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id

# Log level
LOG_LEVEL=INFO
```

## Testing the Installation

### 1. Run Manual Health Check

```bash
cd /home/user/hands-off-engine

# Check system health
python3 infrastructure/health_monitor.py

# Expected output: Overall status and individual check results
```

### 2. Test Self-Healing (Dry Run)

```bash
# Check what would be healed
python3 infrastructure/selfheal.py --once

# Force heal a specific service (for testing)
python3 infrastructure/selfheal.py --force --service=orchestrator
```

### 3. Test Resilience Patterns

```bash
# Run test suite in resilience.py
python3 infrastructure/resilience.py

# Expected output: Test results for retry, circuit breaker, and timeout
```

### 4. Simulate Failure

```bash
# Stop a service to test auto-restart
sudo systemctl stop hands-off-orchestrator

# Wait 1-2 minutes and check if self-heal restarted it
sudo systemctl status hands-off-orchestrator
sudo journalctl -u hands-off-selfheal -n 20
```

### 5. Check Circuit Breaker Status

```bash
# View circuit breaker states
python3 -c "
from infrastructure.resilience import get_circuit_breaker_status
import json
print(json.dumps(get_circuit_breaker_status(), indent=2))
"
```

## Monitoring and Maintenance

### Daily Operations

#### View System Status
```bash
# Quick health check
python3 infrastructure/health_monitor.py

# Watch live (updates every 60 seconds)
python3 infrastructure/health_monitor.py --watch 60

# JSON output for parsing
python3 infrastructure/health_monitor.py --json
```

#### Check Self-Healing Activity
```bash
# View recent self-healing actions
sudo journalctl -u hands-off-selfheal -n 100

# Check self-heal statistics
python3 infrastructure/selfheal.py --status
```

#### View Service Logs
```bash
# Systemd services
sudo journalctl -u hands-off-selfheal -f
sudo journalctl -u hands-off-health-monitor -f

# Docker containers
docker-compose logs -f selfheal
docker-compose logs -f health-monitor
```

### Weekly Maintenance

```bash
# Review alert history
grep -i "healing_action\|circuit_breaker" /var/log/hands-off-engine/*.log | tail -100

# Check disk usage trends
df -h
du -sh /home/user/hands-off-engine/state/*

# Verify backups exist
ls -lh /home/user/hands-off-engine/state/*.bak.* | tail -20

# Test failover (if configured)
# TODO: Add failover testing procedure
```

### Monthly Maintenance

```bash
# Update dependencies
pip3 install --user --upgrade -r requirements.txt

# Rotate old logs
sudo journalctl --vacuum-time=30d

# Review performance metrics
python3 scripts/track_performance.py --summary

# Security audit
# TODO: Add security scanning commands
```

## Troubleshooting

### Services Won't Start

**Symptom**: `systemctl start` fails

**Solutions**:
```bash
# Check logs for errors
sudo journalctl -xe -u hands-off-selfheal

# Verify Python dependencies
python3 -c "import structlog, psutil, requests; print('OK')"

# Check file permissions
ls -la /home/user/hands-off-engine/infrastructure/*.py

# Test script directly
python3 /home/user/hands-off-engine/infrastructure/selfheal.py
```

### High Resource Usage

**Symptom**: Health monitor reports high CPU/memory

**Solutions**:
```bash
# Identify resource hogs
top -u user

# Check for runaway processes
ps aux | grep python | grep hands-off

# Review recent actions
sudo journalctl -u hands-off-selfheal -n 100 | grep "restart"

# Adjust resource limits in service files
sudo systemctl edit hands-off-selfheal
```

### Self-Healing Not Working

**Symptom**: Services stay down after failure

**Solutions**:
```bash
# Verify self-heal service is running
sudo systemctl status hands-off-selfheal

# Check for consecutive failures
python3 infrastructure/selfheal.py --status

# Review restart commands in config
cat infrastructure/selfheal_config.json | jq .restart_commands

# Test restart manually
sudo systemctl restart hands-off-orchestrator

# Force heal action
python3 infrastructure/selfheal.py --force --service=orchestrator
```

### Circuit Breaker Stuck Open

**Symptom**: API calls failing with "Circuit breaker OPEN"

**Solutions**:
```bash
# Check circuit breaker status
python3 -c "
from infrastructure.resilience import get_circuit_breaker_status
import json
print(json.dumps(get_circuit_breaker_status(), indent=2))
"

# Wait for cooldown period (default 300s)
# OR restart the service to reset circuit breakers
sudo systemctl restart hands-off-orchestrator

# Check if external API is actually down
curl -I https://clob.polymarket.com/
```

### Database/State File Corruption

**Symptom**: "invalid JSON" or "corrupted state" errors

**Solutions**:
```bash
# Check which files are corrupted
for f in state/*.json termux-hands-off/state/*.json; do
    echo "Checking $f"
    python3 -c "import json; json.load(open('$f'))" 2>&1 | grep -i error
done

# Self-heal should auto-restore from backup
# Or manually restore
cp state/master.json.bak.$(ls -t state/*.bak.* | head -1 | cut -d. -f4) state/master.json

# Verify restoration
python3 -c "import json; print(json.load(open('state/master.json'))['timestamp'])"
```

## Advanced Topics

### Multi-Server Deployment

For high availability, deploy across multiple servers:

1. **Primary Server**: All services running
2. **Backup Server**: Health monitor + state replication
3. **Failover**: Automatic DNS/load balancer switch

See `docs/MULTI_SERVER_DEPLOYMENT.md` for details (TODO).

### Custom Healing Actions

Add your own healing actions:

```python
# In custom_healing.py
from infrastructure.selfheal import SelfHealController

controller = SelfHealController()

# Register custom action
controller.register_action(
    name="restart_custom_service",
    check=lambda: check_if_service_down(),
    heal=lambda: restart_custom_service(),
    severity="error",
    cooldown=600
)

controller.run()
```

### Integration with Existing Monitoring

Export metrics to external systems:

```bash
# Prometheus metrics endpoint (TODO)
curl http://localhost:9090/metrics

# JSON health status for external monitoring
curl http://localhost:8787/health

# Send to external system
python3 infrastructure/health_monitor.py --json | \
  curl -X POST https://your-monitoring-system.com/api/health \
    -H "Content-Type: application/json" \
    -d @-
```

## Uninstallation

### Remove Systemd Services

```bash
sudo systemctl stop hands-off-selfheal hands-off-health-monitor
sudo systemctl disable hands-off-selfheal hands-off-health-monitor
sudo systemctl disable hands-off-pipeline.timer
sudo rm /etc/systemd/system/hands-off-*.service
sudo rm /etc/systemd/system/hands-off-*.timer
sudo systemctl daemon-reload
```

### Remove Docker Containers

```bash
cd /home/user/hands-off-engine/infrastructure
docker-compose down -v
docker-compose down --rmi all
```

### Remove Files

```bash
# Remove infrastructure code (careful!)
rm -rf /home/user/hands-off-engine/infrastructure/

# Remove logs
sudo rm -rf /var/log/hands-off-engine/

# Remove configs
rm -f /home/user/hands-off-engine/infrastructure/*_config.json
```

## Next Steps

1. **Set up monitoring dashboard**: See `docs/DASHBOARD_SETUP.md` (TODO)
2. **Configure backup automation**: See `docs/BACKUP_STRATEGY.md` (TODO)
3. **Enable alerting**: Configure Telegram/email alerts
4. **Performance tuning**: Adjust thresholds and intervals
5. **Security hardening**: Review `docs/SECURITY.md` (TODO)

## Support

- **Documentation**: `/home/user/hands-off-engine/docs/`
- **Issues**: Check logs and see "Troubleshooting" section above
- **Logs**: `/var/log/hands-off-engine/` or `sudo journalctl -u hands-off-*`

---

**Last Updated**: 2025-11-21
**Version**: 1.0.0
