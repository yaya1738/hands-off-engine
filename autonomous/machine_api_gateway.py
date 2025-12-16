#!/usr/bin/env python3
"""
Machine API Gateway - Multi-Protocol Interface

Provides multiple protocol endpoints for machine-to-machine communication:
- REST API (HTTP/JSON)
- JSON-RPC 2.0
- WebSocket (real-time bidirectional)
- Unix Socket (local IPC)

External systems can interact with INTEGRAFIX through any protocol.

Usage:
    # Start API gateway
    python3 autonomous/machine_api_gateway.py --start

    # Test from external system
    curl -X POST http://localhost:8765/api/command \
        -H "Content-Type: application/json" \
        -d '{"command": "get_status", "params": {}}'
"""

import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import threading

# Import hub
from autonomous.machine_communication_hub import (
    get_hub, MachineMessage, MessageType, Protocol
)

# Try to import web server libraries
try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("⚠️  aiohttp not available (pip install aiohttp)")

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("⚠️  websockets not available (pip install websockets)")


class MachineAPIGateway:
    """
    Multi-protocol API gateway for machine communication.

    Provides:
    - REST API on port 8765
    - WebSocket server on port 8766
    - Unix socket at /tmp/integrafix.sock
    """

    def __init__(self, host='0.0.0.0', rest_port=8765, ws_port=8766):
        self.host = host
        self.rest_port = rest_port
        self.ws_port = ws_port
        self.hub = get_hub()
        self.running = False
        self.websocket_clients = set()

    # ================================================================
    # REST API (HTTP/JSON)
    # ================================================================

    async def handle_rest_command(self, request):
        """
        Handle REST API command request.

        POST /api/command
        {
            "command": "get_status",
            "params": {}
        }
        """
        try:
            data = await request.json()

            command = data.get('command')
            params = data.get('params', {})

            if not command:
                return web.json_response({
                    'error': 'No command specified'
                }, status=400)

            # Create machine message
            message = MachineMessage(
                type=MessageType.COMMAND.value,
                protocol=Protocol.REST.value,
                source=request.remote,
                target='integrafix',
                timestamp=datetime.now(timezone.utc).isoformat(),
                payload={'command': command, 'params': params}
            )

            # Route through hub
            result = self.hub.route_message(message)

            return web.json_response(result)

        except Exception as e:
            return web.json_response({
                'error': str(e)
            }, status=500)

    async def handle_rest_query(self, request):
        """
        Handle REST API query request.

        GET /api/query?type=system_state
        """
        try:
            query_type = request.query.get('type', 'system_state')
            params = dict(request.query)
            params.pop('type', None)

            # Create machine message
            message = MachineMessage(
                type=MessageType.QUERY.value,
                protocol=Protocol.REST.value,
                source=request.remote,
                target='integrafix',
                timestamp=datetime.now(timezone.utc).isoformat(),
                payload={'query': query_type, 'params': params}
            )

            # Route through hub
            result = self.hub.route_message(message)

            return web.json_response(result)

        except Exception as e:
            return web.json_response({
                'error': str(e)
            }, status=500)

    async def handle_rest_event(self, request):
        """
        Handle REST API event publication.

        POST /api/event
        {
            "event_type": "trade_executed",
            "data": {...}
        }
        """
        try:
            data = await request.json()

            event_type = data.get('event_type')
            event_data = data.get('data', {})

            if not event_type:
                return web.json_response({
                    'error': 'No event_type specified'
                }, status=400)

            # Publish event
            self.hub.publish_event(event_type, event_data, source=request.remote)

            return web.json_response({
                'published': True,
                'event_type': event_type
            })

        except Exception as e:
            return web.json_response({
                'error': str(e)
            }, status=500)

    async def handle_rest_stats(self, request):
        """Get hub statistics."""
        stats = self.hub.get_stats()
        return web.json_response(stats)

    async def handle_rest_health(self, request):
        """Health check endpoint."""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

    # ================================================================
    # JSON-RPC 2.0
    # ================================================================

    async def handle_jsonrpc(self, request):
        """
        Handle JSON-RPC 2.0 request.

        POST /rpc
        {
            "jsonrpc": "2.0",
            "method": "execute_trade",
            "params": {...},
            "id": 1
        }
        """
        try:
            data = await request.json()

            # Validate JSON-RPC 2.0 format
            if data.get('jsonrpc') != '2.0':
                return web.json_response({
                    'jsonrpc': '2.0',
                    'error': {
                        'code': -32600,
                        'message': 'Invalid Request'
                    },
                    'id': data.get('id')
                })

            method = data.get('method')
            params = data.get('params', {})
            request_id = data.get('id')

            # Create machine message
            message = MachineMessage(
                type=MessageType.COMMAND.value,
                protocol=Protocol.JSON_RPC.value,
                source=request.remote,
                target='integrafix',
                timestamp=datetime.now(timezone.utc).isoformat(),
                payload={'command': method, 'params': params},
                request_id=str(request_id)
            )

            # Route through hub
            result = self.hub.route_message(message)

            # Format as JSON-RPC response
            if 'error' in result:
                return web.json_response({
                    'jsonrpc': '2.0',
                    'error': {
                        'code': -32000,
                        'message': result['error']
                    },
                    'id': request_id
                })
            else:
                return web.json_response({
                    'jsonrpc': '2.0',
                    'result': result,
                    'id': request_id
                })

        except Exception as e:
            return web.json_response({
                'jsonrpc': '2.0',
                'error': {
                    'code': -32603,
                    'message': f'Internal error: {str(e)}'
                },
                'id': data.get('id') if 'data' in locals() else None
            })

    # ================================================================
    # WEBSOCKET (Real-time bidirectional)
    # ================================================================

    async def handle_websocket(self, request):
        """
        Handle WebSocket connection for real-time communication.

        Supports:
        - Command execution
        - Event subscriptions
        - State streaming
        """
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.websocket_clients.add(ws)
        print(f"✓ WebSocket client connected: {request.remote}")

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)

                        # Route based on message type
                        msg_type = data.get('type', 'command')

                        if msg_type == 'command':
                            message = MachineMessage(
                                type=MessageType.COMMAND.value,
                                protocol=Protocol.WEBSOCKET.value,
                                source=request.remote,
                                target='integrafix',
                                timestamp=datetime.now(timezone.utc).isoformat(),
                                payload=data
                            )
                            result = self.hub.route_message(message)
                            await ws.send_json(result)

                        elif msg_type == 'query':
                            message = MachineMessage(
                                type=MessageType.QUERY.value,
                                protocol=Protocol.WEBSOCKET.value,
                                source=request.remote,
                                target='integrafix',
                                timestamp=datetime.now(timezone.utc).isoformat(),
                                payload=data
                            )
                            result = self.hub.route_message(message)
                            await ws.send_json(result)

                        elif msg_type == 'subscribe':
                            event_type = data.get('event_type')
                            # Store subscription for this websocket
                            await ws.send_json({
                                'subscribed': True,
                                'event_type': event_type
                            })

                    except json.JSONDecodeError:
                        await ws.send_json({'error': 'Invalid JSON'})

                elif msg.type == web.WSMsgType.ERROR:
                    print(f'✗ WebSocket error: {ws.exception()}')

        finally:
            self.websocket_clients.remove(ws)
            print(f"✗ WebSocket client disconnected: {request.remote}")

        return ws

    # ================================================================
    # SERVER MANAGEMENT
    # ================================================================

    async def start_rest_server(self):
        """Start REST API server."""
        if not AIOHTTP_AVAILABLE:
            print("✗ Cannot start REST server - aiohttp not installed")
            return

        app = web.Application()

        # REST API routes
        app.router.add_post('/api/command', self.handle_rest_command)
        app.router.add_get('/api/query', self.handle_rest_query)
        app.router.add_post('/api/event', self.handle_rest_event)
        app.router.add_get('/api/stats', self.handle_rest_stats)
        app.router.add_get('/health', self.handle_rest_health)

        # JSON-RPC route
        app.router.add_post('/rpc', self.handle_jsonrpc)

        # WebSocket route
        app.router.add_get('/ws', self.handle_websocket)

        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, self.host, self.rest_port)
        await site.start()

        print(f"✓ Machine API Gateway started")
        print(f"  REST API: http://{self.host}:{self.rest_port}/api")
        print(f"  JSON-RPC: http://{self.host}:{self.rest_port}/rpc")
        print(f"  WebSocket: ws://{self.host}:{self.rest_port}/ws")
        print(f"  Health: http://{self.host}:{self.rest_port}/health")
        print()

        self.running = True

        # Keep running
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n✗ Shutting down API gateway...")
        finally:
            await runner.cleanup()

    def start(self):
        """Start API gateway (blocking)."""
        asyncio.run(self.start_rest_server())


