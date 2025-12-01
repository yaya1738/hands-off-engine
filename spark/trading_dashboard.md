# Trading Dashboard Spark

Build me a real-time trading dashboard with:

## Header
- Title: "Hands-Off Engine Dashboard"
- Subtitle: "Autonomous Polymarket Trading System"
- Status indicator (green dot = active, red = stopped)

## Main Content

### Current Status Card
- Current bankroll (fetch from API or hardcoded for prototype)
- Active positions count
- Today's P&L
- System mode: DRYRUN or LIVE

### Recent Trades Table
Columns:
- Timestamp
- Market name
- Side (YES/NO)
- Amount (USD)
- Price
- Status (executed, pending, failed)

Data: Fetch from `logs/` directory or recent execution history

### P&L Chart
- Line chart showing cumulative P&L over time
- X-axis: Date
- Y-axis: Profit/Loss (USD)
- Timeframe selector: 24h, 7d, 30d, All

### Alpha Signals Feed
- Scrollable list of recent alpha signals
- Each signal shows:
  - Market name
  - Model edge (%)
  - Confidence
  - Timestamp

## Controls

### Emergency Stop Button
- Big red button
- Requires confirmation modal: "Are you sure? This will stop all trading."
- On confirm: Trigger webhook to GitHub Actions
  ```javascript
  fetch('https://api.github.com/repos/yaya1738/hands-off-engine/dispatches', {
    method: 'POST',
    headers: {
      'Authorization': 'token YOUR_TOKEN',
      'Accept': 'application/vnd.github.v3+json'
    },
    body: JSON.stringify({
      event_type: 'spark_emergency_stop',
      client_payload: { user: 'USER', reason: 'Manual stop from dashboard' }
    })
  })
  ```

### Refresh Button
- Manual refresh data (in addition to auto-refresh)

## Styling
- Dark theme (dark navy background, bright text)
- Professional look, clean lines
- Mobile-responsive (stack cards vertically on small screens)
- Use GitHub's color palette for consistency

## Auto-Refresh
- Refresh data every 30 seconds
- Show "Last updated: X seconds ago" timestamp
- Loading spinner during refresh

## Authentication
- Use GitHub authentication (user must be logged in)
- Only show data to authorized users

## Data Sources
For prototype, can use:
- Mock data that looks realistic
- Fetch from GitHub repo files:
  - `state/polymarket-model.json` for positions
  - `ai/coordination/messages.jsonl` for recent activity
  - Parse execution logs from `logs/` directory

## Technical Notes
- Use modern JavaScript (ES6+)
- Keep it simple, single page app
- Minimize dependencies
- Gracefully handle API errors (show error banner)
