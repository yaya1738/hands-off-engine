# GitHub Apps and Integrations

This document explains the GitHub Apps, integrations, and automation features used in the Hands-Off Engine project.

## Overview

The Hands-Off Engine leverages GitHub's built-in apps and features to achieve zero-touch automation and robust security. This aligns with the project's multi-agent coordination architecture where changes flow automatically while maintaining safety.

## GitHub Apps in Use

### 1. Dependabot

**Purpose:** Automated dependency updates  
**Status:** ✅ Configured  
**Configuration:** `.github/dependabot.yml`

#### What It Does

- Monitors Python dependencies in `ai/requirements.txt`
- Monitors GitHub Actions versions in `.github/workflows/`
- Creates PRs weekly (Mondays at 09:00 UTC) for outdated dependencies
- Labels PRs with `dependencies`, `python`, or `github-actions`, and `auto-merge`

#### Integration with Auto-Merge

Dependabot PRs are automatically merged when:
1. All CI checks pass
2. PR is marked ready for review (not draft)
3. No merge conflicts exist

The auto-merge workflow (`.github/workflows/auto-merge.yml`) includes `dependabot[bot]` in the trusted authors list:

```yaml
env:
  TRUSTED_AUTHORS: "copilot,github-actions[bot],dependabot[bot]"
```

#### Configuration

```yaml
# .github/dependabot.yml
updates:
  - package-ecosystem: "pip"
    directory: "/ai"
    schedule:
      interval: "weekly"
  
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

#### Benefits

- ✅ Keeps dependencies up-to-date automatically
- ✅ Reduces security vulnerabilities
- ✅ No manual intervention needed
- ✅ Works seamlessly with auto-merge

#### Monitoring

Check Dependabot status:
- GitHub UI: Insights → Dependency graph → Dependabot
- PRs labeled `dependencies`
- Security alerts for vulnerable dependencies

### 2. CodeQL (Security Scanning)

**Purpose:** Static code analysis for security vulnerabilities  
**Status:** ✅ Configured  
**Configuration:** `.github/workflows/codeql-analysis.yml`

#### What It Does

- Analyzes Python code for security issues
- Runs on every push to `main` branch
- Runs on every pull request
- Scheduled weekly scans (Mondays at 10:00 UTC)
- Uses `security-extended` query suite for comprehensive analysis

#### Critical for This Project

The Hands-Off Engine handles:
- API keys (Alpaca, OpenAI, Telegram, Polymarket)
- Trading credentials
- Financial operations
- Real money transactions (in LIVE mode)

Security is paramount. CodeQL helps detect:
- SQL injection vulnerabilities
- Command injection risks
- Path traversal issues
- Hardcoded credentials
- Insecure random number generation
- And 200+ other security patterns

#### Workflow

```yaml
# .github/workflows/codeql-analysis.yml
on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]
  schedule:
    - cron: '0 10 * * 1'  # Weekly on Mondays
