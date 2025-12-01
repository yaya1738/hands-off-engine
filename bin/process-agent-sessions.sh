#!/usr/bin/env bash
# Process Agent Session Outputs - Convenience Wrapper
#
# Makes it easy to review and apply updates from tri-agent sessions.
#
# Usage:
#   bin/process-agent-sessions.sh list                 # List recent sessions
#   bin/process-agent-sessions.sh review <session-id>  # Review session outputs
#   bin/process-agent-sessions.sh apply <session-id>   # Apply updates from session
#   bin/process-agent-sessions.sh batch <N>            # Process N most recent sessions

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

APPLIER="python -m ai_nexus.kernel_update_applier"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${BLUE}ℹ${NC} $*"
}

success() {
    echo -e "${GREEN}✓${NC} $*"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $*"
}

error() {
    echo -e "${RED}✗${NC} $*"
}

usage() {
    cat <<EOF
Process Agent Session Outputs

Usage:
  $(basename "$0") list [--recent N]           List recent sessions
  $(basename "$0") review <session-id>         Review session and extracted updates
  $(basename "$0") apply <session-id> [opts]   Apply updates from session
  $(basename "$0") batch [--recent N]          Process multiple recent sessions
  $(basename "$0") help                        Show this help

Options for 'apply':
  --dry-run           Validate without applying (default: true)
  --for-real          Actually apply updates (disables dry-run)
  --min-confidence    high|medium|low (default: medium)

Examples:
  # List 5 most recent sessions
  $(basename "$0") list --recent 5

  # Review a specific session
  $(basename "$0") review autokernel_risk_model_v2_20251127_201339

  # Apply updates (dry run)
  $(basename "$0") apply autokernel_risk_model_v2_20251127_201339

  # Actually apply updates
  $(basename "$0") apply autokernel_risk_model_v2_20251127_201339 --for-real

  # Review and apply recent sessions interactively
  $(basename "$0") batch --recent 3

See docs/TRI_AGENT_SESSION_OUTPUT_HANDLING.md for detailed guide.
EOF
}

# Command: list
cmd_list() {
    local recent=10

    while [[ $# -gt 0 ]]; do
        case $1 in
            --recent)
                recent="$2"
                shift 2
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    info "Listing $recent most recent sessions..."
    $APPLIER list-sessions --recent "$recent"
}

# Command: review
cmd_review() {
    if [[ $# -lt 1 ]]; then
        error "Session ID required"
        usage
        exit 1
    fi

    local session_id="$1"
    local thread_file="ai/intercom/$session_id/thread.jsonl"
    local cpu_file="ai/intercom/$session_id/cpu_instance.json"

    if [[ ! -f "$thread_file" ]]; then
        error "Session not found: $session_id"
        exit 1
    fi

    info "Reviewing session: $session_id"
    echo ""

    # Show CPU instance info
    if [[ -f "$cpu_file" ]]; then
        echo "=== CPU Instance Info ==="
        jq -r '. | "CPU ID: \(.cpu_id)\nStatus: \(.status)\nBound Kernels: \(.bound_kernels | join(", "))\nSteps: \(.steps_completed // "N/A")"' "$cpu_file"
        echo ""
    fi

    # Show thread summary
    echo "=== Thread Summary ==="
    local msg_count=$(wc -l < "$thread_file")
    echo "Messages: $msg_count"

    # Show agents and their message counts
    echo "Participants:"
    jq -r '.from' "$thread_file" | sort | uniq -c | sed 's/^/  /'
    echo ""

    # Extract and show updates
    echo "=== Extracted Updates ==="
    $APPLIER extract --session-id "$session_id"
    echo ""

    # Offer to view full thread
    read -p "View full thread? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        jq -r '.content' "$thread_file" | less
    fi
}

# Command: apply
cmd_apply() {
    if [[ $# -lt 1 ]]; then
        error "Session ID required"
        usage
        exit 1
    fi

    local session_id="$1"
    shift

    local dry_run=true
    local min_confidence="medium"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run=true
                shift
                ;;
            --for-real)
                dry_run=false
                shift
                ;;
            --min-confidence)
                min_confidence="$2"
                shift 2
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    if [[ ! -f "ai/intercom/$session_id/thread.jsonl" ]]; then
        error "Session not found: $session_id"
        exit 1
    fi

    local mode_str="[DRY RUN]"
    if [[ "$dry_run" == false ]]; then
        mode_str="${RED}[LIVE MODE]${NC}"
        warning "This will actually apply updates to kernels!"
        read -p "Are you sure? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "Cancelled"
            exit 0
        fi
    fi

    info "Applying updates from session: $session_id $mode_str"

    local cmd="$APPLIER auto --session-id $session_id --min-confidence $min_confidence"
    if [[ "$dry_run" == true ]]; then
        cmd="$cmd --dry-run"
    fi

    $cmd

    if [[ "$dry_run" == false ]]; then
        success "Updates applied!"
        info "Check audit log: state/kernel_update_log.jsonl"
    else
        info "To apply for real, use: $(basename "$0") apply $session_id --for-real"
    fi
}

# Command: batch
cmd_batch() {
    local recent=5

    while [[ $# -gt 0 ]]; do
        case $1 in
            --recent)
                recent="$2"
                shift 2
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    info "Processing $recent most recent sessions..."
    echo ""

    # Get session list
    local sessions
    sessions=$(ls -t ai/intercom/ | head -"$recent")

    for session in $sessions; do
        echo "=================================================="
        info "Session: $session"
        echo ""

        # Show what would be extracted
        $APPLIER extract --session-id "$session" 2>/dev/null || {
            warning "No updates found or error processing session"
            echo ""
            continue
        }

        echo ""
        read -p "Review this session in detail? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cmd_review "$session"
        fi

        read -p "Apply updates from this session (dry-run)? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cmd_apply "$session" --dry-run
        fi

        echo ""
    done

    success "Batch processing complete!"
}

# Main command dispatcher
main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    local command="$1"
    shift

    case "$command" in
        list)
            cmd_list "$@"
            ;;
        review)
            cmd_review "$@"
            ;;
        apply)
            cmd_apply "$@"
            ;;
        batch)
            cmd_batch "$@"
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

main "$@"
