# GitHub Setup Automation Scripts

Automated GitHub repository configuration for the Hands-Off Engine. Eliminates ALL manual setup steps via GitHub API.

## Philosophy

**Zero human touch.** Everything should be configurable via scripts and workflows.

## Scripts

### Configuration Scripts

#### `configure_branch_protection.py`
Configures branch protection on `main`:
- Required status checks (ci workflow)
- Required PR reviews (1 reviewer, dismiss stale)
- No force pushes
- No deletions
- Bypass rules for trusted bots

**Usage:**
```bash
GITHUB_TOKEN=<token> python scripts/github_setup/configure_branch_protection.py
```

#### `configure_environments.py`
Creates GitHub Environments:
- `staging` - No protection (for DRYRUN)
- `production` - Requires approval (for LIVE)

**Usage:**
```bash
GITHUB_TOKEN=<token> python scripts/github_setup/configure_environments.py
```

#### `configure_security.py`
Enables security features:
- Secret scanning
- Secret scanning push protection
- Dependabot security updates
- Dependabot version updates

**Usage:**
```bash
GITHUB_TOKEN=<token> python scripts/github_setup/configure_security.py
```

#### `configure_project.py`
Creates project board "Hands-Off Engine Kanban" via GraphQL API.

**Usage:**
```bash
GITHUB_TOKEN=<token> python scripts/github_setup/configure_project.py
```

**Note:** Projects V2 have limited API automation. Some manual configuration needed.

### Runner Setup

#### `get_runner_token.py`
Gets a GitHub Actions runner registration token.

**Usage:**
```bash
GITHUB_TOKEN=<token> python scripts/github_setup/get_runner_token.py
```

Outputs token to stdout for use by setup script.

#### `setup_self_hosted_runner.sh`
Installs GitHub Actions runner on Ubuntu server.

**Usage:**
```bash
# On the droplet as root:
RUNNER_TOKEN=<token> REPO=owner/repo bash setup_self_hosted_runner.sh
```

Installs runner as systemd service with labels: `self-hosted`, `linux`, `droplet`

### Status Checking

#### `check_setup_status.py`
Checks current configuration status and outputs JSON.

**Usage:**
```bash
GITHUB_TOKEN=<token> python scripts/github_setup/check_setup_status.py
```

**Output:**
```json
{
  "repository": "owner/repo",
  "timestamp": "2025-12-01T17:00:00Z",
  "branch_protection": {
    "enabled": true,
    "status_checks": true,
    "pr_reviews": true
  },
  "environments": {
    "staging": true,
    "production": true,
    "total": 2
  },
  "security": {
    "secret_scanning": true,
    "dependabot_alerts": true
  },
  "runners": {
    "total": 1,
    "online": 1,
    "runners": [...]
  }
}
```

## Workflows

### `repo-setup.yml`
Master workflow that runs all configuration scripts.

**Triggers:**
- Manual (`workflow_dispatch`)
- Weekly schedule (Sunday midnight UTC)
- Repository dispatch (`telegram_trigger_setup`)

**Usage:**
```bash
# Manual trigger
gh workflow run repo-setup.yml

# With options
gh workflow run repo-setup.yml --field skip_project=true
```

### `deploy-runner.yml`
Deploys self-hosted runner to DigitalOcean droplet via SSH.

**Triggers:**
- Manual (`workflow_dispatch`)
- Repository dispatch (`telegram_trigger_runner`)

**Usage:**
```bash
gh workflow run deploy-runner.yml --field droplet_ip=do138
```

**Requirements:**
- `DO_SSH_KEY` secret (SSH private key)
- SSH access to droplet
- Droplet running Ubuntu

## Telegram Integration

The Telegram bot can trigger these workflows. See [TELEGRAM_INTEGRATION.md](TELEGRAM_INTEGRATION.md) for details.

**Commands:**
- `/setup github` - Trigger repo configuration
- `/setup runner <ip>` - Deploy runner to droplet
- `/setup status` - Check configuration status

## Token Permissions

### GITHUB_TOKEN (default)
Available in GitHub Actions, has limited permissions:
- ✅ Read repository
- ✅ Read/write issues and PRs
- ❌ Admin repository (branch protection, environments)
- ❌ Create runners

### ADMIN_TOKEN (recommended)
Personal Access Token with `admin:repo` scope:
- ✅ All GITHUB_TOKEN permissions
- ✅ Configure branch protection
- ✅ Create/manage environments
- ✅ Create runner tokens

**To use:** Add as repository secret named `ADMIN_TOKEN`

Scripts will try `GITHUB_TOKEN` first, then `ADMIN_TOKEN` if needed.

## Logs

All scripts log to `logs/github_setup.jsonl` for audit trail.

**Format:**
```json
{
  "timestamp": "2025-12-01T17:00:00Z",
  "script": "configure_branch_protection",
  "action": "configure_protection",
  "status": "success",
  "details": {...}
}
```

## Idempotency

All scripts are safe to run multiple times:
- Check before creating
- Update if exists
- Log all actions

## Error Handling

Scripts gracefully degrade:
- Continue with other features if one fails
- Log errors with context
- Exit with appropriate status code
- Clear error messages

## Dependencies

- Python 3.11+
- `requests` library

Install:
```bash
pip install requests
```

## Development

### Testing Scripts Locally

```bash
# Set up environment
export GITHUB_TOKEN=<your-token>
export GITHUB_REPOSITORY=owner/repo

# Run scripts
python scripts/github_setup/configure_branch_protection.py
python scripts/github_setup/check_setup_status.py
```

### Adding New Scripts

1. Create script in `scripts/github_setup/`
2. Make executable: `chmod +x script.py`
3. Add logging to `logs/github_setup.jsonl`
4. Add idempotency checks
5. Add to workflow in `.github/workflows/repo-setup.yml`
6. Update this README

## Troubleshooting

### "Permission denied" errors
- Check token has required scopes
- Use `ADMIN_TOKEN` instead of `GITHUB_TOKEN`
- Verify you have admin access to repository

### Branch protection not working
- Requires admin access
- Create PAT with `admin:repo` scope
- Add as `ADMIN_TOKEN` secret

### Runner deployment fails
- Verify `DO_SSH_KEY` secret is set
- Check droplet IP/hostname is correct
- Ensure droplet is running Ubuntu
- Verify SSH access: `ssh root@<droplet-ip>`

### Environment creation fails
- Some features require paid GitHub plan
- Private repos may have limitations
- Check repository settings

## References

- [GitHub REST API](https://docs.github.com/en/rest)
- [GitHub GraphQL API](https://docs.github.com/en/graphql)
- [GitHub Actions Runner](https://github.com/actions/runner)
- [Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
