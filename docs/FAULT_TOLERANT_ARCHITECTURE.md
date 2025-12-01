# Fault-Tolerant Architecture for Hands-Off Engine

## Overview

This document outlines the fault-tolerant, self-healing architecture designed to enable 24/7 autonomous operation with minimal user intervention.

## Architecture Principles

1. **Self-Healing First**: Detect and automatically remediate failures
2. **Fail Gracefully**: Degrade functionality rather than crash completely
3. **Monitor Everything**: Comprehensive observability at all levels
4. **Secure by Default**: Least privilege, encrypted credentials, audit logs
5. **Scalable Design**: Modular components that can scale independently

## System Architecture

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
│  ┌──────────────────────────────────────────────────┐       │
│  │  Health Monitor (ho_health_monitor)              │       │
│  │  - Service health checks                         │       │
│  │  - Resource monitoring (CPU, memory, disk)       │       │
│  │  - State file freshness checks                   │       │
│  │  - API endpoint validation                       │       │
│  └──────────────────────────────────────────────────┘       │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Self-Heal Controller (ho_selfheal)              │       │
│  │  - Automatic service restarts                    │       │
│  │  - Process resurrection                          │       │
│  │  - State recovery                                │       │
│  │  - Alert escalation                              │       │
│  └──────────────────────────────────────────────────┘       │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Circuit Breaker Manager                         │       │
│  │  - API failure tracking                          │       │
│  │  - Automatic circuit opening/closing             │       │
│  │  - Fallback strategies                           │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Application Services                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │   Alpha    │  │  Decider   │  │  Executor  │           │
│  │   Signal   │  │   Engine   │  │  Service   │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  Finance   │  │   Daily    │  │  Market    │           │
│  │  Watcher   │  │   Health   │  │   Data     │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  ┌──────────────────────────────────────────────────┐       │
│  │  State Management                                │       │
│  │  - SQLite database (structured data)             │       │
│  │  - JSON files (backward compatibility)           │       │
│  │  - Automatic backups (hourly → S3/rsync)         │       │
│  │  - Transaction logs                              │       │
│  └──────────────────────────────────────────────────┘       │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Logging & Monitoring                            │       │
│  │  - Structured JSON logs                          │       │
│  │  - Centralized aggregation (Loki/CloudWatch)     │       │
│  │  - Metrics collection (Prometheus)               │       │
│  │  - Distributed tracing                           │       │
│  └──────────────────────────────────────────────────┘       │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Alert Management                                │       │
│  │  - Telegram (primary)                            │       │
│  │  - Email (important updates)                     │       │
│  │  - IFTTT (backup channel)                        │       │
│  │  - PagerDuty (critical only)                     │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Health Monitoring System

**Purpose**: Continuously monitor all system components and detect failures before they cascade.

**Components**:
- **Health Monitor Service** (`/infrastructure/health_monitor.py`)
  - Runs every 60 seconds
  - Checks 10+ health indicators
  - Publishes status to monitoring dashboard
  - Triggers self-heal actions on failures

**Health Checks**:
- Service heartbeats (master.json age, finance.json updates)
- API endpoint responsiveness (Polymarket API, admin server)
- Resource utilization (disk space, memory, CPU)
- State file integrity (valid JSON, expected schemas)
- Cron job execution (last run times)
- Network connectivity
- Database accessibility

**Alerting Thresholds**:
- **WARNING**: Service hasn't updated in 45 minutes
- **ERROR**: Service hasn't updated in 90 minutes, auto-restart triggered
- **CRITICAL**: Auto-restart failed 3 times, escalate to user

### 2. Self-Healing Controller

**Purpose**: Automatically remediate detected issues without user intervention.

**Actions**:
- **Process Restart**: Kill and respawn unresponsive services
- **State Recovery**: Restore from last known good backup
- **Cache Clear**: Remove corrupted temporary files
- **Resource Cleanup**: Free disk space, clear old logs
- **Network Reset**: Restart network-dependent services
- **Fallback Mode**: Switch to safe mode if issues persist

**Healing Strategies**:
```python
if service_stale(service_name, threshold=45*60):
    log_warning(f"{service_name} is stale")

    if service_stale(service_name, threshold=90*60):
        log_error(f"Auto-restarting {service_name}")
        restart_service(service_name)

        if not service_healthy(service_name, wait=300):
            escalate_alert(f"{service_name} failed to recover")
            enter_safe_mode(service_name)
```

