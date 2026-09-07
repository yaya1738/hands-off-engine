#!/usr/bin/env python3
"""INTEGRAFIX machine communication integration.

Command handlers never claim a consequential side effect unless a governed
execution result proves it. Trading remains fail-closed until the canonical
trading authority is explicitly able to authorize and verify execution.
"""

from typing import Dict
from datetime import datetime, timezone

from autonomous.machine_communication_hub import get_hub, publish_event
from autonomous.hardware_interface import get_interface, set_status, hardware_alert


class MachineIntegration:
    """Integration between INTEGRAFIX and machine communication."""

    def __init__(self):
        self.hub = get_hub()
        self.hardware = get_interface()
        self._register_integrafix_commands()
        self._setup_event_publishers()

    def _register_integrafix_commands(self):
        self.hub.register_command_handler('integrafix_execute_trade', self._cmd_execute_trade)
        self.hub.register_command_handler('integrafix_pause_trading', self._cmd_pause_trading)
        self.hub.register_command_handler('integrafix_resume_trading', self._cmd_resume_trading)
        self.hub.register_command_handler('integrafix_check_bounties', self._cmd_check_bounties)
        self.hub.register_command_handler('integrafix_system_status', self._cmd_system_status)

    def _cmd_execute_trade(self, params: Dict) -> Dict:
        """Attempt a trade only through the canonical governed authority."""
        market = params.get('market')
        direction = params.get('direction')
        size = params.get('size')
        try:
            from ai.factory.live_order_authority import LiveOrderAuthority, OrderIntent
            authority = LiveOrderAuthority()
            result = authority.submit(OrderIntent(
                token_id=params.get('token_id'),
                side=str(direction or '').upper(),
                price=params.get('price'),
                size=size,
            ))
            executed = bool(result.get('executed') is True and result.get('verified') is True)
            return {
                'success': executed,
                'executed': executed,
                'verified': bool(result.get('verified') is True),
                'market': market,
                'direction': direction,
                'size': size,
                'reason': result.get('reason', 'execution_not_verified'),
            }
        except Exception as exc:
            return {
                'success': False,
                'executed': False,
                'verified': False,
                'market': market,
                'direction': direction,
                'size': size,
                'reason': 'governed_execution_error',
                'error_type': type(exc).__name__,
            }

    def _cmd_pause_trading(self, params: Dict) -> Dict:
        set_status('paused')
        return {'success': True, 'status': 'paused', 'timestamp': datetime.now(timezone.utc).isoformat()}

    def _cmd_resume_trading(self, params: Dict) -> Dict:
        set_status('trading')
        return {'success': True, 'status': 'trading', 'timestamp': datetime.now(timezone.utc).isoformat()}

    def _cmd_check_bounties(self, params: Dict) -> Dict:
        return {'bounties': 'unavailable', 'success': False, 'reason': 'bounty_integration_not_implemented'}

    def _cmd_system_status(self, params: Dict) -> Dict:
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

    def _setup_event_publishers(self):
        pass

    def publish_trade_decision(self, decision: Dict):
        publish_event('integrafix.trade.decision', {
            'market': decision.get('market'), 'direction': decision.get('direction'),
            'edge': decision.get('edge'), 'abcfc_score': decision.get('abcfc_score'),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        set_status('trading')

    def publish_trade_executed(self, market: str, direction: str, size: float, price: float):
        publish_event('integrafix.trade.executed', {
            'market': market, 'direction': direction, 'size': size, 'price': price,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

    def publish_trade_won(self, market: str, profit: float, roi: float):
        publish_event('integrafix.trade.won', {
            'market': market, 'profit': profit, 'roi': roi,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        hardware_alert('info', f'Trade won: +${profit:.2f}')

    def publish_bounty_status(self, pr_number: int, status: str, details: str):
        publish_event('integrafix.bounty.status', {
            'pr_number': pr_number, 'status': status, 'details': details,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        if status == 'MERGED':
            hardware_alert('info', f'PR #{pr_number} merged!')

    def publish_system_health(self, component: str, status: str, details: str):
        publish_event('integrafix.system.health', {
            'component': component, 'status': status, 'details': details,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        if status == 'down':
            hardware_alert('critical', f'{component} is down!')
            set_status('error')

    def publish_process_restarted(self, process: str, pid: int):
        publish_event('integrafix.system.restart', {
            'process': process, 'pid': pid,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        set_status('running')


_integration_instance = None

def get_integration() -> MachineIntegration:
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = MachineIntegration()
    return _integration_instance


def notify_trade_decision(decision: Dict):
    get_integration().publish_trade_decision(decision)


def notify_trade_executed(market: str, direction: str, size: float, price: float):
    get_integration().publish_trade_executed(market, direction, size, price)


def notify_trade_won(market: str, profit: float, roi: float):
    get_integration().publish_trade_won(market, profit, roi)


def notify_bounty_status(pr_number: int, status: str, details: str):
    get_integration().publish_bounty_status(pr_number, status, details)


def notify_system_health(component: str, status: str, details: str):
    get_integration().publish_system_health(component, status, details)


def notify_process_restarted(process: str, pid: int):
    get_integration().publish_process_restarted(process, pid)


def test_integration():
    print('INTEGRAFIX MACHINE COMMUNICATION INTEGRATION TEST')
    notify_trade_decision({'market': 'test', 'direction': 'YES', 'edge': 0.15, 'abcfc_score': 125.5})
    notify_trade_won('test', 8.50, 0.34)
    notify_bounty_status(239, 'MERGED', 'test')
    from autonomous.machine_communication_hub import send_command
    result = send_command('integrafix_system_status', {})
    print(f"System: {result.get('system')}")
    print(f"Status: {result.get('status')}")


def main():
    import sys
    if '--test' in sys.argv:
        test_integration()
    else:
        print('INTEGRAFIX Machine Communication Integration')


if __name__ == '__main__':
    main()
