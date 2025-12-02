# Spark App Scaffolds

This directory contains templates for creating GitHub Spark applications that integrate with the Hands-Off Engine.

## What is GitHub Spark?

GitHub Spark is an AI-powered platform for building full-stack apps via natural language. You describe what you want, and Spark generates the code.

## How to Use These Scaffolds

1. Go to [github.com/spark](https://github.com/spark)
2. Copy the entire content of one of the `.md` files below
3. Paste it into Spark's prompt
4. Connect to the `yaya1738/hands-off-engine` repository
5. Spark will generate the app automatically

## Available Scaffolds

### Trading Dashboard (`trading_dashboard.md`)
A real-time dashboard showing:
- Current positions and bankroll
- Recent trades table
- P&L chart
- Alpha signals feed
- Emergency stop button

**Use case:** Quick visual overview of trading performance

### Agent Monitor (`agent_monitor.md`)
A monitoring tool showing:
- Status of all AI agents (Copilot, Claude, ChatGPT)
- Recent coordination messages
- Active tasks
- System health metrics

**Use case:** See what all AI agents are doing at a glance

## Integration with Repository

These Spark apps can:

### Read Data
- Fetch state files via GitHub API
- Parse logs and coordination files
- Display real-time system status

### Trigger Actions
- Send webhooks via `repository_dispatch`
- Trigger emergency stop
- Approve trades
- Request health checks

See `docs/GITHUB_SPARK_INTEGRATION.md` for full integration guide.

## Customizing

These scaffolds are starting points. You can:
- Add more features
- Change the styling
- Modify the data sources
- Add new webhook actions

Just edit the prompt and regenerate in Spark.

## Security Notes

- Spark apps need GitHub API tokens
- Use fine-grained tokens with minimal permissions
- Only grant read access unless write is needed
- Consider adding authentication to Spark apps

## Future Spark App Ideas

- [ ] Manual trade entry form
- [ ] Notification dashboard (all Telegram messages)
- [ ] PR review and approval interface
- [ ] Risk parameter configuration editor
- [ ] System log viewer and search
- [ ] Performance analytics dashboard

---

**Last Updated:** 2025-12-01
**Maintained By:** Copilot Agent
