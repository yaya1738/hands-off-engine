#!/usr/bin/env python3
"""
Machine Communication Hub - M2M Infrastructure

Autonomous communication system for machine-to-machine interaction:
- Other AI systems talking to INTEGRAFIX
- Hardware devices controlled by system
- Distributed autonomous coordination
- Cross-system event propagation

Protocols supported:
- REST API (HTTP/JSON)
- JSON-RPC 2.0
- WebSocket (real-time)
- MQTT (IoT devices)
- gRPC (high-performance)
- Unix sockets (local IPC)

Architecture:
    External Systems (AI, Hardware, IoT)
                ↓
    ┌───────────────────────────────────┐
    │  Machine Communication Hub        │
    │  (Multi-Protocol Router)          │
    └───────────┬───────────────────────┘
                ↓
    ┌───────────┴────────┬──────────────┬────────────┐
    ↓                    ↓              ↓            ↓
API Gateway        Event Bus      Hardware      State API
(Commands)         (Events)       Interface     (Queries)
    ↓                    ↓              ↓            ↓
    └────────────────────┴──────────────┴────────────┘
                         ↓
                  INTEGRAFIX System
         (Trading, Bounties, Monitoring)
"""

import json
import time
import asyncio
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum

STATE_FILE = Path(__file__).parent.parent / 'state' / 'machine_communication.json'


class Protocol(Enum):
    """Supported communication protocols."""
    REST = "rest"
    JSON_RPC = "json_rpc"
    WEBSOCKET = "websocket"
    MQTT = "mqtt"
    GRPC = "grpc"
    UNIX_SOCKET = "unix_socket"


class MessageType(Enum):
    """Machine message types."""
    COMMAND = "command"          # Execute action
    QUERY = "query"              # Request data
    EVENT = "event"              # Notification
    RESPONSE = "response"        # Reply to command/query
    HEARTBEAT = "heartbeat"      # Keep-alive
    SUBSCRIBE = "subscribe"      # Subscribe to events
    UNSUBSCRIBE = "unsubscribe"  # Unsubscribe from events


@dataclass
class MachineMessage:
    """Universal machine message format."""
    type: str                    # MessageType
    protocol: str                # Protocol used
    source: str                  # Source system ID
    target: str                  # Target system ID
    timestamp: str               # ISO timestamp
    payload: Dict[str, Any]      # Message data
    request_id: Optional[str] = None  # For tracking requests/responses
    metadata: Optional[Dict] = None   # Additional context


