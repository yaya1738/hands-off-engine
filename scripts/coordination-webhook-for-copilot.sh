#!/bin/bash
# Webhook endpoint for Copilot to send messages
# Copilot can call this script to send real-time messages to Claude

WEBHOOK_URL="http://localhost:8888/coordination/message"

# Check if message provided
if [ -z "$1" ]; then
    echo "Usage: $0 <message>"
    echo "Example: $0 'I agree with your proposal'"
    exit 1
fi

MESSAGE="$1"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Create JSON payload
PAYLOAD=$(cat <<EOF
{
  "timestamp": "$TIMESTAMP",
  "from": "copilot",
  "to": "claude-code",
  "type": "response",
  "message": "$MESSAGE",
  "context": {
    "method": "webhook",
    "realtime": true
  }
}
EOF
)

# Send to webhook
curl -X POST \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  "$WEBHOOK_URL"

echo ""
echo "✅ Message sent to Claude Code in real-time"
