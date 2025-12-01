# GitHub Spark Integration

## Overview

GitHub Spark is an AI-powered platform for building full-stack apps via natural language. This document describes how to use Spark to create monitoring tools, dashboards, and control panels for the Hands-Off Engine.

---

## Use Cases for Hands-Off Engine

### 1. Trading Dashboard Spark
Build a real-time dashboard showing:
- Current positions from `state/polymarket-model.json`
- Execution history from `logs/`
- Alpha signals visualization
- P&L tracking over time

**Value:** Quick visual insight into trading performance without SSH/CLI.

### 2. Agent Status Monitor Spark
A micro-app displaying:
- Multi-agent coordination status
- Recent messages from `ai/coordination/messages.jsonl`
- System health metrics
- Active tasks and their status

**Value:** See what all AI agents are doing at a glance.

### 3. Risk Control Panel Spark
Quick tool for:
- Viewing current risk limits
- Emergency stop button (triggers repository_dispatch)
- Position sizing calculator
- Manual trade approval interface

**Value:** Safety controls accessible from mobile/web.

---

## How to Create a Spark

1. Go to [github.com/spark](https://github.com/spark)
2. Describe your app in natural language (see scaffolds in `spark/` directory)
3. Connect to `yaya1738/hands-off-engine` repo
4. Spark generates the app code automatically
5. Deploy and share

**Note:** Spark apps are ephemeral prototypes. For production tools, build properly in the repo.

---

## Spark → GitHub Actions Integration

Sparks can trigger workflows via `repository_dispatch` events:

### Emergency Stop
```javascript
fetch('https://api.github.com/repos/yaya1738/hands-off-engine/dispatches', {
  method: 'POST',
  headers: {
    'Authorization': 'token GITHUB_PERSONAL_ACCESS_TOKEN',
    'Accept': 'application/vnd.github.v3+json'
  },
  body: JSON.stringify({
    event_type: 'spark_emergency_stop',
    client_payload: {
      user: 'AUTHENTICATED_USERNAME',
      reason: 'Manual emergency stop'
    }
  })
})
```

### Approve Trade
```javascript
fetch('https://api.github.com/repos/yaya1738/hands-off-engine/dispatches', {
  method: 'POST',
  headers: {
    'Authorization': 'token GITHUB_PERSONAL_ACCESS_TOKEN',
    'Accept': 'application/vnd.github.v3+json'
  },
  body: JSON.stringify({
    event_type: 'spark_approve_trade',
    client_payload: {
      user: 'AUTHENTICATED_USERNAME',
      trade_id: 'trade_12345'
    }
  })
})
```

### Health Check
```javascript
fetch('https://api.github.com/repos/yaya1738/hands-off-engine/dispatches', {
  method: 'POST',
  headers: {
    'Authorization': 'token GITHUB_PERSONAL_ACCESS_TOKEN',
    'Accept': 'application/vnd.github.v3+json'
  },
  body: JSON.stringify({
    event_type: 'spark_health_check',
    client_payload: {
      user: 'AUTHENTICATED_USERNAME'
    }
  })
})
```

---

## Reading Data from the Repository

Spark apps can fetch data from the repository using GitHub's API:

```javascript
// Fetch current positions
const response = await fetch('https://api.github.com/repos/yaya1738/hands-off-engine/contents/state/polymarket-model.json', {
  headers: {
    'Authorization': 'token GITHUB_PERSONAL_ACCESS_TOKEN',
    'Accept': 'application/vnd.github.v3.raw'
  }
})
const positions = await response.json()
```

```javascript
// Fetch recent coordination messages
const response = await fetch('https://api.github.com/repos/yaya1738/hands-off-engine/contents/ai/coordination/messages.jsonl', {
  headers: {
    'Authorization': 'token GITHUB_PERSONAL_ACCESS_TOKEN',
    'Accept': 'application/vnd.github.v3.raw'
  }
})
const messagesText = await response.text()
const messages = messagesText.split('\n').filter(l => l).map(JSON.parse)
```

---

## Security Considerations

1. **Token Management:** Spark apps need a GitHub token with `repo` scope
   - Create a fine-grained personal access token
   - Limit to `yaya1738/hands-off-engine` repository
   - Grant read access for data fetching
   - Grant write access for triggering workflows

2. **Emergency Stop:** The emergency stop button should require confirmation
   - Use a modal/dialog before triggering
   - Display warning about stopping live trading

3. **Data Privacy:** Don't expose sensitive data in Spark apps
   - Avoid showing API keys or secrets
   - Consider masking trade amounts
   - Use authentication for Spark apps

---

## Example Spark Scaffolds

See the `spark/` directory for example prompts:
- `spark/trading_dashboard.md` - Trading performance dashboard
- `spark/agent_monitor.md` - Multi-agent coordination monitor

Copy these prompts into GitHub Spark to generate the apps.

---

## Limitations

- Spark apps are prototypes, not production tools
- Data fetching requires GitHub API token
- No direct SSH access to droplet (use GitHub Actions as intermediary)
- Spark apps may have rate limits on GitHub API calls

---

## Future Enhancements

- [ ] Add Spark app for manual trade entry
- [ ] Create Spark notification dashboard (all Telegram messages)
- [ ] Build Spark app for reviewing and approving AI agent PRs
- [ ] Develop Spark configuration editor for risk parameters

---

**Last Updated:** 2025-12-01
**Maintained By:** Copilot Agent
