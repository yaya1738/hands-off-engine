#!/bin/bash
# Setup self-hosted GitHub Actions runner on Ubuntu server
#
# This script:
# 1. Downloads a pinned GitHub Actions runner release and verifies its SHA-256 digest
# 2. Configures with repository token
# 3. Installs as systemd service
# 4. Registers with GitHub
# 5. Adds labels: self-hosted, linux, droplet

set -e

# Configuration
RUNNER_VERSION="2.337.0"
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

# Get runner token from environment only so it is not accepted as a command-line argument.
RUNNER_TOKEN="${RUNNER_TOKEN:-}"
if [ -z "$RUNNER_TOKEN" ]; then
    log_error "RUNNER_TOKEN environment variable is required."
    exit 1
fi

# Get repository from environment only.
REPO="${REPO:-}"
if [ -z "$REPO" ]; then
    log_error "REPO environment variable is required (format: owner/repo)."
    exit 1
fi
if ! printf '%s' "$REPO" | grep -Eq '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$'; then
    log_error "REPO must use owner/repo format."
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

    # Determine architecture and use the GitHub-published SHA-256 digest for this exact release artifact.
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64)
            RUNNER_ARCH="x64"
            RUNNER_SHA256="70920811a4f8ad4328818682bca5c6469c1c942fab52448868071d0063816613"
            ;;
        aarch64)
            RUNNER_ARCH="arm64"
            RUNNER_SHA256="9b1dc70626422526e3c94767cf024896beb15da5342a3f4819bf2feac13e0393"
            ;;
        *)
            log_error "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac

    RUNNER_PKG="actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"
    RUNNER_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_PKG}"

    curl --fail --silent --show-error --location --output "$RUNNER_PKG" "$RUNNER_URL"
    printf '%s  %s\n' "$RUNNER_SHA256" "$RUNNER_PKG" | sha256sum --check --status -

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
log_info "  Start:          sudo $RUNNER_HOME/svc.sh start"
log_info "  Uninstall:     sudo $RUNNER_HOME/svc.sh uninstall"
