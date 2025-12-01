# Self-Hosted GitHub Actions Runner Setup

## Overview

This guide explains how to set up a self-hosted GitHub Actions runner on the DigitalOcean droplet. This enables GitHub Actions workflows to run on the actual production environment where the Hands-Off Engine operates.

**Benefits:**
- Access to local state files and configurations
- Direct interaction with production services
- No need to replicate production environment in GitHub runners
- Can execute actions that require local credentials

**Security Considerations:**
- Runner has access to repository code and secrets
- Should only be used for trusted workflows
- Must be properly secured and monitored

---

## Prerequisites

- DigitalOcean droplet with SSH access
- Sudo/root privileges on the droplet
- GitHub repository admin access
- Stable internet connection on droplet

---

## Installation Steps

### 1. Create Runner on GitHub

1. Go to repository Settings > Actions > Runners
2. Click "New self-hosted runner"
3. Select Linux and architecture (usually x64)
4. **Note the commands provided** - you'll use these in the next steps

### 2. SSH into DO Droplet

```bash
ssh user@your-droplet-ip
```

### 3. Download and Configure Actions Runner

```bash
# Create a directory for the runner
mkdir -p ~/actions-runner && cd ~/actions-runner

# Download the latest runner package (use URL from GitHub UI)
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract the installer
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure the runner
# Use the token from GitHub UI (it expires after 1 hour)
./config.sh --url https://github.com/yaya1738/hands-off-engine --token YOUR_TOKEN_HERE

# When prompted:
# - Runner group: Default
# - Runner name: do-droplet (or custom name)
# - Labels: do-runner,production,hands-off (comma-separated)
# - Work folder: _work (default)
```

### 4. Install Runner as a Service

To ensure the runner starts automatically and stays running:

```bash
# Install the service
sudo ./svc.sh install

# Start the service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status
```

### 5. Verify Runner is Online

1. Go back to repository Settings > Actions > Runners
2. You should see your runner listed as "Idle"
3. Status should be green (online)

---

## Systemd Service Configuration

The runner service is installed as a systemd unit. You can manage it with:

```bash
# Check status
sudo systemctl status actions.runner.yaya1738-hands-off-engine.do-droplet.service

# Start/stop/restart
sudo systemctl start actions.runner.yaya1738-hands-off-engine.do-droplet.service
sudo systemctl stop actions.runner.yaya1738-hands-off-engine.do-droplet.service
sudo systemctl restart actions.runner.yaya1738-hands-off-engine.do-droplet.service

# View logs
sudo journalctl -u actions.runner.yaya1738-hands-off-engine.do-droplet.service -f
```

**Note:** The exact service name includes your repository and runner name.

---

## Using the Self-Hosted Runner in Workflows

To target the self-hosted runner, use labels in your workflow:

```yaml
jobs:
  deploy:
    runs-on: [self-hosted, do-runner, production]
    steps:
      - name: Deploy to production
        run: |
          # This runs on the DO droplet
          cd ~/hands-off
          git pull
          # ... deployment steps ...
```

**Labels to use:**
- `self-hosted` - Required for all self-hosted runners
- `do-runner` - Custom label for this runner
- `production` - Indicates production environment
- `hands-off` - Project-specific label

---

## Security Best Practices

### 1. Restrict Runner Usage

Only allow trusted workflows to use the self-hosted runner:

```yaml
# In workflow file
jobs:
  sensitive-job:
    runs-on: [self-hosted, do-runner]
    if: github.actor == 'yaya1738' || github.actor == 'copilot'
```

### 2. Environment Isolation

The runner should run as a dedicated user, not root:

```bash
# Create dedicated user for runner
sudo useradd -m -s /bin/bash github-runner

# Move runner to dedicated user's home
sudo mv ~/actions-runner /home/github-runner/
sudo chown -R github-runner:github-runner /home/github-runner/actions-runner

# Install service as that user
sudo su - github-runner
cd actions-runner
sudo ./svc.sh install github-runner
```

### 3. Network Security

