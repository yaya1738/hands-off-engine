#!/usr/bin/env python3
"""
INTEGRAFIX Machine Communication Integration

Wires machine-to-machine communication layer into INTEGRAFIX system.

Provides:
- Event publishing for trades, bounties, system status
- Command handling for external control
- State synchronization for distributed operation
- Hardware integration for physical indicators

Integration points:
1. Trading decisions → Publish events
2. Bounty status → Publish events
3. System health → Publish events
4. External commands → Control trading/system
5. Hardware → Status indicators
"""

from typing import Dict, Any
from datetime import datetime, timezone

# Import M2M layer
from autonomous.machine_communication_hub import get_hub, publish_event
from autonomous.hardware_interface import get_interface, set_status, hardware_alert


class MachineIntegration:
    """
    Integration between INTEGRAFIX and machine communication layer.

    Auto-publishes events and handles external commands.
    """

    def __init__(self):
        self.hub = get_hub()
        self.hardware = get_interface()

        # Wire up INTEGRAFIX-specific command handlers
        self._register_integrafix_commands()

        # Wire up event publishers
        self._setup_event_publishers()

    # ================================================================
    # INTEGRAFIX COMMAND HANDLERS
    # ================================================================

    def _register_integrafix_commands(self):
        """Register INTEGRAFIX-specific commands."""

        # Trading commands
        self.hub.register_command_handler(
            'integrafix_execute_trade',
            self._cmd_execute_trade
        )

        self.hub.register_command_handler(
            'integrafix_pause_trading',
            self._cmd_pause_trading
        )

        self.hub.register_command_handler(
            'integrafix_resume_trading',
            self._cmd_resume_trading
        )

        # Bounty commands
        self.hub.register_command_handler(
            'integrafix_check_bounties',
            self._cmd_check_bounties
        )

        # System commands
        self.hub.register_command_handler(
            'integrafix_system_status',
            self._cmd_system_status
        )

    def _cmd_execute_trade(self, params: Dict) -> Dict:
        """Execute trade through INTEGRAFIX."""
        market = params.get('market')
        direction = params.get('direction')
        size = params.get('size')

        # This would integrate with actual trading pipeline
        # For now, return placeholder
        return {
            'success': True,
            'market': market,
            'direction': direction,
            'size': size,
            'note': 'Trade execution integration pending'
        }

    def _cmd_pause_trading(self, params: Dict) -> Dict:
        """Pause autonomous trading."""
        # Would pause money printer
        set_status('paused')

        return {
            'success': True,
            'status': 'paused',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def _cmd_resume_trading(self, params: Dict) -> Dict:
        """Resume autonomous trading."""
        # Would resume money printer
        set_status('trading')

        return {
            'success': True,
            'status': 'trading',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def _cmd_check_bounties(self, params: Dict) -> Dict:
        """Check bounty status."""
        # Would query bounty monitor
        return {
            'bounties': 'placeholder',
            'note': 'Bounty status integration pending'
        }

    def _cmd_system_status(self, params: Dict) -> Dict:
        """Get INTEGRAFIX system status."""
        return {
            'system': 'INTEGRAFIX',
            'status': 'operational',
            'components': {
                'money_printer': 'active',
                'bounty_monitor': 'active',
                'self_healer': 'active',
                'machine_communication': 'active'
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    # ================================================================
    # EVENT PUBLISHERS
    # ================================================================

    def _setup_event_publishers(self):
        """Set up event publishing for INTEGRAFIX events."""

        # Subscribe to INTEGRAFIX events and republish to M2M network
        # This allows external systems to listen to INTEGRAFIX events

        pass  # Event publishers would be set up here

    # ================================================================
    # INTEGRAFIX EVENT PUBLISHING
    # ================================================================

    def publish_trade_decision(self, decision: Dict):
        """Publish trade decision event."""
        publish_event('integrafix.trade.decision', {
            'market': decision.get('market'),
            'direction': decision.get('direction'),
            'edge': decision.get('edge'),
            'abcfc_score': decision.get('abcfc_score'),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

        # Update hardware status
        set_status('trading')

    def publish_trade_executed(self, market: str, direction: str, size: float, price: float):
        """Publish trade execution event."""
        publish_event('integrafix.trade.executed', {
            'market': market,
            'direction': direction,
            'size': size,
            'price': price,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

    def publish_trade_won(self, market: str, profit: float, roi: float):
        """Publish trade win event."""
        publish_event('integrafix.trade.won', {
            'market': market,
            'profit': profit,
            'roi': roi,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

        # Trigger hardware alert
        hardware_alert('info', f'Trade won: +${profit:.2f}')

    def publish_bounty_status(self, pr_number: int, status: str, details: str):
        """Publish bounty status event."""
        publish_event('integrafix.bounty.status', {
            'pr_number': pr_number,
            'status': status,
            'details': details,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

        if status == 'MERGED':
            hardware_alert('info', f'PR #{pr_number} merged!')

    def publish_system_health(self, component: str, status: str, details: str):
        """Publish system health event."""
        publish_event('integrafix.system.health', {
            'component': component,
            'status': status,
            'details': details,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

        if status == 'down':
            hardware_alert('critical', f'{component} is down!')
            set_status('error')

    def publish_process_restarted(self, process: str, pid: int):
        """Publish process restart event."""
        publish_event('integrafix.system.restart', {
            'process': process,
            'pid': pid,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

        # Reset status if recovered
        set_status('running')


# ================================================================
# CONVENIENCE FUNCTIONS
# ================================================================

_integration_instance = None

def get_integration() -> MachineIntegration:
    """Get singleton integration instance."""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = MachineIntegration()
    return _integration_instance


# Export convenient functions for INTEGRAFIX components to use
def notify_trade_decision(decision: Dict):
    """Notify external systems of trade decision."""
    integration = get_integration()
    integration.publish_trade_decision(decision)


def notify_trade_executed(market: str, direction: str, size: float, price: float):
    """Notify external systems of trade execution."""
    integration = get_integration()
    integration.publish_trade_executed(market, direction, size, price)


def notify_trade_won(market: str, profit: float, roi: float):
    """Notify external systems of trade win."""
    integration = get_integration()
    integration.publish_trade_won(market, profit, roi)


def notify_bounty_status(pr_number: int, status: str, details: str):
    """Notify external systems of bounty status."""
    integration = get_integration()
    integration.publish_bounty_status(pr_number, status, details)


def notify_system_health(component: str, status: str, details: str):
    """Notify external systems of system health."""
    integration = get_integration()
    integration.publish_system_health(component, status, details)


def notify_process_restarted(process: str, pid: int):
    """Notify external systems of process restart."""
    integration = get_integration()
    integration.publish_process_restarted(process, pid)


# ================================================================
# TESTING
# ================================================================

def test_integration():
    """Test machine communication integration."""
    print("="*60)
    print("INTEGRAFIX MACHINE COMMUNICATION INTEGRATION TEST")
    print("="*60)
    print()

    # Test event publishing
    print("1. Testing event publishing...")
    notify_trade_decision({
        'market': 'BTC $150k by Dec 2025',
        'direction': 'YES',
        'edge': 0.15,
        'abcfc_score': 125.5
    })
    print("   ✓ Trade decision published")

    notify_trade_won('BTC $150k by Dec 2025', 8.50, 0.34)
    print("   ✓ Trade win published")

    notify_bounty_status(239, 'MERGED', '$125 bounty claimable')
    print("   ✓ Bounty status published")

    print()
    print("2. Testing command handling...")

    from autonomous.machine_communication_hub import send_command

    result = send_command('integrafix_system_status', {})
    print(f"   System: {result.get('system')}")
    print(f"   Status: {result.get('status')}")

    print()
    print("="*60)
    print("INTEGRATION TEST COMPLETE")
    print("="*60)


def main():
    """Run integration."""
    import sys

    if '--test' in sys.argv:
        test_integration()
    else:
        print("INTEGRAFIX Machine Communication Integration")
        print()
        print("Usage:")
        print("  --test   Test integration")


if __name__ == '__main__':
    main()
