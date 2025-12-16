#!/bin/bash
# Setup Phone Provider (SMS + Voice)

set -e
cd /root/hands-off-engine

echo "═══════════════════════════════════════════════════════════"
echo "  PHONE PROVIDER SETUP"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "This adds SMS and voice call notifications"
echo "Most reliable channel - works without internet!"
echo ""

# Check if already configured
if grep -q 'YOUR_PHONE_NUMBER="+"' .env.handsoff_phone 2>/dev/null; then
    echo "✓ Already configured"
    echo ""
    python3 autonomous/phone_provider.py --test
    exit 0
fi

echo "You need:"
echo "  1. Your phone number"
echo "  2. Twilio account (free trial: \$15 credit)"
echo ""
echo "Get Twilio account:"
echo "  → https://www.twilio.com/try-twilio"
echo "  → Sign up (takes 2 minutes)"
echo "  → Get Account SID, Auth Token, Phone Number"
echo ""

read -p "Continue with setup? (yes/no): " CONTINUE

if [ "$CONTINUE" != "yes" ]; then
    echo "Setup cancelled"
    exit 0
fi

echo ""
echo "Enter your details:"
echo ""

read -p "Your phone number (+1234567890): " YOUR_PHONE
read -p "Twilio Account SID: " TWILIO_SID
read -p "Twilio Auth Token: " TWILIO_TOKEN
read -p "Twilio Phone Number (+1234567890): " TWILIO_PHONE

echo ""
echo "Configuring..."

cat > .env.handsoff_phone << EOF
YOUR_PHONE_NUMBER="$YOUR_PHONE"
TWILIO_ACCOUNT_SID="$TWILIO_SID"
TWILIO_AUTH_TOKEN="$TWILIO_TOKEN"
TWILIO_PHONE_NUMBER="$TWILIO_PHONE"