### 3. Retry & Circuit Breaker Patterns

**Purpose**: Handle transient failures and prevent cascading API failures.

**Implementation**:
- **Retry Decorator**: Exponential backoff for transient errors
- **Circuit Breaker**: Open circuit after N failures, close after cooldown
- **Timeout Guards**: All API calls have max timeout
- **Rate Limiting**: Respect API rate limits automatically

**Example**:
```python
from infrastructure.resilience import retry, circuit_breaker, timeout

@retry(max_attempts=4, backoff=[2, 4, 8, 16])
@circuit_breaker(failure_threshold=5, cooldown=300)
@timeout(30)
def fetch_polymarket_data():
    # API call with automatic retry and circuit breaking
    pass
```

### 4. Service Orchestration

**Options** (choose based on deployment environment):

**Option A: Docker + Docker Compose** (Recommended for cloud)
- Containerized services
- Automatic restart policies
- Resource limits
- Network isolation
- Easy deployment

**Option B: systemd Services** (Recommended for VPS/dedicated servers)
- Native Linux integration
- Automatic restart on failure
- Resource management via cgroups
- Logging to journald
- Startup ordering

**Option C: Supervisor** (Lightweight alternative)
- Simple process manager
- Automatic restarts
- Web UI for monitoring
- Easy configuration

### 5. State Management

**Multi-Tier Strategy**:

**Tier 1: SQLite Database** (new)
- Structured data (transactions, performance metrics, alerts)
- ACID guarantees
- Query capabilities
- Automatic backups

**Tier 2: JSON Files** (existing, backward compatible)
- Large nested objects (decision reports, alpha signals)
- Human-readable for debugging
- Git-trackable for multi-node sync

**Tier 3: In-Memory Cache** (new)
- Frequently accessed data (current positions, recent prices)
- Redis for distributed caching
- Automatic expiration

**Backup Strategy**:
- **Continuous**: WAL mode for SQLite (point-in-time recovery)
- **Hourly**: JSON state files → timestamped backups
- **Daily**: Full system snapshot → cloud storage (S3/B2)
- **Weekly**: Long-term archive with 90-day retention

### 6. Logging & Observability

**Structured Logging**:
```python
import structlog

logger = structlog.get_logger()
logger.info("trade_executed",
    symbol="BTC-USD",
    quantity=0.5,
    price=50000,
    order_id="abc123",
    execution_time_ms=234
)
```

**Log Levels**:
- **DEBUG**: Detailed execution flow (disabled in production)
- **INFO**: Normal operations (trades, updates, health checks)
- **WARNING**: Recoverable issues (retries, staleness)
- **ERROR**: Failures requiring auto-healing
- **CRITICAL**: System-wide failures requiring escalation

**Metrics Collection**:
- Request counts and latencies
- Error rates by component
- Resource utilization trends
- Business metrics (P/L, trade counts, signal quality)

### 7. Security & Compliance

**Security Measures**:
- Encrypted credential storage (keyring/vault)
- Least privilege access (service-specific API keys)
- Audit logs for all financial actions
- Rate limiting on admin API
- IP whitelist for sensitive endpoints
- Automated security scanning

**Compliance Checks**:
- Position size limits (circuit breaker)
- Maximum daily loss threshold
- Regulatory checks before trade execution
- Tax event logging
- Terms of service compliance monitoring

### 8. Failover & Redundancy

**Service Level**:
- Primary and secondary instances for critical services
- Automatic failover on primary failure
- Health-based load balancing

**Data Level**:
- Master-replica database replication
- Multi-region backup storage
- State file mirroring across nodes

**Network Level**:
- Multiple alert channels (Telegram, email, IFTTT)
- Fallback API endpoints (multiple brokers)
- CDN for dashboard assets

## Deployment Architecture

### Single Server Deployment (Current)
```
Termux Phone (Node 1)          DigitalOcean Droplet (Node 2)
├── orchestrator.py            ├── Market data fetching
├── finance_watcher.py         ├── Edge detection
├── daily_health.py            ├── Backup monitoring
└── Cron jobs (hourly)         └── Dashboard hosting
       │                              │
       └──────── Git Sync ────────────┘
            (state files)
```

