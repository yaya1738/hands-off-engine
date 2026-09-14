#!/bin/bash
# Bootstrap script for new compute nodes
# Run this on new droplets to set them up for the hands-off cluster
#
# Usage (from pm-helper): ssh root@<IP> 'bash -s' < scripts/bootstrap_compute_node.sh

set -e

echo "=== Hands-Off Compute Node Bootstrap ==="
echo "Timestamp: $(date -Iseconds)"

# Install dependencies
echo "[1/6] Installing dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip git curl jq

# Clone repo
echo "[2/6] Cloning hands-off-engine..."
if [ -d /root/hands-off-engine ]; then
    cd /root/hands-off-engine && git pull
else
    git clone https://github.com/yaya1738/hands-off-engine.git /root/hands-off-engine
fi

# Install Python requirements
echo "[3/6] Installing Python packages..."
cd /root/hands-off-engine
pip3 install -q -r requirements.txt 2>/dev/null || pip3 install -q requests python-dotenv

# Copy environment files from pm-helper (placeholder - needs manual setup)
echo "[4/6] Setting up environment..."
if [ ! -f /root/hands-off-engine/.env ]; then
    echo "WARNING: No .env file found. Copy from pm-helper:"
    echo "  scp root@138.68.103.156:/root/hands-off-engine/.env /root/hands-off-engine/.env"
fi

# Set up SSH key for inter-node communication
echo "[5/6] Setting up SSH..."
mkdir -p /root/.ssh
chmod 700 /root/.ssh

# Add pm-helper's public key if not present
PM_HELPER_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKUOlcMgjyYnAknQhzB/hHMZewPEx7XPLAd/Q2vLt1JD handsoff-do138"
grep -q "handsoff-do138" /root/.ssh/authorized_keys 2>/dev/null || echo "$PM_HELPER_KEY" >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

# Generate this node's SSH key if not present
if [ ! -f /root/.ssh/id_ed25519 ]; then
    ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519 -N "" -C "$(hostname)"
fi

# Report status
echo "[6/6] Node setup complete!"
echo ""
echo "=== Node Info ==="
echo "Hostname: $(hostname)"
echo "IP: $(curl -s ifconfig.me)"
echo "vCPU: $(nproc)"
echo "RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $2}')"
echo ""
echo "SSH public key for this node:"
cat /root/.ssh/id_ed25519.pub
echo ""
echo "=== Next Steps ==="
echo "1. Copy .env from pm-helper: scp root@138.68.103.156:/root/hands-off-engine/.env* /root/hands-off-engine/"
echo "2. Add this node's SSH key to pm-helper's authorized_keys"
echo "3. Node is ready for distributed workloads"
