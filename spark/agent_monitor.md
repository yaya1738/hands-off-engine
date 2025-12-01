# Agent Status Monitor Spark

Build a monitoring dashboard showing:

## Header
- Title: "Hands-Off AI Agent Monitor"
- System health indicator
- Last system update timestamp

## Main Content

### Agent Status Grid
Four cards, one for each agent:
1. **Copilot Agent**
2. **Claude Code Agent**
3. **ChatGPT Agent**
4. **Claude Web Agent**

Each card shows:
- Agent name with icon
- Status indicator:
  - 🟢 Green: Active (worked in last hour)
  - 🟡 Yellow: Idle (worked in last 24h)
  - 🔴 Red: Error or inactive (no activity >24h)
- Last action description
- Time since last action (e.g., "5 minutes ago")
- Click card to see detailed history

### Coordination Messages Feed
- Scrollable feed showing recent messages from `ai/coordination/messages.jsonl`
- Each message displays:
  - Timestamp (relative: "2 hours ago")
  - Agent name (color-coded badge)
  - Message/action description
  - Any relevant metadata (issue #, PR #, etc.)
- Auto-scroll to latest
- Filter by agent (show all / show specific agent)

### System Metrics Panel
Display if available:
- Current system phase (from `ai/coordination/status.json`)
- Active tasks count
- Pending tasks count
- Recent PR count
- System uptime

### Task Status List
Show active Copilot tasks from `ai/coordination/copilot_tasks.jsonl`:
- Issue number and title
- Current status (assigned, in_progress, completed)
- Time elapsed
- Branch name if available
- PR number if completed

## Detailed Agent View (Modal/Panel)
When clicking on an agent card:
- Full activity history (last 50 actions)
- Average response time
- Success rate (if trackable)
- Recent commits/PRs
- Link to agent's instruction file

## Controls

### Refresh Button
- Manual refresh (in addition to auto-refresh every 30s)

### Filter Controls
- Filter messages by agent
- Filter by date range (24h, 7d, 30d)
- Filter by action type (task_start, task_complete, etc.)

## Styling
- Dark theme with color-coded agents:
  - Copilot: Blue
  - Claude Code: Orange
  - ChatGPT: Green
  - Claude Web: Purple
- Clean, modern dashboard aesthetic
- Responsive design (grid collapses on mobile)

## Real-time Updates
- Refresh coordination data every 30 seconds
- Show loading spinner during refresh
- Highlight new messages since last refresh
- "Live" badge when auto-refreshing is active

## Data Sources
Fetch from GitHub repository:

```javascript
// Get coordination status
fetch('https://api.github.com/repos/yaya1738/hands-off-engine/contents/ai/coordination/status.json', {
  headers: {
    'Authorization': 'token GITHUB_PERSONAL_ACCESS_TOKEN',
    'Accept': 'application/vnd.github.v3.raw'
  }
})

// Get recent coordination messages
fetch('https://api.github.com/repos/yaya1738/hands-off-engine/contents/ai/coordination/messages.jsonl', {
  headers: {
    'Authorization': 'token GITHUB_PERSONAL_ACCESS_TOKEN',
    'Accept': 'application/vnd.github.v3.raw'
  }
})

// Get Copilot tasks
fetch('https://api.github.com/repos/yaya1738/hands-off-engine/contents/ai/coordination/copilot_tasks.jsonl', {
  headers: {
    'Authorization': 'token GITHUB_PERSONAL_ACCESS_TOKEN',
    'Accept': 'application/vnd.github.v3.raw'
  }
})
```

## Error Handling
- Show error banner if API requests fail
- Display "No recent activity" for inactive agents
- Handle missing files gracefully

## Authentication
- Require GitHub authentication
- Only show to repository collaborators

## Features for Future Enhancement
- [ ] Agent performance metrics (tasks completed, avg time)
- [ ] Alert notification when agent enters error state
- [ ] Direct messaging to agents (via GitHub issues)
- [ ] Export coordination log to CSV