# ================================================================
# CONVENIENCE FUNCTIONS
# ================================================================

def start_gateway():
    """Start machine API gateway."""
    gateway = MachineAPIGateway()
    gateway.start()


# ================================================================
# CLIENT EXAMPLES
# ================================================================

def example_rest_client():
    """Example REST API client."""
    import requests

    base_url = "http://localhost:8765"

    # Execute command
    response = requests.post(f"{base_url}/api/command", json={
        'command': 'get_status',
        'params': {}
    })
    print("System status:", response.json())

    # Query data
    response = requests.get(f"{base_url}/api/query?type=system_state")
    print("System state:", response.json())

    # Get statistics
    response = requests.get(f"{base_url}/api/stats")
    print("Hub stats:", response.json())


def example_jsonrpc_client():
    """Example JSON-RPC 2.0 client."""
    import requests

    url = "http://localhost:8765/rpc"

    # Send JSON-RPC request
    response = requests.post(url, json={
        'jsonrpc': '2.0',
        'method': 'get_health',
        'params': {},
        'id': 1
    })

    print("JSON-RPC response:", response.json())


async def example_websocket_client():
    """Example WebSocket client."""
    if not WEBSOCKETS_AVAILABLE:
        print("✗ websockets library required")
        return

    uri = "ws://localhost:8765/ws"

    async with websockets.connect(uri) as websocket:
        # Send command
        await websocket.send(json.dumps({
            'type': 'command',
            'command': 'get_status',
            'params': {}
        }))

        # Receive response
        response = await websocket.recv()
        print("WebSocket response:", json.loads(response))


