#!/bin/bash
# Deploy Trading Components to Runtime Droplets
# ==============================================
#
# Pushes all trading code from dev (MCP) to runtime droplets
# including the new distributed trading integration.
#
# Serving: Yair Siegel

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Deploy Trading to Runtime Droplets${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Get list of droplets
get_droplets() {
    doctl compute droplet list --format ID,Name,PublicIPv4,Tags --no-header 2>/dev/null | \
    grep -E "hands-off-engine|pm-helper"
}

# Get trading-related files to deploy
get_trading_files() {
    cat << 'EOF'
autonomous/trade_executor.py
autonomous/polymarket_live.py
autonomous/concrete_executor.py
autonomous/hft_execution_bridge.py
autonomous/machine_communication_hub.py
autonomous/machine_api_gateway.py
autonomous/machine_distributed_coordinator.py
autonomous/machine_stream_processor.py
autonomous/machine_message_queue.py
autonomous/machine_security.py
executor/polymarket_orders.py
executor/math/abcfc_unified.py
executor/math/abcfc_nexus.py
executor/math/abcfc_layers.py
executor/math/abcfc_system.py
executor/math/abcfc_pure.py
executor/math/abcfc_live.py
integrafix/trading_pipeline.py
integrafix/distributed_trading_integration.py
integrafix/distributed_trading_wrapper.py
integrafix/credential_loader.py
integrafix/polymarket_fundamentals.py
integrafix/fair_price_estimator.py
integrafix/yair_golden_bridge.py
integrafix/money_printer.py
integrafix/money_printer_core.py
integrafix/income_engine.py
integrafix/capital_bridge.py
integrafix/abcfc_hft_frequency.py
config/trading_config.json
config/money_printer_specs.json
scripts/setup_distributed_trading.sh
EOF
}

# Deploy to single droplet
deploy_to_droplet() {
    local droplet_ip=$1
    local droplet_name=$2
    local droplet_id=$3

    print_info "Deploying to $droplet_name ($droplet_ip)..."

    # Check if droplet is accessible
    if ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no root@$droplet_ip "echo 'OK'" &>/dev/null; then
        print_warning "Cannot connect to $droplet_name - skipping"
        return 1
    fi

    # Ensure hands-off-engine directory exists
    ssh root@$droplet_ip "mkdir -p /root/hands-off-engine" 2>/dev/null || true

    # Create necessary directories
    print_info "  Creating directories..."
    ssh root@$droplet_ip "cd /root/hands-off-engine && mkdir -p autonomous executor executor/math integrafix config scripts logs state" 2>/dev/null || true

    # Deploy each file
    local success_count=0
    local fail_count=0

    while IFS= read -r file; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            # Create parent directory on remote
            local parent_dir=$(dirname "$file")
            ssh root@$droplet_ip "mkdir -p /root/hands-off-engine/$parent_dir" 2>/dev/null || true

            # Copy file
            if scp -o StrictHostKeyChecking=no "$PROJECT_ROOT/$file" "root@$droplet_ip:/root/hands-off-engine/$file" &>/dev/null; then
                ((success_count++))
            else
                ((fail_count++))
                print_warning "  Failed to copy $file"
            fi
        fi
    done < <(get_trading_files)

    print_info "  Deployed: $success_count files, Failed: $fail_count files"

    # Install dependencies
    print_info "  Installing dependencies..."
    ssh root@$droplet_ip "cd /root/hands-off-engine && pip install -q requests py-clob-client web3 2>/dev/null || true" &

    # Copy credentials if available
    if [ -f "$PROJECT_ROOT/.env" ]; then
        scp -o StrictHostKeyChecking=no "$PROJECT_ROOT/.env" "root@$droplet_ip:/root/hands-off-engine/.env" &>/dev/null || true
    fi

    # Set executable permissions
    ssh root@$droplet_ip "cd /root/hands-off-engine && chmod +x scripts/*.sh 2>/dev/null || true"

    print_success "Deployed to $droplet_name"
    return 0
}

# Register droplet as trading service
register_trading_service() {
    local droplet_ip=$1
    local droplet_name=$2

    print_info "Registering $droplet_name as trading service..."

    ssh root@$droplet_ip "cd /root/hands-off-engine && python3 integrafix/distributed_trading_integration.py --register --port 8080 2>/dev/null &" || true

    print_success "Registered $droplet_name"
}

# Verify deployment
verify_deployment() {
    local droplet_ip=$1
    local droplet_name=$2

    print_info "Verifying deployment on $droplet_name..."

    # Check if key files exist
    local key_files=(
        "autonomous/trade_executor.py"
        "integrafix/distributed_trading_integration.py"
        "integrafix/trading_pipeline.py"
    )

    local all_exist=true
    for file in "${key_files[@]}"; do
        if ! ssh root@$droplet_ip "test -f /root/hands-off-engine/$file" 2>/dev/null; then
            print_warning "  Missing: $file"
            all_exist=false
        fi
    done

    if [ "$all_exist" = true ]; then
        print_success "Verification passed for $droplet_name"
        return 0
    else
        print_error "Verification failed for $droplet_name"
        return 1
    fi
}

# Main deployment
main() {
    print_header

    # Get droplets
    print_info "Fetching droplet list..."
    droplets=$(get_droplets)

    if [ -z "$droplets" ]; then
        print_error "No droplets found"
        exit 1
    fi

    droplet_count=$(echo "$droplets" | wc -l)
    print_success "Found $droplet_count droplets"
    echo ""

    # Deploy to each droplet
    deployed_count=0
    failed_count=0

    while IFS= read -r droplet; do
        droplet_id=$(echo "$droplet" | awk '{print $1}')
        droplet_name=$(echo "$droplet" | awk '{print $2}')
        droplet_ip=$(echo "$droplet" | awk '{print $3}')

        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Droplet: $droplet_name"
        echo "IP: $droplet_ip"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        if deploy_to_droplet "$droplet_ip" "$droplet_name" "$droplet_id"; then
            ((deployed_count++))

            # Verify deployment
            if verify_deployment "$droplet_ip" "$droplet_name"; then
                # Register as trading service
                register_trading_service "$droplet_ip" "$droplet_name" &
            fi
        else
            ((failed_count++))
        fi

    done <<< "$droplets"

    # Wait for background registration tasks
    wait

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "DEPLOYMENT COMPLETE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    print_success "Successfully deployed to $deployed_count droplets"
    if [ $failed_count -gt 0 ]; then
        print_warning "Failed to deploy to $failed_count droplets"
    fi
    echo ""

    print_info "Next steps:"
    echo "  1. Verify services: python3 integrafix/distributed_trading_integration.py --discover"
    echo "  2. Check stats: python3 integrafix/distributed_trading_integration.py --stats"
    echo "  3. Test execution: python3 integrafix/distributed_trading_integration.py --test"
    echo ""
}

# Parse arguments
SPECIFIC_DROPLET=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --droplet)
            SPECIFIC_DROPLET="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            cat << EOF
