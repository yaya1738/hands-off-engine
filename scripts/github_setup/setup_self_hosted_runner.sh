#!/bin/bash
# Setup self-hosted GitHub Actions runner on Ubuntu server
#
# This script:
# 1. Downloads GitHub Actions runner
# 2. Configures with repository token
# 3. Installs as systemd service
# 4. Registers with GitHub
# 5. Adds labels: self-hosted, linux, droplet

set -e

# Configuration
RUNNER_VERSION="2.311.0"
RUNNER_USER="runner"
RUNNER_HOME="/opt/actions-runner"

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    log_error "Please run as root (use sudo)"
    exit 1
fi

# Get runner token from environment or argument
RUNNER_TOKEN="${RUNNER_TOKEN:-$1}"
if [ -z "$RUNNER_TOKEN" ]; then
    log_error "RUNNER_TOKEN not set. Pass as argument or set environment variable."
    exit 1
fi

# Get repository from environment or argument
REPO="${REPO:-$2}"
if [ -z "$REPO" ]; then
    log_error "REPO not set (format: owner/repo). Pass as argument or set environment variable."
    exit 1
fi

log_info "Setting up GitHub Actions runner for repository: $REPO"

# Create runner user if doesn't exist
if ! id -u "$RUNNER_USER" >/dev/null 2>&1; then
    log_info "Creating runner user: $RUNNER_USER"
    useradd -m -s /bin/bash "$RUNNER_USER"
fi

# Create runner directory
log_info "Creating runner directory: $RUNNER_HOME"
mkdir -p "$RUNNER_HOME"
cd "$RUNNER_HOME"

# Download runner if not already present
if [ ! -f "$RUNNER_HOME/bin/Runner.Listener" ]; then
    log_info "Downloading GitHub Actions runner v$RUNNER_VERSION"
    
    # Determine architecture
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        RUNNER_ARCH="x64"
    elif [ "$ARCH" = "aarch64" ]; then
        RUNNER_ARCH="arm64"
    else
        log_error "Unsupported architecture: $ARCH"
        exit 1
    fi
    
    RUNNER_PKG="actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"
    RUNNER_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_PKG}"
    
    curl -o "$RUNNER_PKG" -L "$RUNNER_URL"
    
    # Extract runner
    log_info "Extracting runner package"
    tar xzf "$RUNNER_PKG"
    rm "$RUNNER_PKG"
else
    log_info "Runner already downloaded, skipping download"
fi

# Set ownership
chown -R "$RUNNER_USER:$RUNNER_USER" "$RUNNER_HOME"

# Configure runner as runner user
log_info "Configuring runner"

# Remove existing config if present (for re-runs)
if [ -f "$RUNNER_HOME/.runner" ]; then
    log_warn "Removing existing runner configuration"
    su - "$RUNNER_USER" -c "cd $RUNNER_HOME && ./config.sh remove --token $RUNNER_TOKEN" || true
fi

# Configure runner
su - "$RUNNER_USER" -c "cd $RUNNER_HOME && ./config.sh \
    --url https://github.com/$REPO \
    --token $RUNNER_TOKEN \
    --name 'droplet-$(hostname)' \
    --labels self-hosted,linux,droplet \
    --work _work \
    --replace \
    --unattended"

# Install systemd service
log_info "Installing systemd service"
cd "$RUNNER_HOME"
./svc.sh install "$RUNNER_USER"

# Start service
log_info "Starting runner service"
./svc.sh start

# Check status
log_info "Checking runner status"
./svc.sh status

log_info "✅ Self-hosted runner setup complete!"
log_info "Runner should now appear in GitHub repository settings under Actions > Runners"
log_info ""
log_info "To manage the runner:"
log_info "  Check status:  sudo $RUNNER_HOME/svc.sh status"
log_info "  Stop:          sudo $RUNNER_HOME/svc.sh stop"
log_info "  Start:         sudo $RUNNER_HOME/svc.sh start"
log_info "  Uninstall:     sudo $RUNNER_HOME/svc.sh uninstall"