```

#### Alerts

View security alerts:
- GitHub UI: Security → Code scanning
- Filter by severity: Critical, High, Medium, Low
- Click alerts for remediation guidance

#### Integration with Development

- CodeQL results appear in PR checks
- Blocks merge if critical issues found (optional)
- Provides remediation suggestions
- Links to CWE (Common Weakness Enumeration) entries

### 3. Secret Scanning

**Purpose:** Detect and prevent secret exposure  
**Status:** ✅ Enabled (GitHub native)  
**Documentation:** `docs/SECRET_SCANNING.md`

#### What It Does

- Scans all commits for over 200 secret patterns
- Alerts when secrets are detected
- Push protection blocks commits with secrets (if enabled)
- Partner notification for service providers (e.g., OpenAI can auto-revoke)

#### Covered Secrets

- API keys (OpenAI, Anthropic, AWS, etc.)
- Database credentials
- SSH keys
- OAuth tokens
- Telegram bot tokens
- Generic secrets (high entropy strings)

#### Responding to Alerts

1. **Review:** Security → Secret scanning
2. **Revoke:** Immediately invalidate the credential
3. **Remove:** Clean from git history if needed
4. **Prevent:** Add to `.gitignore`, use environment variables

See `docs/SECRET_SCANNING.md` for detailed procedures.

### 4. GitHub Environments

**Purpose:** Deployment protection for DRYRUN/LIVE modes  
**Status:** 📝 Documented (manual setup required)  
**Documentation:** `docs/GITHUB_ENVIRONMENTS.md`

#### Environments

**Staging (DRYRUN Mode):**
- No protection rules
- Auto-deploy enabled
- Test credentials
- Safe for automation

**Production (LIVE Mode):**
- Manual approval required
- Tagged reviewers must approve
- Real trading credentials
- Changes require human verification

#### Protection Against Accidents

- ✅ Prevents automated LIVE trading from PRs
- ✅ Requires approval for production deployments
- ✅ Separates test and real credentials
- ✅ Audit trail for all deployments

#### Setup

Environments must be configured manually in GitHub UI:
1. Settings → Environments → New environment
2. Configure protection rules
3. Add environment secrets

See `docs/GITHUB_ENVIRONMENTS.md` for step-by-step instructions.

### 5. GitHub Actions (Workflows)

**Purpose:** CI/CD automation  
**Status:** ✅ Active  
**Files:** `.github/workflows/*.yml`

#### Current Workflows

1. **Auto-merge** (`auto-merge.yml`):
   - Automatically merges trusted PRs
   - Trusts: Copilot, GitHub Actions, Dependabot
   - Checks: All tests pass, no conflicts
   - Enables zero-touch repo management

2. **AI Intake** (`ai-intake.yml`):
   - Responds to issue comments
   - Part of AI Agent Link Protocol
   - Enables ChatGPT → Copilot coordination

3. **CodeQL Analysis** (`codeql-analysis.yml`):
   - Security scanning (described above)

4. **Agent Coordination Notify** (`agent-coordination-notify.yml`):
   - Notifies on coordination file changes
   - Part of multi-agent system

#### Adding New Workflows

Follow existing patterns:
- Use `actions/checkout@v4` for checkout
- Use `actions/setup-python@v5` for Python
- Specify `python-version: "3.11"` or newer
- Use semantic job names
- Add comments explaining purpose
- Include `workflow_dispatch` for manual triggers

## Automation Flow

### Normal PR Flow (Automated)

```
Developer creates PR
    ↓
Copilot/Dependabot creates PR
    ↓
CodeQL scans for vulnerabilities
    ↓
All checks pass
    ↓
Auto-merge workflow merges PR
    ↓
Changes deployed to staging (DRYRUN)
```

### LIVE Deployment Flow (Manual Approval)

```
Staging deployment succeeds
    ↓
Developer triggers production deployment
    ↓
GitHub pauses for approval
    ↓
Reviewer checks changes
    ↓
Reviewer approves
    ↓
Deployment to production (LIVE)
    ↓
Telegram notification sent
```

## Security Architecture

### Layers of Protection

1. **Pre-commit:** Local checks (linting, tests)
2. **Secret Scanning:** Blocks secrets in commits
3. **CodeQL:** Analyzes code for vulnerabilities
4. **Auto-merge:** Only trusted sources
5. **Environments:** Manual approval for LIVE
6. **Audit Log:** Track all security events

### Defense in Depth

Each layer catches different issues:
- Pre-commit → Syntax, style
- Secret scanning → Credential leaks
- CodeQL → Logic vulnerabilities
- Auto-merge → Untrusted changes
- Environments → Unauthorized deployments
- Audit log → Post-incident investigation

## Multi-Agent Coordination

### GitHub Apps Enable Autonomous Operation

The GitHub Apps integrate with the multi-agent architecture:

**Agents:**
- GitHub Copilot (code generation)
- ChatGPT (planning, coordination)
- Claude CLI (implementation)
- GitHub Actions (automation)

**Coordination via GitHub:**
- Issues for task tracking
- PRs for code changes
- Workflows for automation
- Environments for safety

**Benefits:**
- Agents work independently
- Changes reviewed automatically
- Safety checks always enforced
- Human approval only when needed

## Monitoring and Maintenance

### Weekly Checks

- [ ] Review Dependabot PRs (auto-merged if passing)
- [ ] Check CodeQL alerts (Security tab)
- [ ] Audit secret scanning alerts
- [ ] Review auto-merged PRs
- [ ] Verify environment configurations

### Monthly Audits

- [ ] Review all GitHub App configurations
- [ ] Audit access to production environment
- [ ] Rotate long-lived credentials
- [ ] Check workflow run history
- [ ] Update this documentation if needed

### Metrics to Monitor

Track in `scripts/meta_metrics.py`:
- Dependabot PR merge rate
- CodeQL alert trends
- Secret scanning false positive rate
- Auto-merge success rate
- Production deployment frequency

## Troubleshooting

### Dependabot Issues

**Problem:** Dependabot PRs not created  
**Solution:**
- Check `.github/dependabot.yml` syntax
- Verify `ai/requirements.txt` exists
- Check Dependabot logs in Insights

**Problem:** Dependabot PRs not auto-merging  
**Solution:**
- Verify PR has `auto-merge` label
- Check if all CI checks passed
- Confirm no merge conflicts
- Review auto-merge workflow logs

### CodeQL Issues

**Problem:** CodeQL workflow failing  
**Solution:**
- Check Python syntax (CodeQL scans valid code)
- Review workflow logs for errors
- Verify `security-extended` queries are compatible
- Try `default` queries if extended fail

**Problem:** Too many false positives  
**Solution:**
- Add suppressions for specific alerts
- Adjust query suite (use `default` instead of `security-extended`)
- Document why alert is false positive

### Secret Scanning Issues

**Problem:** False positive alerts  
**Solution:**
- Close alert as "False positive"
- Document reasoning
- Consider using test fixtures instead of realistic-looking fake data

**Problem:** Real secret detected  
**Solution:**
- Follow incident response procedure (see `docs/SECRET_SCANNING.md`)
- Revoke credential immediately
- Remove from git history
- Update security practices

## Future Enhancements

Potential improvements:
- [ ] Enable push protection for secret scanning
- [ ] Add custom CodeQL queries for trading logic
- [ ] Automate environment setup via GitHub API
- [ ] Add deployment preview environments
- [ ] Integration tests in staging before production
- [ ] Automated rollback on production failures

## Resources

### Official Documentation

- [Dependabot](https://docs.github.com/en/code-security/dependabot)
- [CodeQL](https://codeql.github.com/docs/)
- [Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments)
- [GitHub Actions](https://docs.github.com/en/actions)

### Project Documentation

- `docs/GITHUB_ENVIRONMENTS.md` - Environment setup guide
- `docs/SECRET_SCANNING.md` - Secret detection and response
- `docs/DEVELOPMENT_STANDARDS.md` - Development best practices
- `docs/AI_AGENT_LINK_PROTOCOL_v0.1.md` - Multi-agent coordination

---

**Last Updated:** 2025-12-01  
**Maintained By:** Hands-Off Engine Team  
**Status:** Living document (update as integrations evolve)