Deploy Trading to Runtime Droplets

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --droplet NAME    Deploy to specific droplet only
    --dry-run         Show what would be deployed without deploying
    --help           Show this help message

EXAMPLES:
    # Deploy to all droplets
    $0

    # Deploy to specific droplet
    $0 --droplet ho-compute-1

    # Dry run (show what would be deployed)
    $0 --dry-run

DROPLETS:
$(get_droplets | awk '{printf "    %s (%s)\n", $2, $3}')

Serving: Yair Siegel
EOF
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ "$DRY_RUN" = true ]; then
    print_info "DRY RUN - Files that would be deployed:"
    get_trading_files
    exit 0
fi

if [ -n "$SPECIFIC_DROPLET" ]; then
    # Deploy to specific droplet
    droplet=$(get_droplets | grep "$SPECIFIC_DROPLET")
    if [ -z "$droplet" ]; then
        print_error "Droplet not found: $SPECIFIC_DROPLET"
        exit 1
    fi

    droplet_id=$(echo "$droplet" | awk '{print $1}')
    droplet_name=$(echo "$droplet" | awk '{print $2}')
    droplet_ip=$(echo "$droplet" | awk '{print $3}')

    deploy_to_droplet "$droplet_ip" "$droplet_name" "$droplet_id"
    verify_deployment "$droplet_ip" "$droplet_name"
    register_trading_service "$droplet_ip" "$droplet_name"
else
    # Deploy to all droplets
    main
fi
