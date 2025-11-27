#!/bin/bash
# Install Full Business Automation
# Makes everything run automatically

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "========================================================================"
echo "  🤖 AUTONOMOUS BUSINESS ENGINE INSTALLER 🤖"
echo "========================================================================"
echo ""
echo "This will make EVERYTHING automatic:"
echo "  - Continuous financial monitoring"
echo "  - Automatic emergency detection"
echo "  - Automatic cost optimization"
echo "  - Automatic opportunity tracking"
echo "  - Self-healing capabilities"
echo ""
echo "Installation options:"
echo "  1) Systemd Service (Recommended - runs 24/7 as system service)"
echo "  2) Cron Jobs (Alternative - scheduled runs)"
echo "  3) Manual (Just test, don't install)"
echo ""

read -p "Choose option (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "Installing as Systemd Service..."
        echo ""

        # Create logs directory
        mkdir -p "$REPO_ROOT/logs"

        # Copy service file
        SERVICE_FILE="$SCRIPT_DIR/systemd/yair-business-autonomous.service"

        # Update paths in service file
        TEMP_SERVICE="/tmp/yair-business-autonomous.service"
        sed "s|/home/user/hands-off-engine|$REPO_ROOT|g" "$SERVICE_FILE" > "$TEMP_SERVICE"
        sed -i "s|User=%u|User=$USER|g" "$TEMP_SERVICE"

        # Install service
        if [ "$EUID" -eq 0 ]; then
            # Running as root
            cp "$TEMP_SERVICE" /etc/systemd/system/yair-business-autonomous.service
            systemctl daemon-reload
            systemctl enable yair-business-autonomous.service
            systemctl start yair-business-autonomous.service

            echo "✅ Service installed and started!"
            echo ""
            echo "Commands:"
            echo "  Status:  sudo systemctl status yair-business-autonomous"
            echo "  Stop:    sudo systemctl stop yair-business-autonomous"
            echo "  Restart: sudo systemctl restart yair-business-autonomous"
            echo "  Logs:    sudo journalctl -u yair-business-autonomous -f"
            echo "  Disable: sudo systemctl disable yair-business-autonomous"
        else
            # Not root - use user service
            mkdir -p ~/.config/systemd/user/
            cp "$TEMP_SERVICE" ~/.config/systemd/user/yair-business-autonomous.service

            systemctl --user daemon-reload
            systemctl --user enable yair-business-autonomous.service
            systemctl --user start yair-business-autonomous.service

            # Enable lingering so service runs without login
            loginctl enable-linger $USER

            echo "✅ User service installed and started!"
            echo ""
            echo "Commands:"
            echo "  Status:  systemctl --user status yair-business-autonomous"
            echo "  Stop:    systemctl --user stop yair-business-autonomous"
            echo "  Restart: systemctl --user restart yair-business-autonomous"
            echo "  Logs:    journalctl --user -u yair-business-autonomous -f"
            echo "  Disable: systemctl --user disable yair-business-autonomous"
        fi

        rm "$TEMP_SERVICE"

        echo ""
        echo "🎉 AUTONOMOUS ENGINE IS NOW RUNNING 24/7!"
        ;;

    2)
        echo ""
        echo "Installing Cron Jobs..."
        echo ""

        # Create crontab entries
        CRON_FILE="/tmp/yair-business-cron"

        cat > "$CRON_FILE" <<EOF
# Yair Siegel Autonomous Business Engine
# Added: $(date)

# Sync every 30 minutes
*/30 * * * * cd $REPO_ROOT && /usr/bin/python3 business/business_sync_engine.py --once >> logs/sync_cron.log 2>&1

# Full autonomous cycle every hour
0 * * * * cd $REPO_ROOT && /usr/bin/python3 business/autonomous_business_engine.py --once >> logs/autonomous_cron.log 2>&1

# Daily status check at 9 AM
0 9 * * * cd $REPO_ROOT && /usr/bin/python3 business/emergency_status_monitor.py >> logs/daily_status.log 2>&1

# Daily optimization at 10 AM
0 10 * * * cd $REPO_ROOT && /usr/bin/python3 business/business_optimization_agent.py >> logs/optimization_cron.log 2>&1

EOF

        # Install cron jobs
        crontab -l 2>/dev/null > /tmp/current_cron || true
        cat "$CRON_FILE" >> /tmp/current_cron
        crontab /tmp/current_cron

        rm "$CRON_FILE" /tmp/current_cron

        echo "✅ Cron jobs installed!"
        echo ""
        echo "Schedule:"
        echo "  - Sync: Every 30 minutes"
        echo "  - Autonomous cycle: Every hour"
        echo "  - Daily status: 9 AM"
        echo "  - Daily optimization: 10 AM"
        echo ""
        echo "View: crontab -l"
        echo "Remove: crontab -e (delete the lines)"
        ;;

    3)
        echo ""
        echo "Testing autonomous engine (manual mode)..."
        echo ""

        cd "$REPO_ROOT"
        python3 business/autonomous_business_engine.py --once

        echo ""
        echo "Test complete! To run continuously:"
        echo "  python3 business/autonomous_business_engine.py"
        echo ""
        echo "Or install with this script (option 1 or 2)"
        ;;

    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "========================================================================"
echo "  Installation Complete!"
echo "========================================================================"
echo ""
echo "Your business is now fully autonomous!"
echo ""
echo "What happens automatically:"
echo "  ✅ Financial monitoring (every 30min)"
echo "  ✅ Emergency detection (real-time)"
echo "  ✅ Cost optimization (automatic)"
echo "  ✅ Opportunity tracking (continuous)"
echo "  ✅ Health scoring (updated)"
echo "  ✅ Self-healing (automatic)"
echo ""
echo "View logs:"
echo "  tail -f $REPO_ROOT/logs/autonomous_engine.log"
echo ""
echo "Check status:"
echo "  python3 business/integrated_emergency_dashboard.py"
echo ""
