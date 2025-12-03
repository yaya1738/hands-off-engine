#!/bin/bash
# Dual-Claude Coordination Helper Script
# Helps Claude instances stay in sync

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SYNC_DIR="$ROOT_DIR/state/claude_sync"

cd "$ROOT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    cat << EOF
Usage: $0 <command> [args...]

Commands:
    status              Show coordination status (sessions, tasks, messages)
    heartbeat <who>     Update heartbeat for instance (web|cli)
    sync <who>          Full sync: heartbeat + check messages + show tasks
    messages <who>      Show messages for instance
    tasks               Show task queue
    claim <who> <task>  Claim a task
    done <who> <task>   Mark task as done
    post <from> <to> <type> <msg>  Post a message

Examples:
    $0 status                          # Check system status
    $0 sync web                        # Web Claude checking in
    $0 claim cli coord-001             # CLI Claude claiming task
    $0 post web cli info "Starting work"  # Send message
EOF
    exit 1
}

[[ $# -eq 0 ]] && usage

CMD="$1"
shift

case "$CMD" in
    status)
        echo -e "${BLUE}=== Dual-Claude Coordination Status ===${NC}\n"

        echo -e "${GREEN}Active Sessions:${NC}"
        python3 "$SYNC_DIR/utils.py" sessions
        echo

        echo -e "${GREEN}Pending Tasks:${NC}"
        if command -v jq &> /dev/null; then
            cat "$SYNC_DIR/task_queue.json" | jq -r '.tasks[] | select(.status == "pending") | "  • [\(.task_id)] \(.description)"' || echo "  No pending tasks"
        else
            python3 -c "import json; data=json.load(open('$SYNC_DIR/task_queue.json')); print('\n'.join(f'  • [{t[\"task_id\"]}] {t[\"description\"]}' for t in data['tasks'] if t['status'] == 'pending') or '  No pending tasks')"
        fi
        echo

        echo -e "${GREEN}Recent Messages (last 5):${NC}"
        tail -5 "$SYNC_DIR/messages.jsonl" 2>/dev/null | while read -r line; do
            if command -v jq &> /dev/null; then
                echo "$line" | jq -r '"  [\(.from) → \(.to)] \(.content)"'
            else
                echo "  $line"
            fi
        done || echo "  No messages yet"
        echo
        ;;

    heartbeat)
        [[ $# -lt 1 ]] && { echo "Usage: $0 heartbeat <who>"; exit 1; }
        WHO="$1"
        python3 "$SYNC_DIR/utils.py" heartbeat "$WHO"
        ;;

    sync)
        [[ $# -lt 1 ]] && { echo "Usage: $0 sync <who>"; exit 1; }
        WHO="$1"

        echo -e "${BLUE}Syncing $WHO Claude...${NC}\n"

        # Update heartbeat
        python3 "$SYNC_DIR/utils.py" heartbeat "$WHO"

        # Check messages
        echo -e "\n${GREEN}Your Messages:${NC}"
        python3 "$SYNC_DIR/utils.py" read "$WHO" | tail -20

        # Show available tasks
        echo -e "\n${GREEN}Available Tasks:${NC}"
        if command -v jq &> /dev/null; then
            cat "$SYNC_DIR/task_queue.json" | jq -r '.tasks[] | select(.status == "pending") | "  • [\(.task_id)] \(.description)"' || echo "  No pending tasks"
        else
            python3 -c "import json; data=json.load(open('$SYNC_DIR/task_queue.json')); print('\n'.join(f'  • [{t[\"task_id\"]}] {t[\"description\"]}' for t in data['tasks'] if t['status'] == 'pending') or '  No pending tasks')"
        fi

        # Show other active sessions
        echo -e "\n${GREEN}Other Active Instances:${NC}"
        python3 "$SYNC_DIR/utils.py" sessions | grep -v "$WHO" || echo "  No other instances active"
        ;;

    messages)
        [[ $# -lt 1 ]] && { echo "Usage: $0 messages <who>"; exit 1; }
        WHO="$1"
        python3 "$SYNC_DIR/utils.py" read "$WHO"
        ;;

    tasks)
        echo -e "${GREEN}Task Queue:${NC}\n"
        if command -v jq &> /dev/null; then
            cat "$SYNC_DIR/task_queue.json" | jq -r '.tasks[] | "\(.status | ascii_upcase | .[0:4]) [\(.task_id)] \(.description)\n      Assigned: \(.assigned_to) | Claimed: \(.claimed_by // "none")"'
        else
            python3 -c "
import json
data = json.load(open('$SYNC_DIR/task_queue.json'))
for t in data['tasks']:
    print(f\"{t['status'].upper()[:4]} [{t['task_id']}] {t['description']}\")
    print(f\"      Assigned: {t['assigned_to']} | Claimed: {t['claimed_by'] or 'none'}\")
"
        fi
        ;;

    claim)
        [[ $# -lt 2 ]] && { echo "Usage: $0 claim <who> <task_id>"; exit 1; }
        WHO="$1"
        TASK="$2"
        python3 "$SYNC_DIR/utils.py" claim "$WHO" "$TASK"
        ;;

    done)
        [[ $# -lt 2 ]] && { echo "Usage: $0 done <who> <task_id>"; exit 1; }
        WHO="$1"
        TASK="$2"
        python3 "$SYNC_DIR/utils.py" complete "$WHO" "$TASK"
        ;;

    post)
        [[ $# -lt 4 ]] && { echo "Usage: $0 post <from> <to> <type> <message>"; exit 1; }
        python3 "$SYNC_DIR/utils.py" post "$@"
        ;;

    *)
        echo "Unknown command: $CMD"
        usage
        ;;
esac