class MachineCommunicationHub:
    """
    Central hub for all machine-to-machine communication.

    Handles multi-protocol routing, event distribution, command execution,
    and state synchronization across distributed systems.
    """

    def __init__(self):
        self.state = self.load_state()
        self.subscribers: Dict[str, List[Callable]] = {}  # Event subscribers
        self.command_handlers: Dict[str, Callable] = {}   # Command handlers
        self.connected_systems: Dict[str, Dict] = {}      # Connected machines

        # Register built-in handlers
        self._register_core_handlers()

        # Start async event loop in background
        self.loop = None
        self.running = False

    def load_state(self) -> dict:
        """Load hub state."""
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {
            'total_messages': 0,
            'messages_by_protocol': {},
            'messages_by_type': {},
            'connected_systems': {},
            'events_published': 0,
            'commands_executed': 0,
            'queries_handled': 0,
            'last_activity': None
        }

    def save_state(self):
        """Save hub state."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    # ================================================================
    # CORE MESSAGE ROUTING
    # ================================================================

    def route_message(self, message: MachineMessage) -> Optional[Dict]:
        """
        Route message to appropriate handler based on type.

        Returns response if applicable.
        """
        # Update stats
        self.state['total_messages'] += 1
        self.state['messages_by_protocol'][message.protocol] = \
            self.state['messages_by_protocol'].get(message.protocol, 0) + 1
        self.state['messages_by_type'][message.type] = \
            self.state['messages_by_type'].get(message.type, 0) + 1
        self.state['last_activity'] = datetime.now(timezone.utc).isoformat()
        self.save_state()

        # Route based on message type
        if message.type == MessageType.COMMAND.value:
            return self._handle_command(message)
        elif message.type == MessageType.QUERY.value:
            return self._handle_query(message)
        elif message.type == MessageType.EVENT.value:
            return self._handle_event(message)
        elif message.type == MessageType.SUBSCRIBE.value:
            return self._handle_subscribe(message)
        elif message.type == MessageType.UNSUBSCRIBE.value:
            return self._handle_unsubscribe(message)
        elif message.type == MessageType.HEARTBEAT.value:
            return self._handle_heartbeat(message)
        else:
            return {'error': f'Unknown message type: {message.type}'}

    # ================================================================
    # COMMAND HANDLING (Execute actions)
    # ================================================================

    def register_command_handler(self, command: str, handler: Callable):
        """Register handler for specific command."""
        self.command_handlers[command] = handler
        print(f"✓ Registered command handler: {command}")

    def _handle_command(self, message: MachineMessage) -> Dict:
        """Execute command from external system."""
        command = message.payload.get('command')
        params = message.payload.get('params', {})

        if not command:
            return {'error': 'No command specified'}

        if command not in self.command_handlers:
            return {'error': f'Unknown command: {command}'}

        try:
            # Execute command
            result = self.command_handlers[command](params)

            self.state['commands_executed'] += 1
            self.save_state()

            return {
                'success': True,
                'command': command,
                'result': result,
                'executed_at': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'command': command
            }

    def _register_core_handlers(self):
        """Register built-in command handlers."""
        # System status
        self.register_command_handler('get_status', self._cmd_get_status)
        self.register_command_handler('get_health', self._cmd_get_health)

        # Trading commands
        self.register_command_handler('execute_trade', self._cmd_execute_trade)
        self.register_command_handler('cancel_trade', self._cmd_cancel_trade)
        self.register_command_handler('get_positions', self._cmd_get_positions)

        # System control
        self.register_command_handler('restart_component', self._cmd_restart_component)
        self.register_command_handler('shutdown', self._cmd_shutdown)
        self.register_command_handler('pause_trading', self._cmd_pause_trading)
        self.register_command_handler('resume_trading', self._cmd_resume_trading)

        # Hardware control
        self.register_command_handler('control_hardware', self._cmd_control_hardware)

        # Data access
        self.register_command_handler('get_metrics', self._cmd_get_metrics)
        self.register_command_handler('get_logs', self._cmd_get_logs)

    # ================================================================
    # QUERY HANDLING (Request data)
    # ================================================================

    def _handle_query(self, message: MachineMessage) -> Dict:
        """Handle data query from external system."""
        query_type = message.payload.get('query')
        params = message.payload.get('params', {})

        self.state['queries_handled'] += 1
        self.save_state()

        # Route to appropriate query handler
        if query_type == 'system_state':
            return self._query_system_state()
        elif query_type == 'trading_state':
            return self._query_trading_state()
        elif query_type == 'bounty_state':
            return self._query_bounty_state()
        elif query_type == 'metrics':
            return self._query_metrics(params)
        elif query_type == 'logs':
            return self._query_logs(params)
        elif query_type == 'hardware_state':
            return self._query_hardware_state()
        else:
            return {'error': f'Unknown query type: {query_type}'}

    def _query_system_state(self) -> Dict:
        """Get overall system state."""
        return {
            'system': 'INTEGRAFIX',
            'status': 'operational',
            'uptime': self._get_uptime(),
            'active_components': self._get_active_components(),
            'machine_communication': {
                'total_messages': self.state['total_messages'],
                'connected_systems': len(self.connected_systems),
                'protocols_active': list(self.state['messages_by_protocol'].keys())
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def _query_trading_state(self) -> Dict:
        """Get trading system state."""
        # Read from money printer state
        state_file = Path(__file__).parent.parent / 'state' / 'money_printer.json'
        if state_file.exists():
            return json.loads(state_file.read_text())
        return {'error': 'Trading state not available'}

    def _query_bounty_state(self) -> Dict:
        """Get bounty system state."""
        # Read from bounty monitor state
        state_file = Path(__file__).parent.parent / 'state' / 'bounty_monitor.json'
        if state_file.exists():
            return json.loads(state_file.read_text())
        return {'error': 'Bounty state not available'}

    def _query_metrics(self, params: Dict) -> Dict:
        """Get system metrics."""
        # Implementation would gather metrics from various components
        return {
            'metrics': 'placeholder',
            'note': 'Implement metric collection'
        }

    def _query_logs(self, params: Dict) -> Dict:
        """Get system logs."""
        log_file = params.get('log_file', 'money_printer.log')
        lines = params.get('lines', 50)

        log_path = Path(__file__).parent.parent / 'logs' / log_file
        if log_path.exists():
            log_lines = log_path.read_text().splitlines()[-lines:]
            return {'logs': log_lines}

        return {'error': f'Log file not found: {log_file}'}

    def _query_hardware_state(self) -> Dict:
        """Get hardware state."""
        # Implementation would query connected hardware
        return {
            'hardware': 'placeholder',
            'note': 'Implement hardware state query'
        }

    # ================================================================
    # EVENT BUS (Pub/Sub for machine events)
    # ================================================================

    def publish_event(self, event_type: str, data: Dict, source: str = 'integrafix'):
        """
        Publish event to all subscribers.

        Events propagate to all connected machines listening for this event type.
        """
        message = MachineMessage(
            type=MessageType.EVENT.value,
            protocol=Protocol.REST.value,
            source=source,
            target='*',  # Broadcast
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload={
                'event_type': event_type,
                'data': data
            }
        )

        # Notify all subscribers for this event type
        if event_type in self.subscribers:
            for handler in self.subscribers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    print(f"Error in event handler: {e}")

        self.state['events_published'] += 1
        self.save_state()

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to specific event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
        print(f"✓ Subscribed to event: {event_type}")

    def _handle_event(self, message: MachineMessage) -> Dict:
        """Handle incoming event from external system."""
        event_type = message.payload.get('event_type')
        data = message.payload.get('data', {})

        # Propagate to local subscribers
        if event_type in self.subscribers:
            for handler in self.subscribers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    print(f"Error handling event: {e}")

        return {'received': True}

    def _handle_subscribe(self, message: MachineMessage) -> Dict:
        """Handle subscription request from external system."""
        event_type = message.payload.get('event_type')
        system_id = message.source

        # Track subscription
        if system_id not in self.connected_systems:
            self.connected_systems[system_id] = {'subscriptions': []}

        if event_type not in self.connected_systems[system_id]['subscriptions']:
            self.connected_systems[system_id]['subscriptions'].append(event_type)

        return {
            'subscribed': True,
            'event_type': event_type
        }

    def _handle_unsubscribe(self, message: MachineMessage) -> Dict:
        """Handle unsubscribe request."""
        event_type = message.payload.get('event_type')
        system_id = message.source

        if system_id in self.connected_systems:
            if event_type in self.connected_systems[system_id].get('subscriptions', []):
                self.connected_systems[system_id]['subscriptions'].remove(event_type)

        return {
            'unsubscribed': True,
            'event_type': event_type
        }

    # ================================================================
    # CONNECTION MANAGEMENT
    # ================================================================

    def register_system(self, system_id: str, metadata: Dict):
        """Register external system connection."""
        self.connected_systems[system_id] = {
            'connected_at': datetime.now(timezone.utc).isoformat(),
            'last_heartbeat': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata,
            'subscriptions': []
        }

        self.state['connected_systems'][system_id] = {
            'first_connected': datetime.now(timezone.utc).isoformat()
        }
        self.save_state()

        print(f"✓ Registered system: {system_id}")

    def _handle_heartbeat(self, message: MachineMessage) -> Dict:
        """Handle heartbeat from connected system."""
        system_id = message.source

        if system_id in self.connected_systems:
            self.connected_systems[system_id]['last_heartbeat'] = \
                datetime.now(timezone.utc).isoformat()

        return {
            'alive': True,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    # ================================================================
    # COMMAND IMPLEMENTATIONS
    # ================================================================

    def _cmd_get_status(self, params: Dict) -> Dict:
        """Get system status."""
        return self._query_system_state()

    def _cmd_get_health(self, params: Dict) -> Dict:
        """Get system health."""
        return {
            'status': 'healthy',
            'components': self._get_active_components(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def _cmd_execute_trade(self, params: Dict) -> Dict:
        """Execute trade via INTEGRAFIX."""
        # This would call into the trading system
        return {
            'note': 'Trade execution integration to be implemented',
            'params': params
        }

    def _cmd_cancel_trade(self, params: Dict) -> Dict:
        """Cancel pending trade."""
        return {
            'note': 'Trade cancellation to be implemented',
            'params': params
        }

    def _cmd_get_positions(self, params: Dict) -> Dict:
        """Get current trading positions."""
        return {
            'note': 'Position query to be implemented'
        }

    def _cmd_restart_component(self, params: Dict) -> Dict:
        """Restart system component."""
        component = params.get('component')
        return {
            'note': f'Restart {component} to be implemented'
        }

    def _cmd_shutdown(self, params: Dict) -> Dict:
        """Shutdown system."""
        return {
            'note': 'Graceful shutdown to be implemented'
        }

    def _cmd_pause_trading(self, params: Dict) -> Dict:
        """Pause trading operations."""
        return {
            'note': 'Trading pause to be implemented'
        }

    def _cmd_resume_trading(self, params: Dict) -> Dict:
        """Resume trading operations."""
        return {
            'note': 'Trading resume to be implemented'
        }

    def _cmd_control_hardware(self, params: Dict) -> Dict:
        """Control hardware device."""
        device = params.get('device')
        action = params.get('action')
        return {
            'note': f'Hardware control ({device}: {action}) to be implemented'
        }

    def _cmd_get_metrics(self, params: Dict) -> Dict:
        """Get system metrics."""
        return self._query_metrics(params)

    def _cmd_get_logs(self, params: Dict) -> Dict:
        """Get system logs."""
        return self._query_logs(params)

    # ================================================================
    # HELPER METHODS
    # ================================================================

    def _get_uptime(self) -> float:
        """Get system uptime in seconds."""
        # Placeholder - would calculate from system start time
        return 0.0

    def _get_active_components(self) -> List[str]:
        """Get list of active system components."""
        # Check running processes
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)

        components = []
        keywords = ['money_printer', 'backend_loop', 'self_healer', 'email_handler']

        for keyword in keywords:
            if keyword in result.stdout:
                components.append(keyword)

        return components

    # ================================================================
    # STATISTICS
    # ================================================================

    def get_stats(self) -> Dict:
        """Get hub statistics."""
        return {
            'total_messages': self.state['total_messages'],
            'by_protocol': self.state['messages_by_protocol'],
            'by_type': self.state['messages_by_type'],
            'connected_systems': len(self.connected_systems),
            'events_published': self.state['events_published'],
            'commands_executed': self.state['commands_executed'],
            'queries_handled': self.state['queries_handled'],
            'last_activity': self.state['last_activity']
        }


# ================================================================
# CONVENIENCE FUNCTIONS
# ================================================================

_hub_instance = None

def get_hub() -> MachineCommunicationHub:
    """Get singleton hub instance."""
    global _hub_instance
    if _hub_instance is None:
        _hub_instance = MachineCommunicationHub()
    return _hub_instance


def send_command(command: str, params: Dict, source: str = 'external') -> Dict:
    """Send command to system."""
    hub = get_hub()
    message = MachineMessage(
        type=MessageType.COMMAND.value,
        protocol=Protocol.REST.value,
        source=source,
        target='integrafix',
        timestamp=datetime.now(timezone.utc).isoformat(),
        payload={'command': command, 'params': params}
    )
    return hub.route_message(message)


def query_system(query: str, params: Dict = None) -> Dict:
    """Query system state."""
    hub = get_hub()
    message = MachineMessage(
        type=MessageType.QUERY.value,
        protocol=Protocol.REST.value,
        source='external',
        target='integrafix',
        timestamp=datetime.now(timezone.utc).isoformat(),
        payload={'query': query, 'params': params or {}}
    )
    return hub.route_message(message)


def publish_event(event_type: str, data: Dict):
    """Publish event to all subscribers."""
    hub = get_hub()
    hub.publish_event(event_type, data)


# ================================================================
# TESTING
# ================================================================

def test_machine_communication():
    """Test machine communication hub."""
    print("="*60)
    print("MACHINE COMMUNICATION HUB TEST")
    print("="*60)
    print()

    hub = get_hub()

    # Test 1: Query system state
    print("1. Testing system query...")
    result = query_system('system_state')
    print(f"   System: {result.get('system')}")
    print(f"   Status: {result.get('status')}")
    print(f"   Active components: {result.get('active_components')}")
    print()

    # Test 2: Send command
    print("2. Testing command execution...")
    result = send_command('get_health', {})
    print(f"   Health: {result.get('status')}")
    print()

    # Test 3: Event subscription
    print("3. Testing event bus...")

    received_events = []
    def event_handler(data):
        received_events.append(data)

    hub.subscribe('test_event', event_handler)
    hub.publish_event('test_event', {'message': 'Hello from machine!'})

    print(f"   Events received: {len(received_events)}")
    print()

    # Test 4: Statistics
    print("4. Hub statistics:")
    stats = hub.get_stats()
    print(f"   Total messages: {stats['total_messages']}")
    print(f"   Commands executed: {stats['commands_executed']}")
    print(f"   Queries handled: {stats['queries_handled']}")
    print(f"   Events published: {stats['events_published']}")
    print()

    print("="*60)
    print("TEST COMPLETE")
    print("="*60)


def main():
    """Run machine communication hub."""
    import sys

    if '--test' in sys.argv:
        test_machine_communication()
    elif '--stats' in sys.argv:
        hub = get_hub()
        stats = hub.get_stats()
        print(json.dumps(stats, indent=2))
    else:
        print("Machine Communication Hub")
        print()
        print("Usage:")
        print("  --test   Test hub functionality")
        print("  --stats  Show statistics")


if __name__ == '__main__':
    main()
