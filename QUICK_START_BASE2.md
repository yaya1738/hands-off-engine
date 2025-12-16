# Quick Start: Base 2 Provisioning

**3-Step Guide to Dual-Base Operation**

---

## Prerequisites

- Terminal access
- Credit card (for Oracle Cloud verification, won't be charged)
- 40 minutes of time
- Current base (Base 1) running

---

## Step 1: Provision Oracle Cloud (30 min)

```bash
cd /root/hands-off-engine
bash scripts/provision_oracle_cloud.sh
```

**What it does:**
- Guides you through Oracle Cloud account creation
- Provisions free VM instance (forever free)
- Sets up SSH keys automatically
- Configures firewall rules
- Tests connection
- Creates SSH alias `base2`

**Interactive steps:**
1. Create Oracle Cloud account at https://www.oracle.com/cloud/free/
2. Follow prompts to provision VM
3. Copy/paste public SSH key when prompted
4. Wait for instance to start
5. Enter public IP address when prompted

**Output:** SSH alias `base2` configured and tested

---

## Step 2: Deploy System (10 min)

```bash
bash scripts/complete_base2_setup.sh base2
```

**What it does:**
- Deploys code to Base 2 (automated)
- Verifies installation (automated)
- Starts autonomous loop (automated)
- Shows monitoring dashboard (automated)

**No interaction required - fully automated!**

**Output:** Dual-base system operational

---

## Step 3: Monitor (Ongoing)

```bash
bash scripts/monitor_dual_bases.sh localhost base2
```

**What it shows:**
- Both bases status
- System resources
- API statistics
- Redundancy status

---

## Troubleshooting

### Can't connect to Oracle Cloud?
```bash
ssh -v ubuntu@<IP_ADDRESS>
```
Check firewall rules in Oracle Cloud console

### Deployment failed?
```bash
bash scripts/verify_new_base.sh base2
```
Shows exactly what's wrong

### System won't start?
```bash
ssh base2
cd /root/hands-off-engine
python3 autonomous/full_autonomous_loop.py
```
Check for error messages

---

## Commands Reference

### Access Base 2
```bash
ssh base2
```

### View autonomous loop
```bash
ssh base2
tmux attach -t hands-off
```

### Check API dashboard
```bash
ssh base2 'cd /root/hands-off-engine && python3 integrafix/api_dashboard.py'
```

### Monitor both bases
```bash
bash scripts/monitor_dual_bases.sh localhost base2
```

### Verify Base 2 health
```bash
bash scripts/verify_new_base.sh base2
```

---

## What You Get

- ✅ Zero cost ($0/month forever)
- ✅ Full redundancy (no single point of failure)
- ✅ Geographic distribution
- ✅ Antifragile architecture
- ✅ Automatic failover capability
- ✅ Infinite ROI

---

## Timeline

| Step | Time | Type |
|------|------|------|
| Provision hardware | 30 min | Interactive |
| Deploy system | 10 min | Automated |
| **Total** | **40 min** | |

---

## Architecture

**Before:**
```
[Base 1] ← Single point of failure
```

**After:**
```
[Base 1] ←→ [Base 2]
   ✅ Full redundancy
   ✅ Zero downtime
   ✅ Antifragile
```

---

## Support

- **Complete guide:** `HARDWARE_DEPLOYMENT.md`
- **Detailed status:** `PROVISIONING_STATUS.md`
- **Scripts:** `scripts/` directory

---

**Ready?** Run Step 1:
```bash
bash scripts/provision_oracle_cloud.sh
```

**Master:** Yair Siegel
**Date:** 2025-12-04
