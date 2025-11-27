#!/bin/bash
# deploy_services.sh - Deploy or update all Hands-Off Engine systemd services
#
# Usage:
#   ./deploy_services.sh install    # Install and enable all services
#   ./deploy_services.sh start      # Start all services
#   ./deploy_services.sh stop       # Stop all services
#   ./deploy_services.sh status     # Show status of all services
#   ./deploy_services.sh restart    # Restart all services
#   ./deploy_services.sh update     # Pull latest code and restart services
#   ./deploy_services.sh uninstall  # Stop and disable all services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SYSTEMD_DIR="$SCRIPT_DIR/systemd"

# Services to manage
SERVICES=(
    "server-sync-agent"
    "self-healing-agent"
    "coordination-agent"
    "telegram-bot"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

install_services() {
    log_info "Installing services..."
    
    for service in "${SERVICES[@]}"; do
        local service_file="$SYSTEMD_DIR/$service.service"
        if [ -f "$service_file" ]; then
            log_info "Installing $service..."
            cp "$service_file" /etc/systemd/system/
            systemctl daemon-reload
            systemctl enable "$service"
            log_info "✓ $service installed and enabled"
        else
            log_warn "Service file not found: $service_file"
        fi
    done
    
    # Create log files
    for service in "${SERVICES[@]}"; do
        local log_file="/var/log/${service}.log"
        touch "$log_file"
        chmod 644 "$log_file"
    done
    
    log_info "All services installed. Use './deploy_services.sh start' to start them."
}

start_services() {
    log_info "Starting services..."
    
    for service in "${SERVICES[@]}"; do
        if systemctl is-enabled "$service" &>/dev/null; then
            log_info "Starting $service..."
            systemctl start "$service" || log_warn "Failed to start $service"
        else
            log_warn "$service is not installed"
        fi
    done
    
    log_info "Services started. Use './deploy_services.sh status' to check."
}

stop_services() {
    log_info "Stopping services..."
    
    for service in "${SERVICES[@]}"; do
        if systemctl is-active "$service" &>/dev/null; then
            log_info "Stopping $service..."
            systemctl stop "$service" || log_warn "Failed to stop $service"
        fi
    done
    
    log_info "Services stopped."
}

restart_services() {
    log_info "Restarting services..."
    
    for service in "${SERVICES[@]}"; do
        if systemctl is-enabled "$service" &>/dev/null; then
            log_info "Restarting $service..."
            systemctl restart "$service" || log_warn "Failed to restart $service"
        fi
    done
    
    log_info "Services restarted."
}

status_services() {
    echo ""
    echo "=== Hands-Off Engine Services Status ==="
    echo ""
    
    for service in "${SERVICES[@]}"; do
        local status
        if systemctl is-active "$service" &>/dev/null; then
            status="${GREEN}RUNNING${NC}"
        elif systemctl is-enabled "$service" &>/dev/null; then
            status="${YELLOW}STOPPED${NC}"
        else
            status="${RED}NOT INSTALLED${NC}"
        fi
        echo -e "  $service: $status"
    done
    
    echo ""
    echo "=== Last 5 log lines per service ==="
    echo ""
    
    for service in "${SERVICES[@]}"; do
        local log_file="/var/log/${service}.log"
        if [ -f "$log_file" ] && [ -s "$log_file" ]; then
            echo "--- $service ---"
            tail -5 "$log_file"
            echo ""
        fi
    done
}

update_from_repo() {
    log_info "Updating from repository..."
    
    cd "$REPO_ROOT"
    
    # Pull latest changes
    if git pull origin main; then
        log_info "✓ Repository updated"
    else
        log_error "Failed to pull from repository"
        exit 1
    fi
    
    # Reinstall services in case they changed
    log_info "Reinstalling service files..."
    for service in "${SERVICES[@]}"; do
        local service_file="$SYSTEMD_DIR/$service.service"
        if [ -f "$service_file" ]; then
            cp "$service_file" /etc/systemd/system/
        fi
    done
    systemctl daemon-reload
    
    # Restart services
    restart_services
    
    log_info "✓ Update complete"
}

uninstall_services() {
    log_info "Uninstalling services..."
    
    for service in "${SERVICES[@]}"; do
        if systemctl is-active "$service" &>/dev/null; then
            log_info "Stopping $service..."
            systemctl stop "$service"
        fi
        
        if systemctl is-enabled "$service" &>/dev/null; then
            log_info "Disabling $service..."
            systemctl disable "$service"
        fi
        
        if [ -f "/etc/systemd/system/$service.service" ]; then
            log_info "Removing $service..."
            rm "/etc/systemd/system/$service.service"
        fi
    done
    
    systemctl daemon-reload
    
    log_info "All services uninstalled."
}

show_usage() {
    echo "Usage: $0 {install|start|stop|status|restart|update|uninstall}"
    echo ""
    echo "Commands:"
    echo "  install   - Install and enable all systemd services"
    echo "  start     - Start all services"
    echo "  stop      - Stop all services"
    echo "  status    - Show status of all services"
    echo "  restart   - Restart all services"
    echo "  update    - Pull latest code and restart services"
    echo "  uninstall - Stop, disable and remove all services"
}

# Main
case "$1" in
    install)
        check_root
        install_services
        ;;
    start)
        check_root
        start_services
        ;;
    stop)
        check_root
        stop_services
        ;;
    status)
        status_services
        ;;
    restart)
        check_root
        restart_services
        ;;
    update)
        check_root
        update_from_repo
        ;;
    uninstall)
        check_root
        uninstall_services
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
