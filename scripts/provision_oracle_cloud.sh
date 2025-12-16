#!/bin/bash
###############################################################################
# Oracle Cloud Provisioning Script
# =================================
#
# Provisions Oracle Cloud Always Free instance for hands-off-engine.
# ABCFC Score: 82.88 (highest)
#
# This script guides you through:
# 1. Oracle Cloud account setup
# 2. VM instance creation
# 3. SSH key configuration
# 4. Initial server setup
#
# Master: Yair Siegel
###############################################################################

set -e

echo "================================================================================"
echo "☁️  ORACLE CLOUD PROVISIONING - Always Free Tier"
echo "================================================================================"
echo ""
echo "📊 ABCFC Analysis Result:"
echo "  Score: 82.88 (highest)"
echo "  Cost: $0/month (forever)"
echo "  Specs: 1 CPU, 1GB RAM, 50GB storage"
echo "  Locations: 4 (US-Phoenix, US-Ashburn, Frankfurt, London)"
echo ""

# ===== STEP 1: Account Setup =====
echo "================================================================================"
echo "📝 STEP 1: Oracle Cloud Account Setup"
echo "================================================================================"
echo ""
echo "1. Go to: https://www.oracle.com/cloud/free/"
echo "2. Click 'Start for free'"
echo "3. Fill in account details"
echo "4. Verify email"
echo "5. Add credit card (won't be charged for Always Free)"
echo ""
read -p "Press Enter when account is created..."

# ===== STEP 2: Instance Configuration =====
echo ""
echo "================================================================================"
echo "🖥️  STEP 2: Create VM Instance"
echo "================================================================================"
echo ""
echo "Instance Configuration:"
echo "  Name: hands-off-engine-base2"
echo "  Image: Ubuntu 22.04 (Canonical Ubuntu)"
echo "  Shape: VM.Standard.E2.1.Micro (Always Free)"
echo "  CPU: 1 core"
echo "  RAM: 1GB"
echo "  Storage: 50GB"
echo ""
echo "Location (choose one based on latency):"
echo "  1. US West (Phoenix) - Best for US West Coast"
echo "  2. US East (Ashburn) - Best for US East Coast"
echo "  3. Germany (Frankfurt) - Best for Europe"
echo "  4. UK (London) - Best for UK/EU"
echo ""
read -p "Enter your choice (1-4): " location_choice

case $location_choice in
    1) REGION="us-phoenix-1" ;;
    2) REGION="us-ashburn-1" ;;
    3) REGION="eu-frankfurt-1" ;;
    4) REGION="uk-london-1" ;;
    *) REGION="us-phoenix-1" ;;
esac

echo ""
echo "Selected Region: $REGION"
echo ""

# ===== STEP 3: SSH Key Generation =====
echo "================================================================================"
echo "🔑 STEP 3: SSH Key Setup"
echo "================================================================================"
echo ""

# Check if SSH key exists
if [ -f ~/.ssh/id_rsa.pub ]; then
    echo "✅ SSH key already exists"
    echo ""
    echo "Your public key:"
    cat ~/.ssh/id_rsa.pub
else
    echo "Generating new SSH key..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N "" -C "hands-off-engine-oracle"
    echo "✅ SSH key generated"
    echo ""
    echo "Your public key:"
    cat ~/.ssh/id_rsa.pub
fi

echo ""
echo "📋 COPY THIS PUBLIC KEY - You'll need it for Oracle Cloud"
echo ""
read -p "Press Enter when ready to continue..."

# ===== STEP 4: Create Instance via Web Console =====
echo ""
echo "================================================================================"
echo "🚀 STEP 4: Create Instance (Web Console)"
echo "================================================================================"
echo ""
echo "Go to Oracle Cloud Console and create instance:"
echo ""
echo "1. Login to: https://cloud.oracle.com/"
echo "2. Navigate to: Compute → Instances"
echo "3. Click 'Create Instance'"
echo ""
echo "Configuration:"
echo "  Name: hands-off-engine-base2"
echo "  Availability Domain: Any (AD-1 recommended)"
echo "  Image: Canonical Ubuntu 22.04"
echo "  Shape: VM.Standard.E2.1.Micro (Always Free eligible)"
echo "  Virtual Cloud Network: Create new VCN (auto-generated)"
echo "  Subnet: Public subnet (auto-generated)"
echo "  Assign Public IP: YES ✓"
echo "  SSH Keys: Paste your public key from above"
echo ""
echo "4. Click 'Create'"
echo "5. Wait for instance to provision (2-3 minutes)"
echo "6. Copy the Public IP address"
echo ""
read -p "Press Enter when instance is created..."

# Get IP address
echo ""
read -p "Enter the instance PUBLIC IP address: " INSTANCE_IP

