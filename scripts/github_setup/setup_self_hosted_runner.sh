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

# Idempotency guard: never tear down an existing runner merely because deployment
# was re-run. Verify its configured repository before deciding whether repair is safe.
if [ -f "$RUNNER_HOME/.runner" ]; then
    CONFIGURED_REPO=$(python3 - "$RUNNER_HOME/.runner" <<'PY'
import json
import sys
from pathlib import Path

try:
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    url = data.get("serverUrl", "")
    prefix = "https://github.com/"
    if url.startswith(prefix):
        print(url[len(prefix):].rstrip("/"))
except (OSError, json.JSONDecodeError):
    pass
PY
)
    if [ "$CONFIGURED_REPO" != "$REPO" ]; then
        log_error "Existing runner is configured for a different repository; refusing to replace it."
        exit 1
    fi

    if [ ! -x "$RUNNER_HOME/svc.sh" ]; then
        log_error "Existing runner configuration found but service manager is missing; refusing destructive repair."
        exit 1
    fi

    if "$RUNNER_HOME/svc.sh" status >/dev/null 2>&1; then
        log_info "Existing runner is already configured and its service is active; no re-registration needed."
        exit 0
    fi

    log_warn "Existing runner is configured for this repository but its service is not active; attempting a non-destructive restart."
    "$RUNNER_HOME/svc.sh" start
    "$RUNNER_HOME/svc.sh" status
    log_info "Existing runner service restarted successfully."
    exit 0
fi

# Create runner user if doesn't exist
if ! id -u "$RUNNER_USER" >/dev/null 2>&1; then
    log_info "Creating runner user: $RUNNER_USER"
    useradd -m -s /bin/bash "$RUNNER_USER"
fi

# Create runner directory
log_info "Creating runner directory: $RUNNER_HOME"
mkdir -p "$RUNNER_HOME"
cd "$RUNNER_HOME"

# Download and verify the exact pinned runner artifact on every setup run.
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

# Set ownership
chown -R "$RUNNER_USER:$RUNNER_USER" "$RUNNER_HOME"

# Configure runner as runner user.
# The runner CLI requires --token, so the token must briefly exist in the config process argv.
# Keep it out of the parent su command line by passing it through a root-only temporary file.
log_info "Configuring runner"
RUNNER_TOKEN_FILE=$(mktemp "$RUNNER_HOME/.runner-token.XXXXXX")
chmod 600 "$RUNNER_TOKEN_FILE"
printf '%s' "$RUNNER_TOKEN" > "$RUNNER_TOKEN_FILE"
chown "$RUNNER_USER:$RUNNER_USER" "$RUNNER_TOKEN_FILE"
trap 'rm -f "$RUNNER_TOKEN_FILE"' EXIT

# A pre-existing .runner configuration is handled by the idempotency guard above.
# Re-registration is intentionally not performed automatically.

# Configure runner
su - "$RUNNER_USER" -c "TOKEN=\$(cat \"$RUNNER_TOKEN_FILE\"); cd \"$RUNNER_HOME\" && ./config.sh \
    --url \"https://github.com/$REPO\" \
    --token \"\$TOKEN\" \
    --name \"droplet-\$(hostname)\" \
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
