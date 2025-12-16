#!/bin/bash
# INTEGRAFIX: Setup Distributed Trading
# =====================================
#
# Automates setup of distributed trading infrastructure
# across multiple machines.
#
# USAGE:
#   # On local machine:
#   ./scripts/setup_distributed_trading.sh --local
#
#   # On remote machines:
#   ./scripts/setup_distributed_trading.sh --remote --port 8080
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
NC='\033[0m' # No Color

# Defaults
MODE="local"
PORT=8080
ENABLE_SECURITY=true
AUTO_DISCOVER=true

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  INTEGRAFIX Distributed Trading Setup${NC}"
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

check_dependencies() {
    print_info "Checking dependencies..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install Python 3.8+"
        exit 1
    fi
    print_success "Python 3 found: $(python3 --version)"

    # Check required Python packages
    python3 -c "import requests" 2>/dev/null || {
        print_warning "requests package not found. Installing..."
        pip install requests
    }

    # Check Redis (optional but recommended)
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            print_success "Redis is running"
        else
            print_warning "Redis is installed but not running"
            print_info "Start Redis with: sudo systemctl start redis"
        fi
    else
        print_warning "Redis not installed (optional but recommended)"
        print_info "Install with: sudo apt install redis-server"
    fi

    # Check M2M components
    if [ -f "autonomous/machine_distributed_coordinator.py" ]; then
        print_success "M2M distributed coordinator found"
    else
        print_error "M2M distributed coordinator not found"
        print_info "Run M2M setup first"
        exit 1
    fi

    if [ -f "autonomous/machine_stream_processor.py" ]; then
        print_success "M2M stream processor found"
    else
        print_error "M2M stream processor not found"
        exit 1
    fi

    if [ -f "integrafix/distributed_trading_integration.py" ]; then
        print_success "Distributed trading integration found"
    else
        print_error "Distributed trading integration not found"
        exit 1
    fi
}

get_local_ip() {
    # Try multiple methods to get local IP
    local ip

    # Method 1: ip command
    if command -v ip &> /dev/null; then
        ip=$(ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \K[0-9.]+')
    fi

    # Method 2: hostname command
    if [ -z "$ip" ] && command -v hostname &> /dev/null; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi

    # Method 3: ifconfig
    if [ -z "$ip" ] && command -v ifconfig &> /dev/null; then
        ip=$(ifconfig 2>/dev/null | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1)
    fi

    # Fallback
    if [ -z "$ip" ]; then
        ip="127.0.0.1"
    fi

    echo "$ip"
}

register_service() {
    local port=$1

    print_info "Registering trading service on port $port..."

    python3 integrafix/distributed_trading_integration.py \
        --register \
        --port "$port" || {
        print_error "Failed to register service"
        return 1
    }

    print_success "Service registered on port $port"
}

discover_services() {
    print_info "Discovering available trading services..."

    python3 integrafix/distributed_trading_integration.py \
        --discover || {
        print_warning "Service discovery failed"
        return 1
    }
}

test_integration() {
    print_info "Testing distributed trading integration..."

    python3 integrafix/distributed_trading_integration.py \
        --test || {
        print_error "Integration test failed"
        return 1
    }

    print_success "Integration test passed"
}

setup_local() {
    print_header
    print_info "Setting up LOCAL trading node..."
    echo ""

    check_dependencies
    echo ""

    local_ip=$(get_local_ip)
    print_info "Local IP: $local_ip"
    echo ""

    # Register local service
    register_service "$PORT"
    echo ""

    # Auto-discover services
    if [ "$AUTO_DISCOVER" = true ]; then
        discover_services
        echo ""
    fi

    # Test integration
    print_info "Running integration tests..."
    test_integration
    echo ""

    print_success "Local trading node setup complete!"
    echo ""
    print_info "Next steps:"
    echo "  1. Setup remote nodes: ./scripts/setup_distributed_trading.sh --remote"
    echo "  2. Check service status: python3 integrafix/distributed_trading_wrapper.py --services"
    echo "  3. View stats: python3 integrafix/distributed_trading_integration.py --stats"
    echo ""
}

setup_remote() {
    print_header
    print_info "Setting up REMOTE trading node..."
    echo ""

    check_dependencies
    echo ""

    local_ip=$(get_local_ip)
    print_info "Local IP: $local_ip"
    echo ""

    # Register remote service
    register_service "$PORT"
    echo ""

    # Auto-discover services
    if [ "$AUTO_DISCOVER" = true ]; then
        discover_services
        echo ""
    fi

    print_success "Remote trading node setup complete!"
    echo ""
    print_info "This node is now discoverable by other trading nodes"
    print_info "Service ID will be visible in discovery from other nodes"
    echo ""
}

show_status() {
    print_header

    # Show service status
    print_info "Service Status:"
    python3 integrafix/distributed_trading_wrapper.py --services || true
    echo ""

    # Show execution stats
    print_info "Execution Statistics:"
    python3 integrafix/distributed_trading_integration.py --stats || true
    echo ""
}

show_help() {
    cat << EOF
INTEGRAFIX: Setup Distributed Trading

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --local             Setup local trading node (default)
    --remote            Setup remote trading node
    --port PORT         Service port (default: 8080)
    --no-discover       Skip automatic service discovery
    --status            Show current status
    --test              Run integration test
    --help              Show this help message

EXAMPLES:
    # Setup local node
    $0 --local

    # Setup remote node on custom port
    $0 --remote --port 8090

    # Check status
    $0 --status

    # Test integration
    $0 --test

NETWORK SETUP:
    For machines on same network:
    - Services will auto-discover each other
    - No additional configuration needed

    For machines on different networks:
    - Use VPN (recommended: Tailscale)
    - Or configure firewall to allow port $PORT

DOCUMENTATION:
    See docs/DISTRIBUTED_TRADING.md for full documentation

Serving: Yair Siegel
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --local)
            MODE="local"
            shift
            ;;
        --remote)
            MODE="remote"
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --no-discover)
            AUTO_DISCOVER=false
            shift
            ;;
        --status)
            show_status
            exit 0
            ;;
        --test)
            test_integration
            exit 0
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run setup based on mode
case $MODE in
    local)
        setup_local
        ;;
    remote)
        setup_remote
        ;;
    *)
        print_error "Invalid mode: $MODE"
        show_help
        exit 1
        ;;
esac