Consider restricting the runner's network access:

```bash
# Example: Only allow GitHub and specific services
sudo ufw allow from <github-ip-range>
sudo ufw allow out to <required-services>
```

### 4. Regular Updates

Keep the runner software updated:

```bash
cd ~/actions-runner
./run.sh  # Check for updates
# If update available, download and extract new version
```

### 5. Monitoring

Add monitoring for the runner service:

```bash
# Add to self-healing agent or cron
#!/bin/bash
if ! systemctl is-active --quiet actions.runner.*; then
  echo "GitHub Actions runner is down"
  # Send alert to Telegram
  # Attempt restart
  sudo systemctl restart actions.runner.*
fi
```

---

## Workflow Examples

### Example 1: Deploy to DO Droplet

```yaml
name: Deploy to Production

on:
  workflow_dispatch:

jobs:
  deploy:
    runs-on: [self-hosted, do-runner]
    steps:
      - name: Pull latest code
        run: |
          cd ~/hands-off-engine
          git pull origin main

      - name: Restart services
        run: |
          # Restart relevant services
          systemctl --user restart hands-off-pipeline
```

### Example 2: Run Health Check Locally

```yaml
name: Local Health Check

on:
  schedule:
    - cron: '0 * * * *'

jobs:
  health-check:
    runs-on: [self-hosted, do-runner]
    steps:
      - name: Check system health
        run: |
          cd ~/hands-off-engine
          python3 scripts/self_healing_agent.py
```

---

## Troubleshooting

### Runner Shows Offline

1. Check service status:
   ```bash
   sudo systemctl status actions.runner.*
   ```

2. Check logs:
   ```bash
   sudo journalctl -u actions.runner.* -n 50
   ```

3. Restart service:
   ```bash
   sudo systemctl restart actions.runner.*
   ```

### Runner Not Picking Up Jobs

1. Verify labels match in workflow
2. Check runner is idle (not running other jobs)
3. Ensure repository has permission to use runner

### Authentication Issues

If runner loses connection:

```bash
# Remove old configuration
cd ~/actions-runner
./config.sh remove --token YOUR_REMOVAL_TOKEN

# Re-configure with new token
./config.sh --url https://github.com/yaya1738/hands-off-engine --token NEW_TOKEN
```

### Disk Space Issues

Runners can accumulate cache and work files:

```bash
# Clean up work directory
cd ~/actions-runner
rm -rf _work/*

# Clean up Docker if used
docker system prune -af
```

---

## Maintenance Checklist

Regular maintenance tasks:

- [ ] Weekly: Check runner service status
- [ ] Monthly: Review runner logs for errors
- [ ] Monthly: Clean up work directory
- [ ] Quarterly: Update runner software
- [ ] As needed: Rotate runner tokens
- [ ] As needed: Review and update labels

---

## Removal

To completely remove the runner:

```bash
# Stop the service
sudo ./svc.sh stop

# Uninstall the service
sudo ./svc.sh uninstall

# Remove configuration
./config.sh remove --token YOUR_REMOVAL_TOKEN

# Delete runner directory
cd ~
rm -rf actions-runner
```

Then remove the runner from GitHub repository settings.

---

## Alternative: Ephemeral Runners

For enhanced security, consider using ephemeral runners that are destroyed after each job:

```bash
# Configure as ephemeral
./config.sh --url https://github.com/yaya1738/hands-off-engine \
  --token YOUR_TOKEN \
  --ephemeral

# Run once (will exit after job)
./run.sh
```

Use with a script that recreates the runner after each job.

---

## Summary

A self-hosted runner on the DO droplet enables:
- ✅ Direct access to production environment
- ✅ Automated deployments and health checks
- ✅ Integration with existing automation
- ⚠️ Requires careful security configuration
- ⚠️ Needs regular maintenance and monitoring

---

**Last Updated:** 2025-12-01  
**Maintained By:** Repository owner  
**Related Workflows:**
- `.github/workflows/deploy.yml`
- `.github/workflows/scheduled-health.yml`