# Validate IP
if [[ ! $INSTANCE_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Invalid IP address format"
    exit 1
fi

echo ""
echo "✅ Instance IP: $INSTANCE_IP"

# ===== STEP 5: Configure Firewall =====
echo ""
echo "================================================================================"
echo "🔥 STEP 5: Configure Firewall Rules"
echo "================================================================================"
echo ""
echo "In Oracle Cloud Console:"
echo ""
echo "1. Go to: Networking → Virtual Cloud Networks"
echo "2. Click on your VCN (e.g., vcn-xxxxx)"
echo "3. Click on 'Security Lists' → 'Default Security List'"
echo "4. Click 'Add Ingress Rules'"
echo ""
echo "Add these rules:"
echo "  Rule 1 - SSH:"
echo "    Source CIDR: 0.0.0.0/0"
echo "    IP Protocol: TCP"
echo "    Destination Port: 22"
echo ""
echo "  Rule 2 - HTTPS (optional):"
echo "    Source CIDR: 0.0.0.0/0"
echo "    IP Protocol: TCP"
echo "    Destination Port: 443"
echo ""
read -p "Press Enter when firewall rules are configured..."

# ===== STEP 6: First Connection =====
echo ""
echo "================================================================================"
echo "🔌 STEP 6: First Connection Test"
echo "================================================================================"
echo ""

echo "Testing SSH connection to $INSTANCE_IP..."
echo ""

# Try to connect
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@$INSTANCE_IP "echo '✅ Connection successful!'" 2>/dev/null

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSH connection successful!"
else
    echo ""
    echo "⚠️  Connection failed. Troubleshooting:"
    echo "  1. Wait 2-3 minutes for instance to fully boot"
    echo "  2. Check firewall rules allow port 22"
    echo "  3. Verify public IP is correct"
    echo "  4. Try manual connection: ssh ubuntu@$INSTANCE_IP"
    echo ""
    read -p "Press Enter to retry..."
    ssh -o StrictHostKeyChecking=no ubuntu@$INSTANCE_IP "echo '✅ Connection successful!'"
fi

# ===== STEP 7: Initial Server Setup =====
echo ""
echo "================================================================================"
echo "⚙️  STEP 7: Initial Server Setup"
echo "================================================================================"
echo ""

echo "Running initial setup on remote server..."
echo ""

ssh ubuntu@$INSTANCE_IP << 'ENDSSH'
# Update system
echo "Updating system packages..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# Install essentials
echo "Installing essential packages..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    git \
    curl \
    htop \
    tree

# Configure firewall on instance
echo "Configuring Ubuntu firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 443/tcp
echo "y" | sudo ufw enable

echo "✅ Server setup complete"
ENDSSH

# ===== STEP 8: Save Configuration =====
echo ""
echo "================================================================================"
echo "💾 STEP 8: Save Configuration"
echo "================================================================================"
echo ""

# Create config file
cat > ~/.oracle_cloud_config << EOF
{
  "provider": "oracle",
  "instance_name": "hands-off-engine-base2",
  "region": "$REGION",
  "instance_ip": "$INSTANCE_IP",
  "username": "ubuntu",
  "ssh_key": "~/.ssh/id_rsa",
  "provisioned_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "specs": {
    "cpu_cores": 1,
    "ram_gb": 1,
    "storage_gb": 50
  },
  "cost_per_month": 0.0,
  "free_tier": "forever"
}
EOF

echo "✅ Configuration saved to: ~/.oracle_cloud_config"

# Create SSH alias
if ! grep -q "hands-off-engine-base2" ~/.ssh/config 2>/dev/null; then
    mkdir -p ~/.ssh
    cat >> ~/.ssh/config << EOF

# hands-off-engine Base 2 (Oracle Cloud)
Host base2
    HostName $INSTANCE_IP
    User ubuntu
    IdentityFile ~/.ssh/id_rsa
    StrictHostKeyChecking no
EOF
    echo "✅ SSH alias created: ssh base2"
fi

# ===== PROVISIONING COMPLETE =====
echo ""
echo "================================================================================"
echo "🎉 PROVISIONING COMPLETE!"
echo "================================================================================"
echo ""
echo "✅ Oracle Cloud instance is ready!"
echo ""
echo "📍 Connection Details:"
echo "  IP Address: $INSTANCE_IP"
echo "  Username: ubuntu"
echo "  SSH Key: ~/.ssh/id_rsa"
echo ""
echo "🔗 Quick Access:"
echo "  ssh base2"
echo "  OR"
echo "  ssh ubuntu@$INSTANCE_IP"
echo ""
echo "📊 Instance Info:"
echo "  Provider: Oracle Cloud"
echo "  Region: $REGION"
echo "  Cost: $0/month (forever)"
echo "  Specs: 1 CPU, 1GB RAM, 50GB storage"
echo ""
echo "🚀 NEXT STEPS:"
echo ""
echo "1. Connect to new base:"
echo "   ssh base2"
echo ""
echo "2. Run setup script:"
echo "   curl -o setup.sh https://raw.githubusercontent.com/yaya1738/hands-off-engine/local-sync/scripts/setup_new_base.sh"
echo "   chmod +x setup.sh"
echo "   ./setup.sh"
echo ""
echo "3. Configure API keys and start system"
echo ""
echo "================================================================================"
echo "⚠️  REMEMBER:"
echo "  - This is BASE 2 (new hardware)"
echo "  - Current base is still running (don't touch it)"
echo "  - Two bases = redundancy"
echo "================================================================================"
echo ""

echo "Configuration saved to: ~/.oracle_cloud_config"
echo ""
echo "✅ Hardware provisioned and ready!"
