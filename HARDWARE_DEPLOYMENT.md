# Hardware Deployment Guide

Complete guide for provisioning and deploying to new hardware bases.

**Status:** Base 1 (current) operational, Base 2 (Oracle Cloud) ready to provision
**Master:** Yair Siegel
**Date:** 2025-12-04

---

## Overview

This system uses multiple hardware bases for redundancy and antifragility. Each base runs independently with the same codebase, state syncing between them.

### Current Architecture

- **Base 1:** Current operational base (this system)
- **Base 2:** Oracle Cloud Always Free (ready to provision)

### Why Multiple Bases?

1. **Zero downtime:** If one base fails, others continue
2. **Geographic distribution:** Multiple locations for resilience
3. **Antifragility:** System gets stronger from failures
4. **Cost optimization:** Free tier resources = infinite ROI

---

## Hardware Selection Process

### ABCFC Analysis Results

We analyzed 6 hardware options using ABCFC scoring:

| Option | Score | Cost/Month | Specs | Free Tier |
|--------|-------|------------|-------|-----------|
| **Oracle Cloud** | **82.88** | **$0** | 1 CPU, 1GB RAM, 50GB | Forever |
| Termux (Android) | 81.76 | $0 | 4 CPU, 2GB RAM, 10GB | Forever |
| AWS EC2 t2.micro | 77.88 | $0 | 1 CPU, 1GB RAM, 30GB | 12 months |
| GCP e2-micro | 77.88 | $0 | 2 CPU, 1GB RAM, 30GB | 12 months |
| Hetzner CX11 | 69.86 | $3.79 | 1 CPU, 2GB RAM, 20GB | No |
| DigitalOcean | 58.80 | $4.00 | 1 CPU, 1GB RAM, 25GB | No |

**Winner:** Oracle Cloud - Always Free
- Forever free (no expiration)
- 4 geographic locations
- Sufficient specs for our needs
- Setup time: 30 minutes

### Analysis Script

See: `analysis/hardware_provisioning_decision.py`

Run analysis:
```bash
cd /root/hands-off-engine
python3 analysis/hardware_provisioning_decision.py
```

---

## Provisioning Process

### Step 1: Provision Hardware

**For Oracle Cloud (recommended):**

```bash
cd /root/hands-off-engine
bash scripts/provision_oracle_cloud.sh
```

This script will guide you through:
1. Creating Oracle Cloud account
2. Provisioning VM instance
3. Setting up SSH keys
4. Configuring firewall
5. Testing connection

**Time:** ~30 minutes
**Cost:** $0 (forever free)

The script is **interactive** - it pauses for you to complete web console steps.

### Step 2: Deploy Code

After provisioning is complete:

```bash
cd /root/hands-off-engine
bash scripts/deploy_to_new_base.sh base2
```

This automatically:
1. Verifies connection
2. Updates system packages
3. Installs dependencies
4. Clones repository
5. Installs Python packages
6. Creates directory structure
7. Copies .env file
8. Verifies installation

**Time:** ~5 minutes
**Requires:** SSH access to new base

### Step 3: Verify Deployment

```bash
bash scripts/verify_new_base.sh base2
```

This checks:
- SSH connectivity
- System information
- Dependencies
- Repository status
- Python packages
- Directory structure
- Environment variables
- Key files
- Firewall configuration
- System functionality

**Exit code:** 0 if all checks pass, >0 if issues found

### Step 4: Start System

```bash
ssh base2
cd /root/hands-off-engine
python3 autonomous/full_autonomous_loop.py
```

Or run in background with tmux:
```bash
ssh base2
tmux new -s hands-off
cd /root/hands-off-engine
python3 autonomous/full_autonomous_loop.py
# Press Ctrl+B, then D to detach
```

---

## Monitoring

### Monitor Both Bases

```bash
bash scripts/monitor_dual_bases.sh localhost base2
```

This shows:
- Connection status
- System resources
- API manager statistics
- Failure hardening status
- Running processes
- Redundancy status

### Individual Base Monitoring

**Base 1 (local):**
```bash
cd /root/hands-off-engine
python3 integrafix/api_dashboard.py
```

