#!/usr/bin/env python3
"""
INTEGRAFIX: Distributed Trading Integration
============================================

Enables local trading implementation to use remote trading components
via the distributed M2M infrastructure.

CAPABILITIES:
- Service discovery & registration
- Remote trade execution
- Real-time trade data streaming
- Automatic failover & load balancing
- Transparent local/remote operation

ARCHITECTURE:
    Local Trading Code
            ↓
    Distributed Trading Proxy (this file)
            ↓
    ┌───────────────────────────┐
    │ Local Executor (if avail) │
    │ Remote Executor 1          │
    │ Remote Executor 2          │
    │ Remote Executor N          │
    └───────────────────────────┘
            ↓
    Polymarket / Live Trading

Serving: Yair Siegel
"""

import json
import os
import sys
import asyncio
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import distributed M2M components
try:
    from autonomous.machine_distributed_coordinator import (
        get_coordinator,
        ServiceInstance,
        LoadBalanceStrategy
    )
    COORDINATOR_AVAILABLE = True
except ImportError:
    COORDINATOR_AVAILABLE = False
    logging.warning("Distributed coordinator not available")

try:
    from autonomous.machine_stream_processor import get_processor, StreamRecord
    STREAM_PROCESSOR_AVAILABLE = True
except ImportError:
    STREAM_PROCESSOR_AVAILABLE = False
    logging.warning("Stream processor not available")

try:
    from autonomous.machine_communication_hub import get_hub, MachineMessage, MessageType
    from autonomous.machine_api_gateway import Protocol
    HUB_AVAILABLE = True
except ImportError:
    HUB_AVAILABLE = False
    logging.warning("M2M communication hub not available")

try:
    from autonomous.machine_security import get_security, Permission
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

# Import local trading components
try:
    from autonomous.trade_executor import TradeExecutor
    LOCAL_EXECUTOR_AVAILABLE = True
except ImportError:
    LOCAL_EXECUTOR_AVAILABLE = False

try:
    from executor.polymarket_orders import PolymarketOrders
    POLYMARKET_ORDERS_AVAILABLE = True
except ImportError:
    POLYMARKET_ORDERS_AVAILABLE = False


class ExecutionMode(Enum):
    """Where to execute trade."""
    LOCAL_ONLY = "local_only"           # Only use local executor
    REMOTE_ONLY = "remote_only"         # Only use remote executors
    LOCAL_FIRST = "local_first"         # Try local first, fallback to remote
    REMOTE_FIRST = "remote_first"       # Try remote first, fallback to local
    LOAD_BALANCED = "load_balanced"     # Distribute across all available
    REDUNDANT = "redundant"             # Execute on both for reliability


class TradeOperation(Enum):
    """Supported trading operations."""
    GET_MARKET_DATA = "get_market_data"
    EXECUTE_TRADE = "execute_trade"
    GET_POSITIONS = "get_positions"
    GET_BALANCE = "get_balance"
    LIMIT_BUY_YES = "limit_buy_yes"
    LIMIT_SELL_YES = "limit_sell_yes"
    LIMIT_BUY_NO = "limit_buy_no"
    LIMIT_SELL_NO = "limit_sell_no"
    MARKET_BUY_YES = "market_buy_yes"
    MARKET_SELL_YES = "market_sell_yes"
    MARKET_BUY_NO = "market_buy_no"
    MARKET_SELL_NO = "market_sell_no"
    CANCEL_ORDER = "cancel_order"
    GET_ORDER_STATUS = "get_order_status"


@dataclass
class TradingServiceInfo:
    """Information about a trading service (local or remote)."""
    service_id: str
    address: str
    port: int
    is_local: bool
    capabilities: List[str]
    load: float  # 0.0 to 1.0
    health: str  # "healthy", "degraded", "unhealthy"
    last_trade_time: Optional[str]
    total_trades: int
    success_rate: float
    avg_latency_ms: float


@dataclass
class TradeRequest:
    """Request for trade execution."""
    operation: str
    params: Dict[str, Any]
    mode: str = ExecutionMode.LOCAL_FIRST.value
    priority: str = "normal"
    idempotency_key: Optional[str] = None
    timeout_seconds: int = 30


