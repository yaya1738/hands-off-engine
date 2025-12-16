#!/bin/bash
# Autonomous Multi-Provider SMS Setup

set -e
cd /root/hands-off-engine

echo "════════════════════════════════════════════════════════════"
echo "  MULTI-PROVIDER SMS SETUP"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Autonomous SMS failover across multiple providers."
echo "System handles everything - you just provide credentials."
echo ""

# Check if already configured
if grep -q 'TWILIO_ACCOUNT_SID="AC' .env.sms_providers 2>/dev/null; then
    echo "✓ Already configured"
    echo ""
    python3 autonomous/sms_provider_manager.py --test
    exit 0
fi

# Setup modes
MODE="interactive"
if [ "$1" == "--quick" ]; then
    MODE="quick"
    echo "Mode: Quick (Twilio only)"
elif [ "$1" == "--full" ]; then
    MODE="full"
    echo "Mode: Full (All providers)"
elif [ "$1" == "--autonomous" ]; then
    MODE="autonomous"
    echo "Mode: Autonomous (System provisions)"
else
    echo "Mode: Interactive"
fi

echo ""

# ================================================================
# MODE 1: AUTONOMOUS (System handles everything)
# ================================================================

if [ "$MODE" == "autonomous" ]; then
    echo "Autonomous provisioning not yet implemented."
    echo "For now, use --quick or --full mode."
    echo ""
    echo "Quick mode: Just Twilio (5 min setup)"
    echo "Full mode:  Multiple providers (15 min setup)"
    exit 1
fi

# ================================================================
# MODE 2: QUICK (Twilio only)
# ================================================================

if [ "$MODE" == "quick" ]; then
    echo "QUICK SETUP - Twilio Only"
    echo ""
    echo "This will configure Twilio as your primary SMS provider."
    echo "System will use free TextBelt as backup (1 SMS/day limit)."
    echo ""
    echo "Get Twilio credentials:"
    echo "  1. Visit: https://www.twilio.com/try-twilio"
    echo "  2. Sign up (free trial: \$15 credit)"
    echo "  3. Get Account SID, Auth Token, Phone Number"
    echo ""

    read -p "Continue? (yes/no): " CONTINUE

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

    # Read existing config
    cp .env.sms_providers .env.sms_providers.backup

    # Update values
    sed -i "s|YOUR_PHONE_NUMBER=\"\"|YOUR_PHONE_NUMBER=\"$YOUR_PHONE\"|" .env.sms_providers
    sed -i "s|TWILIO_ACCOUNT_SID=\"\"|TWILIO_ACCOUNT_SID=\"$TWILIO_SID\"|" .env.sms_providers
    sed -i "s|TWILIO_AUTH_TOKEN=\"\"|TWILIO_AUTH_TOKEN=\"$TWILIO_TOKEN\"|" .env.sms_providers
    sed -i "s|TWILIO_PHONE_NUMBER=\"\"|TWILIO_PHONE_NUMBER=\"$TWILIO_PHONE\"|" .env.sms_providers

    echo "✓ Twilio configured"
    echo ""

    # Test
    echo "Testing SMS providers..."
    python3 autonomous/sms_provider_manager.py --test

    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  SETUP COMPLETE"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Providers configured:"
    echo "  1. Twilio   (primary)"
    echo "  2. TextBelt (free backup - 1/day)"
    echo ""
    echo "Your system now has 2-provider SMS failover!"
    echo ""
    exit 0
fi

# ================================================================
# MODE 3: FULL (All providers)
# ================================================================