**Base 2 (remote):**
```bash
ssh base2 'cd /root/hands-off-engine && python3 integrafix/api_dashboard.py'
```

---

## Architecture

### Multi-Base Architecture

```
┌─────────────────┐         ┌─────────────────┐
│    BASE 1       │         │    BASE 2       │
│   (Primary)     │◄───────►│   (Backup)      │
│                 │  Sync   │                 │
│  Autonomous     │         │  Autonomous     │
│  Loop Running   │         │  Loop Running   │
│                 │         │                 │
│  APIs           │         │  APIs           │
│  State          │         │  State          │
│  Logs           │         │  Logs           │
└─────────────────┘         └─────────────────┘
        │                           │
        └───────────┬───────────────┘
                    │
            ┌───────▼────────┐
            │   External     │
            │   Services     │
            │                │
            │  • GitHub      │
            │  • Polymarket  │
            │  • HackerOne   │
            └────────────────┘
```

### State Synchronization

Currently: Manual (planned: automatic)

To sync state from Base 1 to Base 2:
```bash
scp -r /root/hands-off-engine/state/* base2:/root/hands-off-engine/state/
scp -r /root/hands-off-engine/logs/* base2:/root/hands-off-engine/logs/
```

---

## Scripts Reference

### Provisioning Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `provision_oracle_cloud.sh` | Provision Oracle Cloud instance | `bash scripts/provision_oracle_cloud.sh` |
| `setup_new_base.sh` | Setup fresh installation | Run on new hardware directly |

### Deployment Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `deploy_to_new_base.sh` | Deploy code to new base | `bash scripts/deploy_to_new_base.sh <host>` |
| `verify_new_base.sh` | Verify deployment | `bash scripts/verify_new_base.sh <host>` |

### Monitoring Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `monitor_dual_bases.sh` | Monitor both bases | `bash scripts/monitor_dual_bases.sh <base1> <base2>` |

---

## Configuration

### SSH Configuration

Add to `~/.ssh/config`:
```
Host base2
    HostName <IP_ADDRESS>
    User ubuntu
    IdentityFile ~/.ssh/id_rsa
    StrictHostKeyChecking no
```

### Environment Variables

Both bases need `.env` file with:
```bash
# GitHub API Token
GITHUB_TOKEN=your_token

# Polymarket API Credentials
POLYMARKET_API_KEY=your_key
POLYMARKET_API_SECRET=your_secret
POLYMARKET_PASSPHRASE=your_passphrase

# HackerOne API Token
HACKERONE_API_TOKEN=your_token

# AWS Credentials
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Etherscan/Polygonscan API Keys
ETHERSCAN_API_KEY=your_key
POLYGONSCAN_API_KEY=your_key
```

The deployment script automatically copies `.env` from Base 1 to Base 2.

---

## Troubleshooting

### Connection Issues

**Problem:** Cannot SSH to new base
```bash
# Test connection
ssh -v ubuntu@<IP_ADDRESS>

# Check firewall rules in Oracle Cloud console
# Ensure port 22 is open

# Try manual connection
ssh -o StrictHostKeyChecking=no ubuntu@<IP_ADDRESS>
```

### Deployment Failures

**Problem:** Deployment script fails
```bash
# Run verification to see what's missing
bash scripts/verify_new_base.sh base2

# Check specific issues:
# - SSH connection
# - Git repository
# - Python packages
# - Directory structure
```

### System Not Starting

**Problem:** Autonomous loop won't start
```bash
# SSH to base
ssh base2

# Check for errors
cd /root/hands-off-engine
python3 autonomous/full_autonomous_loop.py

# Check dependencies
pip3 list | grep -E "requests|pydantic|web3"

# Check .env
cat .env | grep -v '^#' | grep '='

# Check logs
tail -100 logs/autonomous.log
```

### Performance Issues

**Problem:** Base running slowly
```bash
# Check system resources
ssh base2 'htop'

# Check for high CPU/memory usage
ssh base2 'top -bn1 | head -20'

# Check disk space
ssh base2 'df -h'

# Monitor with dual base script
bash scripts/monitor_dual_bases.sh localhost base2
```

---

## Best Practices

