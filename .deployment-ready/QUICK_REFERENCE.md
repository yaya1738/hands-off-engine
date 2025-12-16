# NEW BASE DEPLOYMENT - QUICK REFERENCE

## ⚡ ONE-COMMAND DEPLOYMENT

```bash
bash scripts/DEPLOY_NEW_BASE.sh
```

That's it. The script handles everything.

---

## 🔍 PRE-FLIGHT CHECK (Optional)

Before deploying, verify everything is ready:

```bash
bash .deployment-ready/PRE_FLIGHT_CHECK.sh
```

This checks:
- Current base operational
- Credentials available
- Scripts present
- Network connectivity
- System resources

---

## 📋 DEPLOYMENT WORKFLOW

```
Pre-Flight Check
       ↓
Choose Hardware
  (Oracle/Existing)
       ↓
Provision Hardware
   (if needed)
       ↓
Deploy System
       ↓
Configure Credentials
       ↓
Verify Installation
       ↓
Start System
       ↓
✅ Complete!
```

**Time:** 15-20 minutes
**Commands:** 1 (interactive wizard)
**Yair effort:** Answer a few prompts

---

## 🎯 WHAT GETS DEPLOYED

Every new base is a **complete clone**:

```
✅ Backend Loop (29 modules)
✅ Money Printer + ABCFC
✅ 6 Autonomous Systems:
   • Communication
   • Payments
   • Remote Employees
   • Configuration
   • Optimization
   • Trading
✅ Self-Healing
✅ All dependencies
✅ Directory structure
✅ Environment config
```

---

## 🔑 CREDENTIAL OPTIONS

### Option 1: Copy from Current (Recommended)
```
Automatic, secure, fast
```

### Option 2: Enter Manually
```
Script prompts for each credential
```

### Option 3: Configure Later
```
Skip during deployment
Add manually afterwards
```

---

## ✅ POST-DEPLOYMENT COMMANDS

### Check if running
```bash
ssh <new_base> 'pgrep -f backend_loop'
```

### View live system
```bash
ssh <new_base> -t 'tmux attach -t hands-off'
```

### Check full status
```bash
ssh <new_base> 'cd /root/hands-off-engine && bash scripts/status.sh'
```

### View Money Printer
```bash
ssh <new_base> 'cat /root/hands-off-engine/state/money_printer.json'
```

### View logs
```bash
ssh <new_base> 'cd /root/hands-off-engine && tail -100 logs/*.log'
```

---

## 🏗️ EACH BASE IS INDEPENDENT

```
Base 1  ←→  No coordination  ←→  Base 2
  ↓              needed              ↓
Full            between            Full
System          bases              System
  ↓                                  ↓
Runs                               Runs
24/7                              24/7
```

**Benefits:**
- No single point of failure
- No complexity overhead
- Simple monitoring
- True redundancy
- Infinite scalability

---

## 💰 COST BREAKDOWN

### Oracle Cloud Free Tier (Recommended)
```
Cost: $0/month (forever)
Specs: 1 vCPU, 1GB RAM, 50GB storage
Perfect for: Each hands-off-engine base
ABCFC Score: 82.88 (highest)
```

### DigitalOcean (If more power needed)
```
Cost: $96/month
Specs: 8 vCPU, 16GB RAM, 320GB storage
Perfect for: Heavy compute if needed
```

### Current Architecture
```
Base 1 (Current): Running on DO @ $96/month
Base 2 (Deploy):  Oracle Free @ $0/month
Total: $96/month for 2 complete bases
```

---

## 🚨 COMMON ISSUES & FIXES

### "Cannot connect to SSH host"
```bash
# Check SSH config
cat ~/.ssh/config | grep base2

# Test connection
ssh base2 'echo Connected'

# Re-run provisioning if needed
bash scripts/provision_oracle_cloud.sh
```

### "Verification failed"
```bash
# Run verification with details
bash scripts/verify_new_base.sh <host>

# Check specific failures
ssh <host> 'cd /root/hands-off-engine && python3 --version'
ssh <host> 'cd /root/hands-off-engine && pip3 list'
```

### "System starts then stops"
```bash
# Check logs
ssh <host> 'cd /root/hands-off-engine && cat logs/*.log'

# Check credentials
ssh <host> 'cat /root/hands-off-engine/.env'

# Restart manually
ssh <host> 'cd /root/hands-off-engine && python3 autonomous/backend_loop.py'
```

---

## 📁 FILE STRUCTURE

```
scripts/
├── DEPLOY_NEW_BASE.sh ⭐ (USE THIS)
├── provision_oracle_cloud.sh
├── deploy_to_new_base.sh
├── verify_new_base.sh
├── complete_base2_setup.sh
└── monitor_dual_bases.sh

.deployment-ready/
├── README.md (full guide)
├── PRE_FLIGHT_CHECK.sh (readiness check)
└── QUICK_REFERENCE.md (this file)
```

---

## 🎯 DECISION TREE

```
Do you want redundancy?
  ↓ YES

Do you have 15 minutes?
  ↓ YES

Run: bash scripts/DEPLOY_NEW_BASE.sh
  ↓

Follow prompts
  ↓

Done! You have 2 bases running
```

---

## 💡 PRO TIPS

1. **Run pre-flight check first** - Catches issues early
2. **Copy credentials** - Fastest option (option 1)
3. **Use Oracle Free Tier** - $0 cost, perfect specs
4. **Let it run after deployment** - System is autonomous
5. **Monitor occasionally** - Not constantly
6. **Deploy more bases** - Easy to scale

---

## 🚀 READY?

```bash
bash scripts/DEPLOY_NEW_BASE.sh
```

That's the only command you need. The wizard handles the rest.

**Let's deploy! 🎉**