### High-Availability Deployment (Target)
```
Primary Server (Cloud VM)
├── All core services (Docker)
├── PostgreSQL database
├── Prometheus + Grafana
├── Admin dashboard
└── Self-healing controller
       │
       ├─── Backup Server (Standby)
       │    └── Receives state snapshots every 5 min
       │
       └─── External Monitors
            ├── UptimeRobot (HTTP checks)
            ├── Healthchecks.io (cron monitoring)
            └── PagerDuty (critical alerts)
```

## Implementation Roadmap

### Phase 1: Foundation (Week 1) ✓ Current Focus
- [x] Document architecture
- [ ] Implement retry decorator
- [ ] Add circuit breaker pattern
- [ ] Create self-healing watchdog
- [ ] Build health monitor service

### Phase 2: Persistence (Week 2)
- [ ] Create Docker containers
- [ ] Write docker-compose.yml
- [ ] Implement systemd services
- [ ] Add SQLite database layer
- [ ] Automated backup system

### Phase 3: Observability (Week 3)
- [ ] Structured logging library
- [ ] Centralized log aggregation
- [ ] Metrics collection
- [ ] Enhanced dashboard with real-time data
- [ ] Alert management UI

### Phase 4: Redundancy (Week 4)
- [ ] Primary/backup server setup
- [ ] State replication
- [ ] Automatic failover
- [ ] Multi-region backups
- [ ] Load testing

### Phase 5: Scaling (Future)
- [ ] Kubernetes orchestration
- [ ] Horizontal scaling
- [ ] Multi-tenant support
- [ ] Advanced ML model serving
- [ ] API gateway

## Operational Procedures

### Normal Operation
1. Services run automatically via cron/systemd
2. Health monitor checks every 60 seconds
3. Alerts sent only for actionable issues
4. User views daily summary email
5. Dashboard accessible 24/7 for status checks

### Incident Response
1. **Detection**: Health monitor or alert fired
2. **Auto-Heal**: Self-heal controller attempts recovery
3. **Verification**: Health check confirms resolution
4. **Alert**: User notified of incident and resolution
5. **Post-Mortem**: Incident logged with root cause

### Manual Intervention
```bash
# View system status
./scripts/monitor.sh

# Check health
./infrastructure/health_check.sh

# Restart specific service
systemctl restart hands-off-executor

# Force healing action
./infrastructure/selfheal.py --force --service=executor

# Enter safe mode (pause trading)
curl -X POST http://localhost:8787/admin/pause \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# View logs
journalctl -u hands-off-executor -f
tail -f /var/log/hands-off-engine/executor.log

# Check circuit breaker status
./infrastructure/circuit_breaker_status.py
```

## Performance Targets

- **Uptime**: 99.9% (< 9 hours downtime/year)
- **Recovery Time**: < 5 minutes for service restart
- **Alert Latency**: < 2 minutes from failure to notification
- **Data Loss**: < 1 hour (backup frequency)
- **False Positives**: < 1 per week (alert tuning)

## Cost Estimates

### Infrastructure
- **Cloud VM**: $10-50/month (DigitalOcean, Hetzner)
- **Backup Storage**: $5-10/month (S3, Backblaze B2)
- **Monitoring**: $0 (self-hosted) or $10-20/month (SaaS)
- **Alerts**: $0 (Telegram, email)

### Maintenance
- **Automated**: 95% of issues self-heal
- **Manual Review**: ~2 hours/week (checking summaries)
- **Major Updates**: ~4 hours/month (system upgrades)

**Total**: ~$30-80/month + ~10 hours/month

## Testing Strategy

### Health Check Tests
- Simulate service failures (kill processes)
- Verify auto-restart works
- Test alert delivery
- Validate state recovery

### Load Tests
- High-volume market data ingestion
- Concurrent trade executions
- Dashboard stress testing
- Database performance under load

### Failure Scenarios
- Network outage
- API rate limits
- Disk full
- Memory exhaustion
- Database corruption
- Invalid state files

### Security Tests
- Credential leak detection
- API authentication bypass attempts
- SQL injection (if using raw SQL)
- XSS in dashboard
- CSRF on admin endpoints

## References

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [systemd Service Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Prometheus Monitoring](https://prometheus.io/docs/introduction/overview/)
- [12-Factor App Methodology](https://12factor.net/)

---

**Last Updated**: 2025-11-21
**Version**: 1.0.0
**Status**: Implementation In Progress