### 1. Never Touch Running Base

When deploying new base:
- ✅ Provision new hardware
- ✅ Deploy to new base
- ✅ Verify new base
- ✅ Start system on new base
- ❌ Don't stop current base
- ❌ Don't migrate data yet
- ❌ Don't touch current system

### 2. Verify Before Starting

Always run verification:
```bash
bash scripts/verify_new_base.sh base2
```

Only start system if all checks pass.

### 3. Monitor Both Bases

Run monitoring regularly:
```bash
bash scripts/monitor_dual_bases.sh localhost base2
```

Watch for:
- Both bases online
- Similar performance
- No critical errors

### 4. Keep Credentials Synced

When updating API keys:
```bash
# Update .env on both bases
vim /root/hands-off-engine/.env  # Base 1
ssh base2 'vim /root/hands-off-engine/.env'  # Base 2
```

### 5. Regular Health Checks

```bash
# Run on both bases daily
python3 integrafix/api_dashboard.py
python3 integrafix/failure_hardening.py
```

---

## Security Considerations

### SSH Keys

- Use strong SSH keys (4096-bit RSA)
- Never commit private keys to git
- Use different keys for different bases (optional)

### API Credentials

- Store in `.env` file (gitignored)
- Never commit credentials to git
- Rotate credentials periodically
- Use minimal permissions

### Firewall Rules

- Only open required ports (22, 443)
- Use Oracle Cloud security lists
- Enable UFW on instance
- Restrict SSH to known IPs (optional)

### System Updates

```bash
# Update regularly on both bases
ssh base2 'sudo apt-get update && sudo apt-get upgrade -y'
```

---

## Future Enhancements

### Planned Features

1. **Automatic state sync** - Real-time synchronization between bases
2. **Load balancing** - Distribute work across bases
3. **Automatic failover** - Switch to backup if primary fails
4. **Health monitoring** - Automated alerts for issues
5. **Base orchestration** - Central management of all bases

### Adding More Bases

To add Base 3, 4, etc.:

1. Run hardware analysis for new options
2. Provision new hardware
3. Deploy with `deploy_to_new_base.sh`
4. Verify with `verify_new_base.sh`
5. Update monitoring script for new base

---

## Cost Analysis

### Current Setup

- **Base 1:** $0/month (Termux or existing)
- **Base 2:** $0/month (Oracle Cloud Forever Free)
- **Total:** $0/month

### Scalability

Adding more free bases:
- AWS EC2 t2.micro (12 months free)
- GCP e2-micro (12 months free)
- Azure B1S (12 months free)

**Total cost for 5 bases:** $0/month (first year)

### ROI Analysis

- **Cost:** $0/month
- **Value:** Redundancy prevents $1000+ losses
- **Expected value:** $50/month (5% failure rate)
- **ROI:** ∞ (infinite)

---

## Support

### Documentation

- **API System:** `API_SYSTEM.md`
- **Web Architecture:** `WEB_ARCHITECTURE.md`
- **Autonomous Status:** `AUTONOMOUS_STATUS.md`

### Scripts

All scripts in `scripts/` directory:
- Provisioning
- Deployment
- Verification
- Monitoring

### Analysis

All analysis in `analysis/` directory:
- Hardware provisioning decision
- Cost-benefit analysis
- ABCFC scoring

---

## Quick Start

**Complete workflow for adding Base 2:**

```bash
# 1. Provision hardware
cd /root/hands-off-engine
bash scripts/provision_oracle_cloud.sh
# Follow interactive prompts (~30 min)

# 2. Deploy code
bash scripts/deploy_to_new_base.sh base2
# Automated (~5 min)

# 3. Verify installation
bash scripts/verify_new_base.sh base2
# Check all tests pass

# 4. Start system
ssh base2 'cd /root/hands-off-engine && tmux new -d -s hands-off "python3 autonomous/full_autonomous_loop.py"'

# 5. Monitor both bases
bash scripts/monitor_dual_bases.sh localhost base2

# 6. Celebrate redundancy! 🎉
```

---

**Master:** Yair Siegel
**Last Updated:** 2025-12-04
**Status:** Base 1 operational, Base 2 ready to provision
