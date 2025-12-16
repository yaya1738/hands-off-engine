# MASTER ACCESS DOCUMENT - Yair Siegel
## CONFIDENTIAL - DO NOT SHARE

**Last Updated:** 2025-11-30
**Owner:** Yair Siegel (siegel.yaz@gmail.com)

---

## SSH ACCESS

### Authorized Keys (YOUR KEYS ONLY)
```
# pm-helper server key (inter-server)
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKUOlcMgjyYnAknQhzB/hHMZewPEx7XPLAd/Q2vLt1JD handsoff-do138

# Termux/Phone
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA8ae2bwqf597DPpmEa76Wi3GxTRkSE432p6d6L5pPPY pm-agent
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBpjBQaUbCWCbHjcA1ijILa6rkZ+R1bY3jxifvU1zaOS termux@handsoff
```

### Server Access
| Server | IP | SSH Command |
|--------|-----|-------------|
| pm-helper | 138.68.103.156 | `ssh root@138.68.103.156` |
| ho-cli-main | 167.172.132.72 | `ssh root@167.172.132.72` or `ho` |
| ho-compute-1 | 167.172.155.42 | `ssh root@167.172.155.42` |
| ho-compute-2 | 178.128.155.150 | `ssh root@178.128.155.150` |
| ho-scale-* | 64.227.26.112 | `ssh root@64.227.26.112` |
| ho-topdawg-4 | 157.230.221.18 | `ssh root@157.230.221.18` |

---

## API CREDENTIALS

### DigitalOcean
- **Token:** `dop_v1_e08e7243de8b4abe69c76767f17919de4caacc2889135d0d9e558e6f300d22be`
- **Location:** `/root/hands-off-engine/.env`

### OpenAI
- **Key:** In `.env` file
- **Location:** `/root/hands-off-engine/.env`

### Anthropic/Claude
- **Auth:** OAuth via Claude CLI
- **Location:** `/root/.claude/.credentials.json`

### Polymarket
- **Wallet:** 0xb6781D9278c60dC3CE8c3E355Cd04142da3BF74D
- **Keys:** `/root/hands-off-engine/.env.polymarket`

### GitHub
- **Access:** SSH key (no PAT configured)
- **Repo:** git@github.com:yaya1738/hands-off-engine.git

---

## SECURITY SETTINGS

### SSH Hardening (Applied)
- Password authentication: **DISABLED**
- Root login: Only via SSH key
- Authorized keys: Only your 3 keys above

### Firewall Rules
- Port 22: SSH (open)
- Port 80/443: HTTP/HTTPS (open)
- Port 8000-8081: Internal services

---

## RECOVERY

### If Locked Out:
1. DigitalOcean Console: https://cloud.digitalocean.com
2. Account: siegel.yaz@gmail.com
3. Use console access to add SSH key back

### Backup Keys Location:
1. Your phone (Termux)
2. DigitalOcean account (pm-helper-key, pm-agent-termux)

---

## QUICK COMMANDS

```bash
# Access CLI server
ho

# Check all droplets
doctl compute droplet list

# System status
systemctl status mega-coordinator master-controller
```

---

**IMPORTANT:** This file contains sensitive credentials. Keep secure.
