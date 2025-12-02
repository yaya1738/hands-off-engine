# GitHub Setup Automation - Telegram Bot Integration

## Overview
The Telegram bot can trigger GitHub repository setup workflows via the repository_dispatch API.

## New Commands to Add

### `/setup github`
Triggers the repo-setup workflow to configure:
- Branch protection rules
- GitHub Environments
- Security features
- Project boards

**Implementation:**
```python
async def handle_setup_github(update, context):
    """Trigger GitHub repository auto-configuration."""
    # Send repository_dispatch event
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "event_type": "telegram_trigger_setup"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 204:
        await update.message.reply_text(
            "✅ GitHub setup workflow triggered\n"
            "Check Actions tab for progress"
        )
    else:
        await update.message.reply_text(
            f"❌ Failed to trigger workflow: {response.status_code}"
        )
```

### `/setup runner <ip>`
Triggers the deploy-runner workflow to install runner on droplet.

**Implementation:**
```python
async def handle_setup_runner(update, context):
    """Deploy self-hosted runner to droplet."""
    if not context.args:
        await update.message.reply_text(
            "Usage: /setup runner <droplet_ip>\n"
            "Example: /setup runner do138"
        )
        return
    
    droplet_ip = context.args[0]
    
    # Trigger workflow via repository_dispatch
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "event_type": "telegram_trigger_runner",
        "client_payload": {
            "droplet_ip": droplet_ip
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 204:
        await update.message.reply_text(
            f"✅ Runner deployment triggered for {droplet_ip}\n"
            "Check Actions tab for progress"
        )
    else:
        await update.message.reply_text(
            f"❌ Failed to trigger workflow: {response.status_code}"
        )
```

### `/setup status`
Shows current GitHub configuration status.

**Implementation:**
```python
async def handle_setup_status(update, context):
    """Check GitHub repository setup status."""
    # Call check_setup_status.py script
    import subprocess
    import json
    
    result = subprocess.run(
        ["python", "scripts/github_setup/check_setup_status.py"],
        capture_output=True,
        text=True,
        env={**os.environ, "GITHUB_TOKEN": GITHUB_TOKEN}
    )
    
    if result.returncode == 0:
        status = json.loads(result.stdout)
        
        # Format status message
        msg = "📊 GitHub Repository Status\n\n"
        
        # Branch protection
        bp = status.get("branch_protection", {})
        if bp.get("enabled"):
            msg += "✅ Branch Protection: Enabled\n"
        else:
            msg += "❌ Branch Protection: Not configured\n"
        
        # Environments
        envs = status.get("environments", {})
        msg += f"🏗️ Environments: {envs.get('total', 0)}\n"
        if envs.get("staging"):
            msg += "  ✅ staging\n"
        if envs.get("production"):
            msg += "  ✅ production\n"
        
        # Security
        sec = status.get("security", {})
        msg += "🔒 Security:\n"
        if sec.get("secret_scanning"):
            msg += "  ✅ Secret scanning\n"
        if sec.get("dependabot_alerts"):
            msg += "  ✅ Dependabot alerts\n"
        
        # Runners
        runners = status.get("runners", {})
        msg += f"🏃 Runners: {runners.get('total', 0)} "
        msg += f"({runners.get('online', 0)} online)\n"
        
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text(
            f"❌ Failed to get status:\n{result.stderr}"
        )
```

## Required Configuration

### Environment Variables
Add to Telegram bot environment:
```bash
GITHUB_TOKEN=<personal access token with workflow permissions>
OWNER=<repository owner>
REPO=<repository name>
```

### Command Registration
Add to command handlers in `telegram_command_bot.py`:
```python
application.add_handler(CommandHandler("setup", handle_setup_command))

async def handle_setup_command(update, context):
    """Route setup subcommands."""
    if not context.args:
        await update.message.reply_text(
            "Available setup commands:\n"
            "/setup github - Configure repository\n"
            "/setup runner <ip> - Deploy runner to droplet\n"
            "/setup status - Check configuration status"
        )
        return
    
    subcommand = context.args[0]
    if subcommand == "github":
        await handle_setup_github(update, context)
    elif subcommand == "runner":
        await handle_setup_runner(update, context[1:])
    elif subcommand == "status":
        await handle_setup_status(update, context)
    else:
        await update.message.reply_text(f"Unknown subcommand: {subcommand}")
```

## Workflow Triggers

The workflows also need to listen for repository_dispatch events:

### repo-setup.yml
Add to `on:` section:
```yaml
on:
  workflow_dispatch:
  schedule:
    - cron: '0 0 * * 0'
  repository_dispatch:
    types: [telegram_trigger_setup]
```

### deploy-runner.yml  
Add to `on:` section:
```yaml
on:
  workflow_dispatch:
  repository_dispatch:
    types: [telegram_trigger_runner]
```

And use the payload:
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Get droplet IP
        id: droplet
        run: |
          if [ "${{ github.event_name }}" == "repository_dispatch" ]; then
            echo "ip=${{ github.event.client_payload.droplet_ip }}" >> $GITHUB_OUTPUT
          else
            echo "ip=${{ github.event.inputs.droplet_ip }}" >> $GITHUB_OUTPUT
          fi
      
      - name: Deploy
        run: |
          # Use ${{ steps.droplet.outputs.ip }} for droplet IP
```

## Testing

Test the Telegram commands:
```
/setup status
/setup github
/setup runner do138
```

Check workflow runs in the Actions tab.