if [ "$MODE" == "full" ]; then
    echo "FULL SETUP - All Providers"
    echo ""
    echo "This will configure multiple SMS providers for maximum reliability."
    echo ""
    echo "You'll need accounts for:"
    echo "  1. Twilio    (recommended)"
    echo "  2. AWS SNS   (optional but recommended)"
    echo "  3. Vonage    (optional)"
    echo "  4. Plivo     (optional)"
    echo ""
    echo "Minimum: Just Twilio + your phone number"
    echo "Recommended: Twilio + AWS SNS"
    echo ""

    read -p "Continue? (yes/no): " CONTINUE

    if [ "$CONTINUE" != "yes" ]; then
        echo "Setup cancelled"
        exit 0
    fi

    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  YOUR PHONE NUMBER"
    echo "════════════════════════════════════════════════════════════"
    echo ""

    read -p "Your phone number (+1234567890): " YOUR_PHONE

    # Update phone number
    sed -i "s|YOUR_PHONE_NUMBER=\"\"|YOUR_PHONE_NUMBER=\"$YOUR_PHONE\"|" .env.sms_providers

    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  PROVIDER 1: TWILIO"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Signup: https://www.twilio.com/try-twilio"
    echo "Cost: \$0.0075/SMS (free trial: \$15)"
    echo ""

    read -p "Configure Twilio? (yes/skip): " CONF_TWILIO

    if [ "$CONF_TWILIO" == "yes" ]; then
        read -p "Twilio Account SID: " TWILIO_SID
        read -p "Twilio Auth Token: " TWILIO_TOKEN
        read -p "Twilio Phone Number: " TWILIO_PHONE

        sed -i "s|TWILIO_ACCOUNT_SID=\"\"|TWILIO_ACCOUNT_SID=\"$TWILIO_SID\"|" .env.sms_providers
        sed -i "s|TWILIO_AUTH_TOKEN=\"\"|TWILIO_AUTH_TOKEN=\"$TWILIO_TOKEN\"|" .env.sms_providers
        sed -i "s|TWILIO_PHONE_NUMBER=\"\"|TWILIO_PHONE_NUMBER=\"$TWILIO_PHONE\"|" .env.sms_providers

        echo "✓ Twilio configured"
    else
        echo "Skipped Twilio"
    fi

    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  PROVIDER 2: AWS SNS"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Console: https://console.aws.amazon.com/sns"
    echo "Cost: \$0.00645/SMS (cheapest option)"
    echo ""

    read -p "Configure AWS SNS? (yes/skip): " CONF_AWS

    if [ "$CONF_AWS" == "yes" ]; then
        read -p "AWS Access Key ID: " AWS_KEY
        read -p "AWS Secret Access Key: " AWS_SECRET
        read -p "AWS Region (us-east-1): " AWS_REGION
        AWS_REGION=${AWS_REGION:-us-east-1}

        sed -i "s|AWS_ACCESS_KEY_ID=\"\"|AWS_ACCESS_KEY_ID=\"$AWS_KEY\"|" .env.sms_providers
        sed -i "s|AWS_SECRET_ACCESS_KEY=\"\"|AWS_SECRET_ACCESS_KEY=\"$AWS_SECRET\"|" .env.sms_providers
        sed -i "s|AWS_REGION=\"us-east-1\"|AWS_REGION=\"$AWS_REGION\"|" .env.sms_providers

        echo "✓ AWS SNS configured"
    else
        echo "Skipped AWS SNS"
    fi

    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  PROVIDER 3: VONAGE"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Signup: https://dashboard.nexmo.com/sign-up"
    echo "Cost: \$0.0073/SMS"
    echo ""

    read -p "Configure Vonage? (yes/skip): " CONF_VON

    if [ "$CONF_VON" == "yes" ]; then
        read -p "Vonage API Key: " VON_KEY
        read -p "Vonage API Secret: " VON_SECRET

        sed -i "s|VONAGE_API_KEY=\"\"|VONAGE_API_KEY=\"$VON_KEY\"|" .env.sms_providers
        sed -i "s|VONAGE_API_SECRET=\"\"|VONAGE_API_SECRET=\"$VON_SECRET\"|" .env.sms_providers

        echo "✓ Vonage configured"
    else
        echo "Skipped Vonage"
    fi

    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  PROVIDER 4: PLIVO"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Signup: https://console.plivo.com/accounts/register/"
    echo "Cost: \$0.0070/SMS"
    echo ""

    read -p "Configure Plivo? (yes/skip): " CONF_PLIVO

    if [ "$CONF_PLIVO" == "yes" ]; then
        read -p "Plivo Auth ID: " PLIVO_ID
        read -p "Plivo Auth Token: " PLIVO_TOKEN

        sed -i "s|PLIVO_AUTH_ID=\"\"|PLIVO_AUTH_ID=\"$PLIVO_ID\"|" .env.sms_providers
        sed -i "s|PLIVO_AUTH_TOKEN=\"\"|PLIVO_AUTH_TOKEN=\"$PLIVO_TOKEN\"|" .env.sms_providers

        echo "✓ Plivo configured"
    else
        echo "Skipped Plivo"
    fi

    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  TESTING PROVIDERS"
    echo "════════════════════════════════════════════════════════════"
    echo ""

    python3 autonomous/sms_provider_manager.py --test

    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  SETUP COMPLETE"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Multi-provider SMS failover is now active!"
    echo ""
    echo "Check status: python3 autonomous/sms_provider_manager.py --stats"
    echo ""
    exit 0
fi

# ================================================================
# MODE 4: INTERACTIVE (Default)
# ================================================================

echo "Choose setup mode:"
echo ""
echo "  1. Quick  - Just Twilio (5 min)"
echo "  2. Full   - All providers (15 min)"
echo "  3. Manual - Edit config file yourself"
echo ""

read -p "Choice (1/2/3): " CHOICE

if [ "$CHOICE" == "1" ]; then
    exec $0 --quick
elif [ "$CHOICE" == "2" ]; then
    exec $0 --full
elif [ "$CHOICE" == "3" ]; then
    echo ""
    echo "Edit: nano .env.sms_providers"
    echo ""
    exit 0
else
    echo "Invalid choice"
    exit 1
fi