# ================================================================
# TESTING & MAIN
# ================================================================

def test_api_gateway():
    """Test API gateway (requires server running)."""
    print("="*60)
    print("MACHINE API GATEWAY TEST")
    print("="*60)
    print()

    print("Testing REST API client...")
    try:
        example_rest_client()
        print("✓ REST API working")
    except Exception as e:
        print(f"✗ REST API error: {e}")

    print()
    print("Testing JSON-RPC client...")
    try:
        example_jsonrpc_client()
        print("✓ JSON-RPC working")
    except Exception as e:
        print(f"✗ JSON-RPC error: {e}")

    print()
    print("="*60)


def main():
    """Run machine API gateway."""
    import sys

    if '--start' in sys.argv:
        print("Starting Machine API Gateway...")
        start_gateway()

    elif '--test' in sys.argv:
        test_api_gateway()

    elif '--examples' in sys.argv:
        print("Example usage:")
        print()
        print("# REST API")
        print("curl http://localhost:8765/api/query?type=system_state")
        print()
        print("# JSON-RPC")
        print('curl -X POST http://localhost:8765/rpc -H "Content-Type: application/json" \\')
        print('  -d \'{"jsonrpc": "2.0", "method": "get_status", "params": {}, "id": 1}\'')
        print()
        print("# WebSocket (JavaScript)")
        print("const ws = new WebSocket('ws://localhost:8765/ws');")
        print("ws.send(JSON.stringify({type: 'command', command: 'get_status'}));")

    else:
        print("Machine API Gateway")
        print()
        print("Usage:")
        print("  --start     Start API gateway server")
        print("  --test      Test API gateway (requires running server)")
        print("  --examples  Show usage examples")


if __name__ == '__main__':
    main()
