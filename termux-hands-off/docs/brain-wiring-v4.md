# Brain Wiring v4 - Batch 26 Deployment Guide

## Overview

Batch 26 Wiring v4 implements the systemd infrastructure for Hands-Off brain services. This deployment follows a **two-phase rollout**:

- **Phase 1 (Active)**: Brain viewer service only - read-only web interface for inspecting brain state
- **Phase 2 (Stub)**: Orchestrator, Decider, and Executor services - installed but not enabled

## Architecture

### Runtime Environment

- **Droplet Runtime Root**: `/root/hands-off-out`
- **Repo Subtree**: `termux-hands-off/` (1:1 mirror to droplet)
- **Deployment Flow**:
  1. Changes made in `termux-hands-off/` subtree
  2. Pushed from Termux via `mirror_ship.sh`
  3. Deployed on droplet via `ho-ai-deploy.sh`

### Components

#### Phase 1: Brain Viewer (Active)

**Purpose**: Read-only web interface for viewing brain state

**Service**: `ho-brain-viewer.service`
- Port: 8091 (configurable via `BRAIN_VIEWER_PORT`)
- Host: 127.0.0.1 (localhost only)
- Type: Long-running Flask web service
- State: Enabled and started

**Endpoints**:
- `GET /health` - Health check (returns 200 OK)
- `GET /txt/brain` - Text summary of brain state
- `GET /` - Redirects to `/txt/brain`

**Key Files**:
- Unit: `systemd/ho-brain-viewer.service`
- Wrapper: `bin/ho-brain-viewer.sh`
- App: `app/brain/viewer/app.py`
- Config: `config/brain-viewer.env`

**Safety**:
- Strictly read-only (no trades, no mutations)
- Reads from `/root/hands-off-out/state`
- Respects canonical mode file: `/root/hands-off-out/state/flags/mode.json`
- Does NOT conflict with existing viewer (different port, different unit name)

#### Phase 2: Brain Services (Stubs)

**Purpose**: Placeholder units for future batch activation

**Services** (all disabled):
1. `ho-brain-orchestrator.service` + `.timer`
   - Coordinates brain workflow
   - Timer: Every 5 minutes after boot

2. `ho-brain-decider.service` + `.timer`
   - Makes trading decisions
   - Timer: Every 5 minutes after boot

3. `ho-brain-executor.service` + `.timer`
   - Executes orders (DRYRUN/LIVE aware)
   - Timer: Every 5 minutes after boot

**State**:
- Units installed to `/etc/systemd/system`
- **NOT enabled** (systemctl is-enabled → disabled)
- **NOT started** (systemctl is-active → inactive)
- Wrapper scripts are stubs that log and exit 0

**Key Files**:
- Units: `systemd/ho-brain-{orchestrator,decider,executor}.{service,timer}`
- Wrappers: `bin/ho-brain-{orchestrator,decider,executor}.sh` (stubs)
- Apps: `app/brain/{orchestrator,decider,executor}/main.py` (stubs)

## Deployment Process

### Wiring Script: `ho-brain-wire.sh`

Located: `deploy/ho-brain-wire.sh` (mirrors to `/root/hands-off-out/deploy/`)

**What it does**:
1. Ensures log directory exists
2. Reads canonical mode file (DRYRUN/LIVE) for logging
3. Validates required config files exist
4. Backs up existing ho-brain-* units with `.bak.<timestamp>`
5. Copies all units from `systemd/` → `/etc/systemd/system/`
6. Runs `systemctl daemon-reload`
7. **Enables ONLY** `ho-brain-viewer.service`
8. Restarts `ho-brain-viewer.service`
9. Performs HTTP health check on viewer (soft-fail, warning only)
10. Confirms Phase 2 units remain disabled
11. Exits with appropriate status code

**Safe for DRYRUN**:
- Only touches ho-brain-* units (never touches other services)
- Validates mode file before proceeding
- HTTP check failures are warnings, not errors
- Uses `set -euo pipefail` with proper error handling

### Integration with Deployment Pipeline

```
[Termux Repo]
    ↓
mirror_ship.sh  (pushes termux-hands-off/ → /root/hands-off-out)
    ↓
[Droplet: /root/hands-off-out]
    ↓
ho-ai-deploy.sh  (calls ho-brain-wire.sh)
    ↓
ho-brain-wire.sh  (installs units, enables viewer only)
    ↓
[Systemd: /etc/systemd/system]
```

## Configuration Files

### `config/brain-services.env`
Shared environment for all brain services:
- `VENV_PATH`: Python virtual environment
- `PYTHONPATH`: Module import path
- `BRAIN_STATE_DIR`: State directory location
- `BRAIN_CONFIG_FILE`: Global config file path

### `config/brain-viewer.env`
Viewer-specific settings:
- `BRAIN_VIEWER_PORT`: HTTP port (8091)
- `BRAIN_VIEWER_HOST`: Bind address (127.0.0.1)
- `BRAIN_VIEWER_READ_ONLY`: Enforce read-only mode (true)

### `config/brain-config.json`
Global brain configuration:
- Version and phase info
- State directory paths
- Timer intervals for Phase 2 services
- Service status tracking

### Canonical Mode File
**Location**: `/root/hands-off-out/state/flags/mode.json`

This is the **single source of truth** for DRYRUN vs LIVE mode.
- Used by wiring script for logging
- Used by brain services to enforce safety
- Never mutated by brain services

## DRYRUN Deployment Checklist

### Pre-Deployment
1. Confirm canonical mode file shows DRYRUN:
   ```bash
   cat /root/hands-off-out/state/flags/mode.json
   ```

### Deployment
2. Run from Termux:
   ```bash
   mirror_ship.sh
   ```