@dataclass
class TradeResult:
    """Result of trade execution."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    executed_on: str = "unknown"  # "local" or service_id
    latency_ms: float = 0.0
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class DistributedTradingProxy:
    """
    Proxy for distributed trading operations.

    Transparently routes trading operations to local or remote executors
    based on availability, load, and configuration.
    """

    def __init__(
        self,
        node_id: str = None,
        enable_local: bool = True,
        enable_remote: bool = True,
        default_mode: ExecutionMode = ExecutionMode.LOCAL_FIRST
    ):
        self.node_id = node_id or self._get_node_id()
        self.enable_local = enable_local
        self.enable_remote = enable_remote
        self.default_mode = default_mode

        # Initialize components
        self.coordinator = get_coordinator() if COORDINATOR_AVAILABLE else None
        self.stream_processor = get_processor() if STREAM_PROCESSOR_AVAILABLE else None
        self.hub = get_hub() if HUB_AVAILABLE else None
        self.security = get_security() if SECURITY_AVAILABLE else None

        # Local trading components
        self.local_executor = None
        self.local_orders = None
        if enable_local:
            if LOCAL_EXECUTOR_AVAILABLE:
                self.local_executor = TradeExecutor()
            if POLYMARKET_ORDERS_AVAILABLE:
                self.local_orders = PolymarketOrders()

        # State
        self.registered_services: Dict[str, TradingServiceInfo] = {}
        self.trade_history: List[Dict] = []
        self.stats = {
            'total_requests': 0,
            'local_executions': 0,
            'remote_executions': 0,
            'failures': 0,
            'avg_latency_ms': 0.0
        }

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Initialize streams for trade data
        if self.stream_processor:
            self._setup_trade_streams()

    def _get_node_id(self) -> str:
        """Generate unique node ID."""
        import socket
        hostname = socket.gethostname()
        return f"trading-node-{hostname}-{os.getpid()}"

    def _setup_trade_streams(self):
        """Setup real-time trade data streams."""
        if not self.stream_processor:
            return

        # Create streams for different trade data
        # Note: create_stream only takes name and max_size
        self.stream_processor.create_stream('trades', max_size=10000)
        self.stream_processor.create_stream('market_data', max_size=10000)
        self.stream_processor.create_stream('positions', max_size=10000)

    # ==================== SERVICE REGISTRATION ====================

    def register_local_trading_service(
        self,
        port: int = 8080,
        capabilities: List[str] = None
    ) -> str:
        """
        Register this node as a trading service.

        Makes local trading capabilities discoverable by other nodes.
        """
        if not self.coordinator:
            raise RuntimeError("Coordinator not available")

        if capabilities is None:
            capabilities = [
                'execute_trade',
                'get_market_data',
                'get_positions',
                'polymarket_orders'
            ]

        # Register service
        service_id = self.coordinator.register_service(
            name='trading-executor',
            address=self._get_local_ip(),
            port=port,
            metadata={
                'node_id': self.node_id,
                'capabilities': capabilities,
                'executor_available': LOCAL_EXECUTOR_AVAILABLE,
                'orders_available': POLYMARKET_ORDERS_AVAILABLE,
                'version': '1.0.0'
            },
            tags=['trading', 'polymarket', 'executor']
        )

        self.logger.info(f"Registered trading service: {service_id}")

        # Start health check heartbeat
        asyncio.create_task(self._heartbeat_loop(service_id))

        return service_id

    def _get_local_ip(self) -> str:
        """Get local IP address."""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    async def _heartbeat_loop(self, service_id: str):
        """Send periodic heartbeats to coordinator."""
        while True:
            try:
                if self.coordinator:
                    self.coordinator.heartbeat(service_id)
                await asyncio.sleep(10)  # Heartbeat every 10 seconds
            except Exception as e:
                self.logger.error(f"Heartbeat failed: {e}")

    def discover_trading_services(self) -> List[TradingServiceInfo]:
        """
        Discover all available trading services (local + remote).

        Returns list of services sorted by health and load.
        """
        if not self.coordinator:
            # No coordinator, only return local if available
            if self.enable_local and self.local_executor:
                return [TradingServiceInfo(
                    service_id='local',
                    address='127.0.0.1',
                    port=0,
                    is_local=True,
                    capabilities=['all'],
                    load=0.0,
                    health='healthy',
                    last_trade_time=None,
                    total_trades=0,
                    success_rate=1.0,
                    avg_latency_ms=0.0
                )]
            return []

        # Discover services via coordinator
        services = self.coordinator.discover_service('trading-executor')

        result = []
        for svc in services:
            info = TradingServiceInfo(
                service_id=svc.id,
                address=svc.address,
                port=svc.port,
                is_local=(svc.metadata.get('node_id') == self.node_id),
                capabilities=svc.metadata.get('capabilities', []),
                load=0.0,  # TODO: Get actual load
                health=svc.health,
                last_trade_time=svc.metadata.get('last_trade_time'),
                total_trades=svc.metadata.get('total_trades', 0),
                success_rate=svc.metadata.get('success_rate', 1.0),
                avg_latency_ms=svc.metadata.get('avg_latency_ms', 0.0)
            )
            result.append(info)
            self.registered_services[svc.id] = info

        # Add local executor if available and not already registered
        if self.enable_local and self.local_executor:
            if not any(s.is_local for s in result):
                result.append(TradingServiceInfo(
                    service_id='local',
                    address='127.0.0.1',
                    port=0,
                    is_local=True,
                    capabilities=['all'],
                    load=0.0,
                    health='healthy',
                    last_trade_time=None,
                    total_trades=0,
                    success_rate=1.0,
                    avg_latency_ms=0.0
                ))

        # Sort by health and load
        result.sort(key=lambda s: (
            0 if s.health == 'healthy' else 1 if s.health == 'degraded' else 2,
            s.load
        ))

        return result

    # ==================== TRADE EXECUTION ====================

    def execute_trade(
        self,
        operation: str,
        params: Dict[str, Any],
        mode: ExecutionMode = None
    ) -> TradeResult:
        """
        Execute trade operation (local or remote).

        Args:
            operation: TradeOperation enum value or string
            params: Operation parameters
            mode: Execution mode (LOCAL_ONLY, REMOTE_ONLY, etc.)

        Returns:
            TradeResult with execution details
        """
        start_time = datetime.now(timezone.utc)
        mode = mode or self.default_mode

        self.stats['total_requests'] += 1

        request = TradeRequest(
            operation=operation,
            params=params,
            mode=mode.value if isinstance(mode, ExecutionMode) else mode
        )

        try:
            # Route based on execution mode
            if mode == ExecutionMode.LOCAL_ONLY:
                result = self._execute_local(request)
            elif mode == ExecutionMode.REMOTE_ONLY:
                result = self._execute_remote(request)
            elif mode == ExecutionMode.LOCAL_FIRST:
                result = self._execute_local_first(request)
            elif mode == ExecutionMode.REMOTE_FIRST:
                result = self._execute_remote_first(request)
            elif mode == ExecutionMode.LOAD_BALANCED:
                result = self._execute_load_balanced(request)
            elif mode == ExecutionMode.REDUNDANT:
                result = self._execute_redundant(request)
            else:
                result = TradeResult(
                    success=False,
                    error=f"Unknown execution mode: {mode}"
                )

            # Calculate latency
            end_time = datetime.now(timezone.utc)
            result.latency_ms = (end_time - start_time).total_seconds() * 1000

            # Update stats
            if result.success:
                if result.executed_on == 'local':
                    self.stats['local_executions'] += 1
                else:
                    self.stats['remote_executions'] += 1
            else:
                self.stats['failures'] += 1

            # Update average latency
            total = self.stats['total_requests']
            self.stats['avg_latency_ms'] = (
                (self.stats['avg_latency_ms'] * (total - 1) + result.latency_ms) / total
            )

            # Publish to trade stream
            if result.success and self.stream_processor:
                self._publish_trade_to_stream(request, result)

            # Log trade
            self.trade_history.append({
                'timestamp': result.timestamp,
                'operation': operation,
                'params': params,
                'result': asdict(result)
            })

            return result

        except Exception as e:
            self.logger.error(f"Trade execution failed: {e}")
            self.stats['failures'] += 1
            return TradeResult(
                success=False,
                error=str(e)
            )

    def _execute_local(self, request: TradeRequest) -> TradeResult:
        """Execute trade on local executor."""
        if not self.local_executor and not self.local_orders:
            return TradeResult(
                success=False,
                error="Local executor not available"
            )

        try:
            operation = request.operation
            params = request.params

            # Route to appropriate handler
            if operation == TradeOperation.GET_MARKET_DATA.value:
                data = self.local_executor.get_market_data(
                    limit=params.get('limit', 20)
                )
                return TradeResult(
                    success=True,
                    data={'markets': data},
                    executed_on='local'
                )

            elif operation.startswith('limit_') or operation.startswith('market_'):
                # Order execution via polymarket_orders
                if not self.local_orders:
                    return TradeResult(
                        success=False,
                        error="Polymarket orders not available"
                    )

                method = getattr(self.local_orders, operation, None)
                if not method:
                    return TradeResult(
                        success=False,
                        error=f"Unknown order operation: {operation}"
                    )

                result = method(**params)
                return TradeResult(
                    success=True,
                    data=result,
                    executed_on='local'
                )

            elif operation == TradeOperation.EXECUTE_TRADE.value:
                # Generic trade execution via trade_executor
                # This would call the appropriate method based on params
                market = params.get('market')
                direction = params.get('direction')
                size = params.get('size')
                price = params.get('price')

                # Route to appropriate order type
                if direction == 'YES' and price:
                    result = self.local_orders.limit_buy_yes(market, price, size)
                elif direction == 'NO' and price:
                    result = self.local_orders.limit_buy_no(market, price, size)
                elif direction == 'YES':
                    result = self.local_orders.market_buy_yes(market, size)
                elif direction == 'NO':
                    result = self.local_orders.market_buy_no(market, size)
                else:
                    return TradeResult(
                        success=False,
                        error=f"Invalid direction: {direction}"
                    )

                return TradeResult(
                    success=True,
                    data=result,
                    executed_on='local'
                )

            else:
                return TradeResult(
                    success=False,
                    error=f"Unknown operation: {operation}"
                )

        except Exception as e:
            return TradeResult(
                success=False,
                error=str(e),
                executed_on='local'
            )

    def _execute_remote(
        self,
        request: TradeRequest,
        service: TradingServiceInfo = None
    ) -> TradeResult:
        """Execute trade on remote executor."""
        if not self.enable_remote:
            return TradeResult(
                success=False,
                error="Remote execution disabled"
            )

        # Discover services if not provided
        if service is None:
            services = self.discover_trading_services()
            remote_services = [s for s in services if not s.is_local]
            if not remote_services:
                return TradeResult(
                    success=False,
                    error="No remote services available"
                )
            service = remote_services[0]

        try:
            # Send request via M2M hub
            if self.hub:
                message = MachineMessage(
                    type=MessageType.COMMAND.value,
                    protocol=Protocol.REST.value,
                    source=self.node_id,
                    target=service.service_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    payload={
                        'command': 'execute_trade',
                        'params': {
                            'operation': request.operation,
                            'params': request.params
                        }
                    }
                )
                result = self.hub.route_message(message)

                if result and result.get('success'):
                    return TradeResult(
                        success=True,
                        data=result.get('data'),
                        executed_on=service.service_id
                    )
                else:
                    return TradeResult(
                        success=False,
                        error=result.get('error', 'Remote execution failed'),
                        executed_on=service.service_id
                    )

            # Fallback to direct HTTP if hub not available
            url = f"http://{service.address}:{service.port}/api/trade"
            response = requests.post(
                url,
                json={
                    'operation': request.operation,
                    'params': request.params
                },
                timeout=request.timeout_seconds
            )

            if response.status_code == 200:
                data = response.json()
                return TradeResult(
                    success=True,
                    data=data,
                    executed_on=service.service_id
                )
            else:
                return TradeResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    executed_on=service.service_id
                )

        except Exception as e:
            return TradeResult(
                success=False,
                error=str(e),
                executed_on=service.service_id if service else 'unknown'
            )

    def _execute_local_first(self, request: TradeRequest) -> TradeResult:
        """Try local first, fallback to remote."""
        # Try local
        if self.enable_local and (self.local_executor or self.local_orders):
            result = self._execute_local(request)
            if result.success:
                return result
            self.logger.warning(f"Local execution failed: {result.error}, trying remote")

        # Fallback to remote
        return self._execute_remote(request)

    def _execute_remote_first(self, request: TradeRequest) -> TradeResult:
        """Try remote first, fallback to local."""
        # Try remote
        if self.enable_remote:
            result = self._execute_remote(request)
            if result.success:
                return result
            self.logger.warning(f"Remote execution failed: {result.error}, trying local")

        # Fallback to local
        return self._execute_local(request)

    def _execute_load_balanced(self, request: TradeRequest) -> TradeResult:
        """Distribute request across available services."""
        services = self.discover_trading_services()
        if not services:
            return TradeResult(
                success=False,
                error="No services available"
            )

        # Use coordinator's load balancer if available
        if self.coordinator:
            service_id = self.coordinator.select_service(
                'trading-executor',
                strategy=LoadBalanceStrategy.LEAST_CONNECTIONS
            )
            if service_id:
                service = self.registered_services.get(service_id)
                if service:
                    if service.is_local:
                        return self._execute_local(request)
                    else:
                        return self._execute_remote(request, service)

        # Fallback to simple round-robin
        service = services[self.stats['total_requests'] % len(services)]
        if service.is_local:
            return self._execute_local(request)
        else:
            return self._execute_remote(request, service)

    def _execute_redundant(self, request: TradeRequest) -> TradeResult:
        """Execute on both local and remote for reliability."""
        local_result = None
        remote_result = None

        # Execute local
        if self.enable_local and (self.local_executor or self.local_orders):
            local_result = self._execute_local(request)

        # Execute remote
        if self.enable_remote:
            remote_result = self._execute_remote(request)

        # Return first successful result
        if local_result and local_result.success:
            return local_result
        if remote_result and remote_result.success:
            return remote_result

        # Both failed
        return TradeResult(
            success=False,
            error=f"Local: {local_result.error if local_result else 'N/A'}, "
                  f"Remote: {remote_result.error if remote_result else 'N/A'}"
        )

    def _publish_trade_to_stream(self, request: TradeRequest, result: TradeResult):
        """Publish trade execution to stream for real-time sync."""
        if not self.stream_processor:
            return

        try:
            # publish(stream_name, key, value, metadata)
            self.stream_processor.publish(
                'trades',
                key=f"{self.node_id}:{result.timestamp}",
                value={
                    'operation': request.operation,
                    'params': request.params,
                    'success': result.success,
                    'executed_on': result.executed_on,
                    'latency_ms': result.latency_ms,
                    'node_id': self.node_id,
                    'timestamp': result.timestamp
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to publish trade to stream: {e}")

    # ==================== CONVENIENCE METHODS ====================

    def get_market_data(self, limit: int = 20, mode: ExecutionMode = None) -> TradeResult:
        """Get market data (convenience method)."""
        return self.execute_trade(
            TradeOperation.GET_MARKET_DATA.value,
            {'limit': limit},
            mode
        )

    def limit_buy_yes(
        self,
        market: str,
        price: float,
        size: float,
        mode: ExecutionMode = None
    ) -> TradeResult:
        """Place limit buy order for YES token (convenience method)."""
        return self.execute_trade(
            TradeOperation.LIMIT_BUY_YES.value,
            {'market': market, 'price': price, 'size': size},
            mode
        )

    def limit_buy_no(
        self,
        market: str,
        price: float,
        size: float,
        mode: ExecutionMode = None
    ) -> TradeResult:
        """Place limit buy order for NO token (convenience method)."""
        return self.execute_trade(
            TradeOperation.LIMIT_BUY_NO.value,
            {'market': market, 'price': price, 'size': size},
            mode
        )

    def market_buy_yes(
        self,
        market: str,
        size: float,
        mode: ExecutionMode = None
    ) -> TradeResult:
        """Place market buy order for YES token (convenience method)."""
        return self.execute_trade(
            TradeOperation.MARKET_BUY_YES.value,
            {'market': market, 'size': size},
            mode
        )

    def market_buy_no(
        self,
        market: str,
        size: float,
        mode: ExecutionMode = None
    ) -> TradeResult:
        """Place market buy order for NO token (convenience method)."""
        return self.execute_trade(
            TradeOperation.MARKET_BUY_NO.value,
            {'market': market, 'size': size},
            mode
        )

    # ==================== MONITORING ====================

    def get_stats(self) -> Dict:
        """Get execution statistics."""
        return {
            **self.stats,
            'available_services': len(self.discover_trading_services()),
            'local_available': self.enable_local and bool(self.local_executor or self.local_orders),
            'remote_available': self.enable_remote,
            'success_rate': (
                (self.stats['local_executions'] + self.stats['remote_executions'])
                / max(1, self.stats['total_requests'])
            )
        }

    def get_service_status(self) -> List[Dict]:
        """Get status of all trading services."""
        services = self.discover_trading_services()
        return [
            {
                'service_id': s.service_id,
                'address': f"{s.address}:{s.port}",
                'is_local': s.is_local,
                'health': s.health,
                'load': s.load,
                'capabilities': s.capabilities,
                'total_trades': s.total_trades,
                'success_rate': s.success_rate,
                'avg_latency_ms': s.avg_latency_ms
            }
            for s in services
        ]

    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """Get recent trade history."""
        return self.trade_history[-limit:]


# ==================== GLOBAL INSTANCE ====================

_distributed_trading = None

def get_distributed_trading(
    node_id: str = None,
    enable_local: bool = True,
    enable_remote: bool = True,
    default_mode: ExecutionMode = ExecutionMode.LOCAL_FIRST
) -> DistributedTradingProxy:
    """Get or create global distributed trading proxy."""
    global _distributed_trading
    if _distributed_trading is None:
        _distributed_trading = DistributedTradingProxy(
            node_id=node_id,
            enable_local=enable_local,
            enable_remote=enable_remote,
            default_mode=default_mode
        )
    return _distributed_trading


# ==================== CLI ====================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='INTEGRAFIX Distributed Trading Integration'
    )
    parser.add_argument(
        '--register',
        action='store_true',
        help='Register this node as a trading service'
    )
    parser.add_argument(
        '--discover',
        action='store_true',
        help='Discover available trading services'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show execution statistics'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run test trade execution'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Port for trading service (default: 8080)'
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create proxy
    proxy = get_distributed_trading()

    if args.register:
        print("🔧 Registering local trading service...")
        service_id = proxy.register_local_trading_service(port=args.port)
        print(f"✅ Registered: {service_id}")
        print(f"   Address: {proxy._get_local_ip()}:{args.port}")
        print(f"   Node ID: {proxy.node_id}")

    if args.discover:
        print("\n🔍 Discovering trading services...")
        services = proxy.discover_trading_services()
        print(f"\n✅ Found {len(services)} service(s):")
        for svc in services:
            print(f"\n   Service: {svc.service_id}")
            print(f"   Address: {svc.address}:{svc.port}")
            print(f"   Local: {svc.is_local}")
            print(f"   Health: {svc.health}")
            print(f"   Capabilities: {', '.join(svc.capabilities)}")
            print(f"   Total Trades: {svc.total_trades}")
            print(f"   Success Rate: {svc.success_rate:.1%}")

    if args.stats:
        print("\n📊 Execution Statistics:")
        stats = proxy.get_stats()
        print(json.dumps(stats, indent=2))

    if args.test:
        print("\n🧪 Running test trade execution...")

        # Test 1: Get market data (local first)
        print("\n1. Get market data (LOCAL_FIRST):")
        result = proxy.get_market_data(limit=5, mode=ExecutionMode.LOCAL_FIRST)
        print(f"   Success: {result.success}")
        print(f"   Executed on: {result.executed_on}")
        print(f"   Latency: {result.latency_ms:.2f}ms")
        if result.data:
            print(f"   Markets: {len(result.data.get('markets', []))}")

        # Test 2: Get market data (remote only)
        print("\n2. Get market data (REMOTE_ONLY):")
        result = proxy.get_market_data(limit=5, mode=ExecutionMode.REMOTE_ONLY)
        print(f"   Success: {result.success}")
        print(f"   Executed on: {result.executed_on}")
        print(f"   Latency: {result.latency_ms:.2f}ms")
        if not result.success:
            print(f"   Error: {result.error}")

        # Test 3: Load balanced execution
        print("\n3. Get market data (LOAD_BALANCED):")
        result = proxy.get_market_data(limit=5, mode=ExecutionMode.LOAD_BALANCED)
        print(f"   Success: {result.success}")
        print(f"   Executed on: {result.executed_on}")
        print(f"   Latency: {result.latency_ms:.2f}ms")

        # Show final stats
        print("\n📊 Final Statistics:")
        stats = proxy.get_stats()
        print(f"   Total Requests: {stats['total_requests']}")
        print(f"   Local Executions: {stats['local_executions']}")
        print(f"   Remote Executions: {stats['remote_executions']}")
        print(f"   Failures: {stats['failures']}")
        print(f"   Success Rate: {stats['success_rate']:.1%}")
        print(f"   Avg Latency: {stats['avg_latency_ms']:.2f}ms")

        print("\n✅ Test complete")