3. Run on droplet:
   ```bash
   cd /root/hands-off-out
   ./ho-ai-deploy.sh
   echo "Exit code: $?"
   ```

### Post-Deployment Validation

4. Check viewer service status:
   ```bash
   systemctl status ho-brain-viewer.service
   systemctl is-enabled ho-brain-viewer.service  # Should be "enabled"
   systemctl is-active ho-brain-viewer.service   # Should be "active"
   ```

5. Verify Phase 2 units are disabled:
   ```bash
   for unit in orchestrator decider executor; do
     systemctl is-enabled ho-brain-${unit}.service || true
     systemctl is-active ho-brain-${unit}.service || true
   done
   # All should be "disabled" or "static", and "inactive"
   ```

6. Test viewer HTTP endpoints:
   ```bash
   source /root/hands-off-out/config/brain-viewer.env
   curl -fsS "http://127.0.0.1:${BRAIN_VIEWER_PORT}/health"
   curl -fsS "http://127.0.0.1:${BRAIN_VIEWER_PORT}/txt/brain"
   ```

7. Check logs:
   ```bash
   journalctl -u ho-brain-viewer.service -n 50 --no-pager
   tail -50 /root/hands-off-out/state/logs/brain-viewer.log
   ```

8. Verify read-only behavior:
   ```bash
   grep -Ei "LIVE|order|execute" /root/hands-off-out/state/logs/brain-viewer.log | tail
   # Should see NO lines indicating live orders or trades
   ```

9. Regression check existing viewer:
   ```bash
   # Test existing viewer on its known port (if applicable)
   # Ensure no port conflicts or service disruption
   ```

### Success Criteria
- ✅ Viewer service is running and healthy
- ✅ HTTP endpoints return valid responses
- ✅ Phase 2 units installed but disabled
- ✅ No LIVE order behavior in logs
- ✅ Existing services unaffected
- ✅ Canonical mode file shows DRYRUN

## Phase 1 vs Phase 2 Split

### Phase 1 (This Batch)
**Goal**: Deploy read-only brain viewer for state inspection

**What's Active**:
- `ho-brain-viewer.service` (enabled + started)

**What's Safe**:
- No trading decisions
- No order execution
- No external API calls (except state reading)
- Coexists with existing infrastructure

### Phase 2 (Future Batch)
**Goal**: Activate orchestrator → decider → executor pipeline

**What Will Activate**:
- Timer-driven orchestration
- Decision-making logic
- Order execution (respecting DRYRUN/LIVE mode)

**Prerequisites Before Phase 2**:
- Phase 1 viewer validated and stable
- DRYRUN testing completed
- Risk management finalized
- Explicit approval to enable Phase 2 units

## Troubleshooting

### Viewer Won't Start
```bash
# Check journal logs
journalctl -u ho-brain-viewer.service -n 100 --no-pager

# Check if port is already in use
ss -tlnp | grep 8091

# Verify config files
cat /root/hands-off-out/config/brain-viewer.env
cat /root/hands-off-out/config/brain-services.env

# Test Python app manually
cd /root/hands-off-out
python3 -m app.brain.viewer.app
```

### HTTP Health Check Fails
```bash
# Check if service is running
systemctl status ho-brain-viewer.service

# Test endpoints manually
curl -v http://127.0.0.1:8091/health
curl -v http://127.0.0.1:8091/txt/brain

# Check firewall (should be localhost only)
# No external access needed
```

### Phase 2 Units Accidentally Enabled
```bash
# Disable immediately
systemctl disable --now ho-brain-orchestrator.service
systemctl disable --now ho-brain-orchestrator.timer
systemctl disable --now ho-brain-decider.service
systemctl disable --now ho-brain-decider.timer
systemctl disable --now ho-brain-executor.service
systemctl disable --now ho-brain-executor.timer

# Verify disabled
systemctl is-enabled ho-brain-orchestrator.service  # Should be "disabled"
```

### Rollback Procedure
```bash
# Stop and disable viewer
systemctl disable --now ho-brain-viewer.service

# Restore previous units from backup
cd /etc/systemd/system
ls -la ho-brain-*.bak.*  # Find backup timestamp
# Restore as needed

# Reload systemd
systemctl daemon-reload
```

## File Reference Summary

### Systemd Units (`termux-hands-off/systemd/`)
- `ho-brain-viewer.service` (Phase 1)
- `ho-brain-orchestrator.{service,timer}` (Phase 2 stub)
- `ho-brain-decider.{service,timer}` (Phase 2 stub)
- `ho-brain-executor.{service,timer}` (Phase 2 stub)

### Scripts (`termux-hands-off/bin/`)
- `ho-brain-viewer.sh` (active wrapper)
- `ho-brain-orchestrator.sh` (stub)
- `ho-brain-decider.sh` (stub)
- `ho-brain-executor.sh` (stub)

### Deployment (`termux-hands-off/deploy/`)
- `ho-brain-wire.sh` (main wiring script)

### Config (`termux-hands-off/config/`)
- `brain-services.env` (shared env)
- `brain-viewer.env` (viewer env)
- `brain-config.json` (global config)

### Python App (`termux-hands-off/app/brain/`)
- `viewer/app.py` (Flask web app)
- `orchestrator/main.py` (stub)
- `decider/main.py` (stub)
- `executor/main.py` (stub)

## Next Steps

After successful Phase 1 deployment:

1. Monitor viewer logs for stability
2. Validate state reading accuracy
3. Use viewer to inspect brain state during DRYRUN operations
4. Plan Phase 2 activation in future batch
5. Document any learnings or adjustments needed

---

**Version**: Batch 26 Wiring v4
**Phase**: 1 (Viewer Only)
**Status**: Ready for DRYRUN deployment
**Last Updated**: 2025-11-19
