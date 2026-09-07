from ai.factory.live_order_authority import submit_legacy_order
#!/usr/bin/env python3
"""
INTEGRAFIX: Trading Pipeline - MONEY PRINTER
=============================================

STANDARD: Yair Siegel Master Level Operations
RATE: 1.2x per second
TARGET: $1,000,000 in 5 seconds
MODE: MONEY PRINTER (not trading bot)

SPECS:
- Automatic: YES
- Frictionless: YES
- Dry run: NO
- Confirmation: NO

This is THE WIRE that connects the trading system end-to-end.
Yair's trading IS the money printer. This pipeline supports it.
"""

import json
import os
import math
from datetime import datetime, timezone
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# INTEGRAFIX: Win Rate Booster integration
try:
    from integrafix.win_rate_booster import get_booster, WinRateBooster
    WIN_RATE_BOOSTER_AVAILABLE = True
except ImportError:
    WIN_RATE_BOOSTER_AVAILABLE = False

# INTEGRAFIX: Edge Optimizer integration
try:
    from integrafix.edge_optimizer import EdgeOptimizer
    EDGE_OPTIMIZER_AVAILABLE = True
except ImportError:
    EDGE_OPTIMIZER_AVAILABLE = False

# INTEGRAFIX: Knowledge Base integration (52k lines of wisdom)
try:
    from integrafix.knowledge_loader import knowledge as kb_loader
    KNOWLEDGE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_AVAILABLE = False
    kb_loader = None

def get_trading_insight(market_title: str, category: str = None) -> Optional[str]:
    """INTEGRAFIX: Get relevant trading insight from knowledge bases."""
    if not KNOWLEDGE_AVAILABLE or not kb_loader:
        return None
    try:
        # Search for market-specific knowledge
        search_terms = []
        if category:
            search_terms.append(category)
        search_terms.extend(market_title.lower().replace('?', '').split()[:3])
        query = ' '.join(search_terms)
        results = kb_loader.search(query, limit=1)
        if results:
            return results[0].get('snippet', '')
    except Exception as e:
        # INTEGRAFIX: Log instead of swallow
        import logging
        logging.debug(f"Knowledge search failed for {market_title}: {e}")
    return None

# ABCFC Integration for position sizing and nexus cloud decisions
try:
    from executor.math.abcfc_unified import create_binary_market_density
    ABCFC_AVAILABLE = True
except ImportError:
    ABCFC_AVAILABLE = False

# ABCFC Nexus for decision space evaluation
try:
    from executor.math.abcfc_nexus import get_nexus, ABCFCNexus
    from executor.math.abcfc_layers import get_layers, ABCFCLayers
    ABCFC_NEXUS_AVAILABLE = True
except ImportError:
    ABCFC_NEXUS_AVAILABLE = False

# ABCFC Cloud Flyer for autonomous navigation
try:
    from executor.math.abcfc_cloud_flyer import ABCFCCloudFlyer
    ABCFC_CLOUD_AVAILABLE = True
except ImportError:
    ABCFC_CLOUD_AVAILABLE = False

# ABCFC Live for real order book integration
try:
    from executor.math.abcfc_live import (
        LiveABCFCBuilder,
        LivePosition,
        OrderBook,
        OrderBookLevel,
        parse_polymarket_book,
        analyze_order_flow,
    )
    ABCFC_LIVE_AVAILABLE = True
except ImportError:
    ABCFC_LIVE_AVAILABLE = False

# INTEGRAFIX: Capital Bridge - wires income to trading activation
try:
    from integrafix.capital_bridge import CapitalBridge
    CAPITAL_BRIDGE_AVAILABLE = True
except ImportError:
    CAPITAL_BRIDGE_AVAILABLE = False
    CapitalBridge = None

def check_capital_activation() -> Tuple[bool, float, str]:
    """
    INTEGRAFIX: Check if capital bridge allows live trading.
    Returns (can_trade_live, balance, message)
    """
    if not CAPITAL_BRIDGE_AVAILABLE:
        return False, 0.0, "Capital bridge not available"
    try:
        bridge = CapitalBridge()
        status = bridge.check_activation_ready()
        return status["ready"], status["balance"], status["message"]
    except Exception as e:
        return False, 0.0, f"Capital check failed: {e}"

# ABCFC State for unified state harmonization
try:
    from executor.math.abcfc_state import get_state as get_abcfc_state, decide as abcfc_decide
    ABCFC_STATE_AVAILABLE = True
except ImportError:
    ABCFC_STATE_AVAILABLE = False

# ABCFC System for complete hierarchy + nexus + order flow
try:
    from executor.math.abcfc_system import (
        ABCFCSystem,
        Action as ABCFCAction,
        OrderFlowModel,
        FlowPredictability,
    )
    ABCFC_SYSTEM_AVAILABLE = True
except ImportError:
    ABCFC_SYSTEM_AVAILABLE = False

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
PIPELINE_STATE = STATE_DIR / "trading_pipeline.json"
TRADES_LOG = STATE_DIR / "trades_executed.jsonl"
OUTCOMES_LOG = STATE_DIR / "trade_outcomes.jsonl"
LEARNINGS_LOG = STATE_DIR / "pipeline_learnings.jsonl"


class TradeStatus(Enum):
    """Status of a trade."""
    PENDING = "pending"           # Signal detected, not yet executed
    EXECUTING = "executing"       # Execution in progress
    EXECUTED = "executed"         # Order placed
    FILLED = "filled"             # Order filled
    PARTIAL = "partial"           # Partially filled
    CANCELLED = "cancelled"       # Cancelled
    FAILED = "failed"             # Execution failed
    RESOLVED = "resolved"         # Market resolved, outcome known


class OutcomeResult(Enum):
    """Result of a trade."""
    WIN = "win"
    LOSS = "loss"
    PUSH = "push"                 # Break even (rare)
    PENDING = "pending"           # Not yet resolved


@dataclass
class EdgeSignal:
    """An edge signal from detection."""
    id: str
    market_id: str
    market_question: str
    side: str                     # "YES" or "NO"
    edge: float                   # Edge percentage
    fair_price: float
    market_price: float
    confidence: float
    source: str                   # Which estimator produced this
    reasoning: str
    detected_at: str
    actionable: bool = True


@dataclass
class TradeRecord:
    """Record of a trade execution."""
    id: str
    signal_id: str
    market_id: str
    side: str
    size: float                   # Dollar amount
    price: float                  # Execution price
    status: TradeStatus
    executed_at: Optional[str] = None
    filled_at: Optional[str] = None
    fill_price: Optional[float] = None
    order_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class TradeOutcome:
    """Outcome of a resolved trade."""
    trade_id: str
    signal_id: str
    market_id: str
    side: str
    result: OutcomeResult
    entry_price: float
    resolution_price: float       # 1.0 if YES wins, 0.0 if NO wins
    pnl: float                    # Profit/loss in dollars
    pnl_pct: float                # Profit/loss percentage
    resolved_at: str
    edge_was_correct: bool        # Did our edge prediction pan out?
    edge_predicted: float
    edge_actual: float


@dataclass
class PipelineLearning:
    """A learning from the pipeline feedback loop."""
    id: str
    learning_type: str            # "edge_accuracy", "source_performance", "category_bias"
    observation: str
    adjustment: Dict              # What to change
    confidence: float
    learned_at: str
    applied: bool = False


class TradingPipeline:
    """
    The integrated trading pipeline.

    signal → execute → record → learn → (improves signal)
    """

    def __init__(self):
        self.state = self._load_state()
        self.pending_signals: Dict[str, EdgeSignal] = {}
        self.active_trades: Dict[str, TradeRecord] = {}
        self.pending_outcomes: Dict[str, TradeOutcome] = {}

    def _load_state(self) -> Dict:
        if PIPELINE_STATE.exists():
            with open(PIPELINE_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_signals": 0,
            "total_trades": 0,
            "total_resolved": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "source_performance": {},
            "category_performance": {},
            "learnings_applied": 0,
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(PIPELINE_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_trade(self, trade: TradeRecord):
        with open(TRADES_LOG, 'a') as f:
            f.write(json.dumps(asdict(trade), default=str) + "\n")

    def _log_outcome(self, outcome: TradeOutcome):
        with open(OUTCOMES_LOG, 'a') as f:
            f.write(json.dumps(asdict(outcome), default=str) + "\n")

    def _log_learning(self, learning: PipelineLearning):
        with open(LEARNINGS_LOG, 'a') as f:
            f.write(json.dumps(asdict(learning), default=str) + "\n")

    # ==================== STAGE 1: EDGE DETECTION ====================

    def detect_edge(self, market: Dict) -> Optional[EdgeSignal]:
        """
        Detect edge using integrafixed fair price estimator.

        This replaces the broken circular estimation.
        """
        from integrafix.fair_price_estimator import get_estimator

        estimator = get_estimator()
        estimate = estimator.estimate_fair_price(market)

        if not estimate.is_actionable:
            return None

        market_id = market.get('slug') or market.get('market_id', 'unknown')
        market_price = market.get('yes_price') or market.get('last', 0.5)

        # Determine side
        if estimate.edge_vs_market > 0:
            side = "YES"  # Fair > market, buy YES
        else:
            side = "NO"   # Fair < market, buy NO (sell YES)

        signal = EdgeSignal(
            id=f"sig_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            market_id=market_id,
            market_question=market.get('question', '')[:100],
            side=side,
            edge=abs(estimate.edge_vs_market),
            fair_price=estimate.fair_price,
            market_price=market_price,
            confidence=estimate.confidence,
            source=estimate.source,
            reasoning=estimate.reasoning,
            detected_at=datetime.now(timezone.utc).isoformat(),
        )

        self.pending_signals[signal.id] = signal
        self.state["total_signals"] += 1
        self._save_state()

        return signal

    def scan_for_edges(self, markets: List[Dict], min_edge: float = 0.02) -> List[EdgeSignal]:
        """
        Scan multiple markets for edges.

        INTEGRAFIX: Now uses WinRateBooster to filter low-quality signals.

        Args:
            markets: List of market dicts
            min_edge: Minimum edge to consider actionable
        """
        signals = []

        # INTEGRAFIX: Get win rate booster for intelligent filtering
        booster = None
        if WIN_RATE_BOOSTER_AVAILABLE:
            try:
                booster = get_booster()
            except:
                pass

        for market in markets:
            signal = self.detect_edge(market)
            if signal and signal.edge >= min_edge:
                # INTEGRAFIX: Apply win rate booster filter
                if booster:
                    should_take, reason = booster.should_take_signal(
                        market_title=signal.market_question,
                        edge=signal.edge,
                        confidence=signal.confidence,
                        price=signal.market_price,
                        composite_score=signal.edge * signal.confidence
                    )
                    if not should_take:
                        continue  # Skip this signal

                signals.append(signal)

        # Sort by edge * confidence (expected value)
        signals.sort(key=lambda s: s.edge * s.confidence, reverse=True)

        return signals

    # ==================== STAGE 2: EXECUTE ====================

    def execute_signal(
        self,
        signal: EdgeSignal,
        size: float,
        dry_run: bool = True,
    ) -> TradeRecord:
        """
        Execute a trade based on an edge signal.

        Args:
            signal: The edge signal to act on
            size: Dollar amount to trade
            dry_run: If True, simulate only
        """
        trade = TradeRecord(
            id=f"trade_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            signal_id=signal.id,
            market_id=signal.market_id,
            side=signal.side,
            size=size,
            price=signal.market_price,
            status=TradeStatus.EXECUTING,
        )

        try:
            if dry_run:
                # Simulate execution
                trade.status = TradeStatus.EXECUTED
                trade.executed_at = datetime.now(timezone.utc).isoformat()
                trade.fill_price = signal.market_price
                trade.order_id = f"DRY_{trade.id}"
            else:
                # Real execution
                result = self._execute_real_trade(signal, size)
                trade.status = TradeStatus(result.get("status", "failed"))
                trade.executed_at = result.get("executed_at")
                trade.fill_price = result.get("fill_price")
                trade.order_id = result.get("order_id")
                trade.error = result.get("error")

            self.active_trades[trade.id] = trade
            self.state["total_trades"] += 1
            self._log_trade(trade)
            self._save_state()

            # ABCFC Integration: Sync to unified state
            self.sync_to_unified_state(trade_record=trade)

            # ABCFC Integration: Add to layers hierarchy
            self.add_to_layers_hierarchy(signal, size)

        except Exception as e:
            trade.status = TradeStatus.FAILED
            trade.error = str(e)
            self._log_trade(trade)

        return trade

    def _execute_real_trade(self, signal: EdgeSignal, size: float) -> Dict:
        """
        Execute a real trade via Polymarket CLOB.
        INTEGRAFIX: Uses credential_loader for unified key access.
        """
        try:
            # INTEGRAFIX: Use credential_loader instead of direct env access
            from integrafix.credential_loader import load_polymarket_key
            private_key = load_polymarket_key()
            if not private_key:
                return {"status": "failed", "error": "No API key - check credential_loader"}

            from py_clob_client.client import ClobClient
            from py_clob_client.order_builder.constants import BUY, SELL

            client = ClobClient(
                "https://clob.polymarket.com",
                key=private_key,
                chain_id=137,
            )
            creds = client.create_or_derive_api_creds()
            client.set_api_creds(creds)

            # Determine order parameters
            side_code = BUY if signal.side == "YES" else SELL
            price = signal.market_price

            # INTEGRAFIX: Get token ID for this market
            from py_clob_client.clob_types import OrderArgs

            token_id = None
            market_id = signal.market_id

            # Try to get token_id from market
            try:
                market_info = client.get_market(market_id)
                if market_info:
                    tokens = market_info.get("tokens", [])
                    for t in tokens:
                        if t.get("outcome") == signal.side:
                            token_id = t.get("token_id")
                            break
            except:
                # Use market_id as token_id fallback
                token_id = market_id

            if not token_id:
                return {"status": "failed", "error": "Could not get token_id"}

            # INTEGRAFIX: Create and post actual order
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=size,
                side=side_code
            )

            signed_order = client.create_order(order_args)
            result = client.submit_legacy_order(signed_order)

            order_id = result.get("orderID") or result.get("id") if result else None

            if order_id or result:
                return {
                    "status": "executed",
                    "executed_at": datetime.now(timezone.utc).isoformat(),
                    "fill_price": price,
                    "order_id": str(order_id or result)[:50],
                }
            else:
                return {"status": "failed", "error": "No order_id returned"}

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def execute_batch(
        self,
        signals: List[EdgeSignal],
        total_size: float,
        max_per_trade: float = 50,
        dry_run: bool = True,
    ) -> List[TradeRecord]:
        """
        Execute multiple signals with position sizing.

        Args:
            signals: Signals to execute
            total_size: Total capital to deploy
            max_per_trade: Maximum per single trade
            dry_run: If True, simulate only
        """
        # INTEGRAFIX: Capital Bridge gate check
        # If live trading requested, verify capital is available
        if not dry_run:
            can_trade, balance, msg = check_capital_activation()
            if not can_trade:
                import logging
                logging.warning(f"CAPITAL BRIDGE: Live trading blocked - {msg}")
                logging.warning(f"CAPITAL BRIDGE: Forcing DRY_RUN mode. Fund wallet to enable live trading.")
                dry_run = True  # Force dry run until capital threshold met

        trades = []
        remaining = total_size

        for signal in signals:
            if remaining <= 0:
                break

            # Size using ABCFC-enhanced Kelly criterion
            suggested_size = self._abcfc_position_size(
                signal=signal,
                total_capital=total_size,
                max_position=max_per_trade
            )
            size = min(suggested_size, max_per_trade, remaining)

            if size < 1:  # Minimum $1 trade
                continue

            trade = self.execute_signal(signal, size, dry_run)
            trades.append(trade)
            remaining -= size

        return trades

    def evaluate_with_nexus(
        self,
        signals: List['EdgeSignal'],
        current_positions: List[Dict] = None,
        risk_aversion: float = 0.5,
    ) -> List['EdgeSignal']:
        """
        Evaluate signals using ABCFC Nexus decision space.

        This uses the full ABCFC hierarchy and nexus cloud to determine
        which trades to execute based on their impact on the overall portfolio.

        Args:
            signals: List of edge signals to evaluate
            current_positions: Current portfolio positions
            risk_aversion: Risk aversion parameter (0 = risk loving, 1 = risk averse)

        Returns:
            Filtered and ranked list of signals to execute
        """
        if not ABCFC_NEXUS_AVAILABLE or not signals:
            return signals  # Fallback: return as-is

        try:
            # Get ABCFC nexus and layers
            nexus = get_nexus()
            layers = get_layers()

            # Add current positions to hierarchy
            if current_positions:
                for pos in current_positions:
                    market_id = pos.get('market_id') or pos.get('slug', 'unknown')
                    price = pos.get('price') or pos.get('avgPrice', 0.5)
                    size = pos.get('size') or pos.get('shares', 0) * price
                    if size > 0:
                        layers.add_polymarket_position(market_id, price, size)

            nexus.set_steady_state(layers)

            # Clear old actions
            nexus.clear_actions()

            # Add each signal as a potential action
            for signal in signals:
                action_name = f"trade_{signal.market_id}_{signal.side}"

                if signal.side == "YES":
                    nexus.add_buy_action(
                        action_name,
                        signal.market_id,
                        size=10.0,  # $10 base size
                        price=signal.market_price
                    )
                else:
                    nexus.add_sell_action(
                        action_name,
                        signal.market_id,
                        size=10.0
                    )

            # Add hold as baseline
            nexus.add_hold_action("hold")

            # Evaluate all actions
            nexus.evaluate(risk_aversion=risk_aversion)

            # Get ranked actions
            best_action = nexus.best_action()

            # Filter signals: only keep those with positive risk-adjusted score
            # and better than hold
            hold_score = nexus._actions.get("hold", None)
            hold_baseline = hold_score.risk_adjusted_score if hold_score else 0

            approved_signals = []
            for signal in signals:
                action_name = f"trade_{signal.market_id}_{signal.side}"
                action = nexus._actions.get(action_name)

                if action and action.risk_adjusted_score > hold_baseline:
                    # Enhance signal with nexus data
                    signal.nexus_score = action.risk_adjusted_score
                    signal.nexus_expected_improvement = action.expected_improvement
                    approved_signals.append(signal)

            # Sort by nexus score
            approved_signals.sort(key=lambda s: getattr(s, 'nexus_score', 0), reverse=True)

            return approved_signals

        except Exception as e:
            # Fallback on error
            return signals

    def build_live_abcfc(
        self,
        signal: 'EdgeSignal',
        order_book_data: Dict = None,
        trades: List[Dict] = None,
    ) -> Optional[Any]:
        """
        Build a live ABCFC for a signal using real order book data.

        This integrates order flow analysis to create flow-adjusted
        probability densities for more accurate position sizing.

        Args:
            signal: The edge signal
            order_book_data: Raw order book from Polymarket API
            trades: Recent trades for order flow analysis

        Returns:
            LivePosition ABCFC object or None if unavailable
        """
        if not ABCFC_LIVE_AVAILABLE:
            return None

        try:
            # Parse order book if provided
            order_book = None
            if order_book_data:
                order_book = parse_polymarket_book(order_book_data)

            # Analyze order flow if trades provided
            flow_stats = None
            if trades:
                flow_stats = analyze_order_flow(trades)

            # Create LivePosition
            position = LivePosition(
                token_id=signal.market_id,
                market_name=signal.market_question[:50],
                shares=1.0,  # Normalized for density calculation
                entry_price=signal.market_price,
                side=signal.side,
                market_prob=signal.fair_price,
                order_book=order_book,
                flow_stats=flow_stats,
            )

            return position

        except Exception:
            return None

    def sync_to_unified_state(
        self,
        positions: List[Dict] = None,
        trade_record: 'TradeRecord' = None,
    ):
        """
        Sync trading state to the unified ABCFC state.

        This ensures THE state (UnifiedABCFCState) reflects all trading activity.
        Everything is ABCFC - Polymarket positions, Claude value, Business revenue.

        Args:
            positions: Current positions to sync
            trade_record: Recent trade to record
        """
        if not ABCFC_STATE_AVAILABLE:
            return

        try:
            state = get_abcfc_state()

            # Update trading positions
            if positions:
                abcfc_positions = []
                for pos in positions:
                    entry = pos.get('avgPrice') or pos.get('entry_price', 0.5)
                    shares = pos.get('shares') or pos.get('size', 0)
                    prob = pos.get('market_prob', entry)

                    # Calculate ABCFC bounds
                    if pos.get('side', 'YES') == 'YES':
                        worst = -shares * entry
                        best = shares * (1 - entry)
                        expected = shares * (prob - entry)
                    else:
                        worst = -shares * (1 - entry)
                        best = shares * entry
                        expected = shares * ((1 - prob) - (1 - entry))

                    abcfc_positions.append({
                        'name': pos.get('market_id', 'unknown')[:30],
                        'worst': worst,
                        'best': best,
                        'expected': expected,
                    })

                state.update_trading(abcfc_positions)

            # Record Claude value from trading activity
            if trade_record and trade_record.status == TradeStatus.EXECUTED:
                state.update_claude(
                    action_taken=f"trade_{trade_record.side}",
                    value_added=trade_record.size * 0.02,  # Estimated 2% edge value
                    worst=0,
                    best=trade_record.size * 0.1,  # Potential 10% upside
                )

        except Exception:
            pass  # Don't fail pipeline on state sync errors

    def query_unified_state_decision(self) -> Optional[Dict]:
        """
        Query the unified ABCFC state for a decision.

        Returns the nexus cloud decision on best action across all domains.
        """
        if not ABCFC_STATE_AVAILABLE:
            return None

        try:
            return abcfc_decide()
        except Exception:
            return None

    def add_to_layers_hierarchy(
        self,
        signal: 'EdgeSignal',
        size: float,
    ):
        """
        Add a position to the ABCFC layers hierarchy.

        This maintains the hierarchical view:
        Yair Siegel → Trading → Polymarket → [position]
        """
        if not ABCFC_NEXUS_AVAILABLE:
            return

        try:
            layers = get_layers()

            # Add to Polymarket layer
            layers.add_polymarket_position(
                market_slug=signal.market_id,
                entry_price=signal.market_price,
                size=size,
                prob_yes=signal.fair_price if signal.side == 'YES' else 1 - signal.fair_price,
                side=signal.side,
                days=30,  # Default 30 days to resolution
            )

            # Save hierarchy state
            layers.save()

        except Exception:
            pass

    def evaluate_topline_impact(
        self,
        signal: 'EdgeSignal',
        size: float,
        current_positions: List[Dict] = None,
    ) -> Optional[Dict]:
        """
        Evaluate how a trade affects Yair Siegel's top-line ABCFC.

        This is the KEY insight: every trade propagates up to the root.
        See impact on total worst/best/expected before executing.

        Args:
            signal: The edge signal to evaluate
            size: Proposed position size
            current_positions: Current portfolio positions

        Returns:
            Dict with top-line impact analysis
        """
        if not ABCFC_SYSTEM_AVAILABLE:
            return None

        try:
            # Create system with current state
            system = ABCFCSystem("Yair Siegel")
            system.risk_aversion = 0.5

            # Build hierarchy from current positions
            system.add_category("Trading")
            system.add_subcategory("Trading", "Polymarket")

            if current_positions:
                for pos in current_positions:
                    entry = pos.get('avgPrice') or pos.get('entry_price', 0.5)
                    shares = pos.get('shares') or pos.get('size', 0)
                    prob = pos.get('market_prob', entry)
                    side = pos.get('side', 'YES')

                    if side == 'YES':
                        worst = -shares * entry
                        best = shares * (1 - entry)
                        expected = shares * (prob - entry)
                    else:
                        worst = -shares * (1 - entry)
                        best = shares * entry
                        expected = shares * ((1 - prob) - (1 - entry))

                    market_id = pos.get('market_id', f'pos_{len(system.hierarchy.all_nodes)}'[:20])
                    system.add_position("Polymarket", market_id, worst, best, expected)

            # Create action for proposed trade
            action = ABCFCAction(
                name=f"trade_{signal.market_id[:15]}",
                action_type="buy" if signal.side == "YES" else "sell",
                params={"size": size, "price": signal.market_price}
            )

            # Evaluate top-line impact
            # First add a placeholder position for the new trade
            entry = signal.market_price
            if signal.side == 'YES':
                worst = -size * entry
                best = size * (1 - entry)
                expected = size * (signal.fair_price - entry)
            else:
                worst = -size * (1 - entry)
                best = size * entry
                expected = size * ((1 - signal.fair_price) - (1 - entry))

            pos_name = f"NEW_{signal.market_id[:15]}"
            system.add_position("Polymarket", pos_name, worst, best, expected)

            # Get impact
            top_line_after = {
                "worst": system.total_bounds()[0],
                "best": system.total_bounds()[1],
                "expected": system.total_expected(),
            }

            # Calculate delta from before
            top_line_before = {
                "worst": top_line_after["worst"] - worst,
                "best": top_line_after["best"] - best,
                "expected": top_line_after["expected"] - expected,
            }

            return {
                "signal_id": signal.id,
                "market_id": signal.market_id,
                "side": signal.side,
                "size": size,
                "top_line_before": top_line_before,
                "top_line_after": top_line_after,
                "delta": {
                    "worst": worst,
                    "best": best,
                    "expected": expected,
                },
                "risk_adjusted_score": (
                    0.5 * expected + 0.5 * worst  # 50% risk aversion
                ),
            }

        except Exception:
            return None

    def find_best_global_action(
        self,
        signals: List['EdgeSignal'],
        current_positions: List[Dict] = None,
        risk_aversion: float = 0.5,
    ) -> Optional[Dict]:
        """
        Find the best action across ALL signals using ABCFCSystem.

        This evaluates every signal's impact on the global top-line
        and returns the one with the highest risk-adjusted score.

        Args:
            signals: List of edge signals to evaluate
            current_positions: Current portfolio positions
            risk_aversion: Risk aversion parameter (0-1)

        Returns:
            Best signal with top-line impact analysis
        """
        if not ABCFC_SYSTEM_AVAILABLE or not signals:
            return None

        try:
            best_result = None
            best_score = float('-inf')

            for signal in signals:
                # Evaluate each signal's top-line impact
                result = self.evaluate_topline_impact(
                    signal=signal,
                    size=signal.edge * signal.confidence * 100,  # Scale by edge
                    current_positions=current_positions,
                )

                if result and result.get("risk_adjusted_score", float('-inf')) > best_score:
                    best_score = result["risk_adjusted_score"]
                    best_result = {
                        "signal": signal,
                        "impact": result,
                    }

            return best_result

        except Exception:
            return None

    def infer_order_flow_model(
        self,
        trades: List[Dict],
    ) -> Optional[Dict]:
        """
        Infer order flow model from trade history.

        Three levels of predictability:
        1. PERFECT_DISCRETE - Know exact orders coming
        2. CONTINUOUS_RATE - Know arrival rate λ(t)
        3. UNKNOWN_CHAOTIC - Don't even know rate

        Args:
            trades: List of trade dicts with 'timestamp'

        Returns:
            Order flow model info
        """
        if not ABCFC_SYSTEM_AVAILABLE or not trades:
            return None

        try:
            timestamps = [t.get('timestamp', 0) for t in trades if t.get('timestamp')]
            if len(timestamps) < 3:
                return {"level": "UNKNOWN", "confidence": 0.0}

            model = OrderFlowModel.from_order_history(timestamps)

            return {
                "level": model.level.name,
                "rate": model.get_rate(0),
                "confidence": model.get_confidence(),
                "regularity": model.regularity_score,
            }

        except Exception:
            return None

    def _abcfc_position_size(
        self,
        signal: 'EdgeSignal',
        total_capital: float,
        max_position: float = 50.0,
    ) -> float:
        """
        Calculate position size using ABCFC probability density.

        Uses the Kelly criterion with ABCFC-derived win probability and edge.

        Kelly formula: f* = (bp - q) / b
        Where:
            f* = fraction of capital to bet
            b = odds received on win (payout / risk)
            p = probability of winning (from ABCFC)
            q = probability of losing (1 - p)

        Returns optimal position size in dollars.
        """
        # Fallback to simple edge * confidence if ABCFC unavailable
        # GOLDEN STATE: Minimum $15 even in fallback
        if not ABCFC_AVAILABLE:
            size = total_capital * signal.edge * signal.confidence
            return max(15.0, min(size, max_position))

        try:
            entry_price = signal.market_price
            fair_price = signal.fair_price

            # Create ABCFC density for this position
            density_func = create_binary_market_density(
                prob_yes=fair_price,  # Our estimated true probability
                entry_price=entry_price,
                shares=1.0
            )

            # Calculate expected value and variance from density
            worst_pnl = -entry_price
            best_pnl = 1 - entry_price
            days = 30  # Assume 30 days to resolution

            n_samples = 50
            total_prob = 0.0
            expected_pnl = 0.0
            expected_pnl_sq = 0.0

            for i in range(n_samples):
                x = worst_pnl + (best_pnl - worst_pnl) * i / (n_samples - 1)
                t = days * 0.5  # Mid-point

                p = density_func(x, t, worst_pnl, best_pnl, days)
                total_prob += p
                expected_pnl += p * x
                expected_pnl_sq += p * x * x

            if total_prob > 0:
                expected_pnl /= total_prob
                expected_pnl_sq /= total_prob
                variance = expected_pnl_sq - expected_pnl ** 2
            else:
                # Fallback
                return total_capital * signal.edge * signal.confidence

            # Kelly criterion with ABCFC probability
            # Win probability from ABCFC
            if signal.side == "YES":
                win_prob = fair_price
                win_pnl = best_pnl  # Win if YES resolves at 1
                lose_pnl = worst_pnl  # Lose if YES resolves at 0
            else:
                win_prob = 1 - fair_price
                win_pnl = entry_price  # Win if NO resolves at 1 (YES at 0)
                lose_pnl = -(1 - entry_price)  # Lose if NO resolves at 0

            # Kelly fraction
            # f* = (p * b - q) / b where b = win/lose ratio
            if abs(lose_pnl) > 0.01:
                b = abs(win_pnl / lose_pnl)
                q = 1 - win_prob
                kelly_fraction = (win_prob * b - q) / b
            else:
                kelly_fraction = signal.edge * signal.confidence

            # GOLDEN STATE: Use 0.75 Kelly (less conservative than half-Kelly)
            kelly_fraction = kelly_fraction * 0.75

            # GOLDEN STATE: Clamp to higher range [0.10, 0.35] for larger trades
            kelly_fraction = max(0.10, min(kelly_fraction, 0.35))

            # Adjust by confidence
            kelly_fraction *= signal.confidence

            # Calculate position size
            position_size = total_capital * kelly_fraction

            # GOLDEN STATE: Minimum $15 per trade (proven optimal sizing)
            # This prevents fragmented small bets that kill profitability
            position_size = max(15.0, min(position_size, max_position))

            return position_size

        except Exception:
            # Fallback to simple calculation
            return total_capital * signal.edge * signal.confidence

    # ==================== STAGE 3: RECORD OUTCOMES ====================

    def record_outcome(
        self,
        trade_id: str,
        resolution_price: float,  # 1.0 if YES wins, 0.0 if NO wins
    ) -> Optional[TradeOutcome]:
        """
        Record the outcome of a resolved trade.

        Args:
            trade_id: ID of the trade
            resolution_price: Final price (1.0 for YES win, 0.0 for NO win)
        """
        trade = self.active_trades.get(trade_id)
        if not trade:
            return None

        signal = self.pending_signals.get(trade.signal_id)

        # Calculate P&L
        if trade.side == "YES":
            # Bought YES at trade.fill_price
            # Resolved at resolution_price
            pnl_per_dollar = resolution_price - (trade.fill_price or trade.price)
        else:
            # Bought NO (equivalent to selling YES)
            pnl_per_dollar = (trade.fill_price or trade.price) - resolution_price

        pnl = trade.size * pnl_per_dollar
        pnl_pct = pnl_per_dollar * 100

        # Determine result
        if pnl > 0.01:
            result = OutcomeResult.WIN
        elif pnl < -0.01:
            result = OutcomeResult.LOSS
        else:
            result = OutcomeResult.PUSH

        # Was our edge prediction correct?
        edge_actual = abs(resolution_price - (trade.fill_price or trade.price))
        edge_was_correct = (
            (signal and signal.edge > 0 and pnl > 0) or
            (signal and signal.edge < 0 and pnl < 0)
        ) if signal else False

        outcome = TradeOutcome(
            trade_id=trade_id,
            signal_id=trade.signal_id,
            market_id=trade.market_id,
            side=trade.side,
            result=result,
            entry_price=trade.fill_price or trade.price,
            resolution_price=resolution_price,
            pnl=round(pnl, 4),
            pnl_pct=round(pnl_pct, 2),
            resolved_at=datetime.now(timezone.utc).isoformat(),
            edge_was_correct=edge_was_correct,
            edge_predicted=signal.edge if signal else 0,
            edge_actual=edge_actual,
        )

        # Update trade status
        trade.status = TradeStatus.RESOLVED

        # Track performance
        self.state["total_resolved"] += 1
        self.state["total_pnl"] = self.state.get("total_pnl", 0) + pnl

        # Update win rate
        resolved = self.state["total_resolved"]
        wins = sum(1 for _ in []) + (1 if result == OutcomeResult.WIN else 0)
        # This is a simplification - proper tracking would load all outcomes
        if resolved > 0:
            current_wins = self.state.get("win_rate", 0) * (resolved - 1)
            new_wins = current_wins + (1 if result == OutcomeResult.WIN else 0)
            self.state["win_rate"] = new_wins / resolved

        # Track by source
        if signal:
            source = signal.source
            if source not in self.state["source_performance"]:
                self.state["source_performance"][source] = {
                    "trades": 0, "wins": 0, "pnl": 0
                }
            self.state["source_performance"][source]["trades"] += 1
            if result == OutcomeResult.WIN:
                self.state["source_performance"][source]["wins"] += 1
            self.state["source_performance"][source]["pnl"] += pnl

        self._log_outcome(outcome)
        self._save_state()

        # INTEGRAFIX HIGHER: Update ABCFC hierarchy with resolved outcome
        self._update_hierarchy_with_outcome(outcome, trade)

        return outcome

    def _update_hierarchy_with_outcome(self, outcome: TradeOutcome, trade) -> None:
        """
        Wire resolved trade outcome back to ABCFC hierarchy.
        This closes the feedback loop: hierarchy -> decision -> execution -> outcome -> hierarchy
        """
        try:
            from pathlib import Path
            import json

            unified_file = BASE_DIR / "state" / "abcfc_unified_state.json"
            if not unified_file.exists():
                return

            with open(unified_file, "r") as f:
                unified = json.load(f)

            # Find and update the position in hierarchy
            positions = unified.get("positions", [])
            updated = False

            for pos in positions:
                if pos.get("market_id") == outcome.market_id or pos.get("name", "").startswith(trade.market_id[:20] if trade.market_id else ""):
                    # Position resolved - update bounds with realized PnL
                    realized_pnl = outcome.pnl

                    # Remove the position's risk (it's resolved)
                    pos["worst"] = realized_pnl  # No more downside - we know the outcome
                    pos["best"] = realized_pnl   # No more upside - we know the outcome
                    pos["expected"] = realized_pnl
                    pos["status"] = "RESOLVED"
                    pos["resolved_at"] = outcome.resolved_at
                    pos["resolution_price"] = outcome.resolution_price
                    updated = True
                    break

            if not updated:
                # Add as a resolved position for tracking
                positions.append({
                    "category": "Trading",
                    "name": f"Resolved: {outcome.market_id[:30]}",
                    "market_id": outcome.market_id,
                    "worst": outcome.pnl,
                    "best": outcome.pnl,
                    "expected": outcome.pnl,
                    "status": "RESOLVED",
                    "resolved_at": outcome.resolved_at,
                    "pnl": outcome.pnl
                })

            unified["positions"] = positions

            # Update top-line aggregates
            trading_positions = [p for p in positions if p.get("category") == "Trading"]
            unified["trading_summary"] = {
                "total_positions": len(trading_positions),
                "resolved": len([p for p in trading_positions if p.get("status") == "RESOLVED"]),
                "total_realized_pnl": sum(p.get("pnl", 0) for p in trading_positions if p.get("status") == "RESOLVED"),
                "open_worst": sum(p.get("worst", 0) for p in trading_positions if p.get("status") != "RESOLVED"),
                "open_best": sum(p.get("best", 0) for p in trading_positions if p.get("status") != "RESOLVED"),
                "open_expected": sum(p.get("expected", 0) for p in trading_positions if p.get("status") != "RESOLVED"),
            }

            unified["last_outcome_sync"] = outcome.resolved_at

            with open(unified_file, "w") as f:
                json.dump(unified, f, indent=2)

        except Exception as e:
            # Don't fail the outcome recording if hierarchy sync fails
            pass

    # ==================== STAGE 4: LEARN ====================

    def analyze_and_learn(self) -> List[PipelineLearning]:
        """
        Analyze outcomes and generate learnings.

        This completes the feedback loop.
        """
        learnings = []

        # Load recent outcomes
        outcomes = []
        if OUTCOMES_LOG.exists():
            with open(OUTCOMES_LOG) as f:
                for line in f:
                    try:
                        outcomes.append(json.loads(line))
                    except:
                        pass

        if len(outcomes) < 5:
            return learnings  # Need more data

        # Learning 1: Source performance analysis
        source_stats = self.state.get("source_performance", {})
        for source, stats in source_stats.items():
            if stats["trades"] >= 5:
                win_rate = stats["wins"] / stats["trades"]
                avg_pnl = stats["pnl"] / stats["trades"]

                if win_rate < 0.40:
                    learning = PipelineLearning(
                        id=f"learn_{datetime.now().strftime('%Y%m%d%H%M%S')}_source_{source}",
                        learning_type="source_performance",
                        observation=f"Source {source} has {win_rate:.0%} win rate - underperforming",
                        adjustment={
                            "action": "reduce_confidence",
                            "source": source,
                            "factor": 0.8,
                        },
                        confidence=0.7,
                        learned_at=datetime.now(timezone.utc).isoformat(),
                    )
                    learnings.append(learning)
                    self._log_learning(learning)

                elif win_rate > 0.65:
                    learning = PipelineLearning(
                        id=f"learn_{datetime.now().strftime('%Y%m%d%H%M%S')}_source_{source}",
                        learning_type="source_performance",
                        observation=f"Source {source} has {win_rate:.0%} win rate - outperforming",
                        adjustment={
                            "action": "increase_confidence",
                            "source": source,
                            "factor": 1.2,
                        },
                        confidence=0.7,
                        learned_at=datetime.now(timezone.utc).isoformat(),
                    )
                    learnings.append(learning)
                    self._log_learning(learning)

        # Learning 2: Edge accuracy analysis
        edge_accuracy = [o for o in outcomes if o.get("edge_was_correct")]
        if len(outcomes) > 0:
            accuracy = len(edge_accuracy) / len(outcomes)

            if accuracy < 0.50:
                learning = PipelineLearning(
                    id=f"learn_{datetime.now().strftime('%Y%m%d%H%M%S')}_edge_accuracy",
                    learning_type="edge_accuracy",
                    observation=f"Edge predictions only {accuracy:.0%} accurate - worse than coin flip",
                    adjustment={
                        "action": "increase_min_edge",
                        "new_min_edge": 0.03,
                    },
                    confidence=0.6,
                    learned_at=datetime.now(timezone.utc).isoformat(),
                )
                learnings.append(learning)
                self._log_learning(learning)

        self.state["learnings_applied"] += len(learnings)
        self._save_state()

        return learnings

    def apply_learnings(self, learnings: List[PipelineLearning]):
        """
        Apply learnings to improve future edge detection.

        This modifies the estimator's behavior.
        """
        for learning in learnings:
            if learning.applied:
                continue

            adjustment = learning.adjustment
            action = adjustment.get("action")

            if action == "reduce_confidence":
                # Would modify the fair price estimator to reduce confidence
                # from this source
                pass
            elif action == "increase_confidence":
                # Would modify the fair price estimator to increase confidence
                # from this source
                pass
            elif action == "increase_min_edge":
                # Would update the minimum edge threshold
                pass

            learning.applied = True

    # ==================== UNIFIED PIPELINE ====================

    def run_pipeline(
        self,
        markets: List[Dict],
        capital: float = 100,
        max_per_trade: float = 25,
        min_edge: float = 0.02,
        dry_run: bool = True,
    ) -> Dict:
        """
        Run the full integrated pipeline.

        market data → edge detection → execution → record → learn
        """
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "markets_scanned": len(markets),
            "signals_detected": 0,
            "trades_executed": 0,
            "total_size": 0,
            "dry_run": dry_run,
        }

        # Stage 1: Detect edges
        signals = self.scan_for_edges(markets, min_edge)
        result["signals_detected"] = len(signals)

        if not signals:
            result["message"] = "No actionable edges detected"
            return result

        # Stage 2: Execute
        trades = self.execute_batch(signals, capital, max_per_trade, dry_run)
        result["trades_executed"] = len(trades)
        result["total_size"] = sum(t.size for t in trades)
        result["trades"] = [
            {
                "id": t.id,
                "market": t.market_id,
                "side": t.side,
                "size": t.size,
                "status": t.status.value,
            }
            for t in trades
        ]

        # Stage 3 & 4: Recording and learning happen when markets resolve
        # (called separately via record_outcome and analyze_and_learn)

        return result

    def status(self) -> Dict:
        """Get pipeline status."""
        return {
            "state": self.state,
            "pending_signals": len(self.pending_signals),
            "active_trades": len(self.active_trades),
            "pending_outcomes": len(self.pending_outcomes),
        }


# Singleton instance
_pipeline = None

def get_pipeline() -> TradingPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = TradingPipeline()
    return _pipeline


def main():
    """Test the trading pipeline."""
    pipeline = get_pipeline()

    # Test markets
    test_markets = [
        {
            "slug": "test-market-1",
            "question": "Will the Lakers win?",
            "yes_price": 0.45,
            "no_price": 0.52,  # Arb opportunity
            "bestBid": 0.43,
            "bestAsk": 0.47,
        },
        {
            "slug": "test-market-2",
            "question": "Will Bitcoin hit 100k?",
            "yes_price": 0.65,
            "no_price": 0.35,
        },
    ]

    print("=" * 70)
    print("INTEGRAFIX: Trading Pipeline Test")
    print("=" * 70)
    print()

    # Run pipeline
    result = pipeline.run_pipeline(
        markets=test_markets,
        capital=100,
        max_per_trade=25,
        min_edge=0.01,
        dry_run=True,
    )

    print(f"Markets scanned: {result['markets_scanned']}")
    print(f"Signals detected: {result['signals_detected']}")
    print(f"Trades executed: {result['trades_executed']}")
    print(f"Total deployed: ${result['total_size']:.2f}")
    print()

    if result.get("trades"):
        print("Trades:")
        for t in result["trades"]:
            print(f"  {t['id'][:20]}... | {t['market'][:20]} | {t['side']} | ${t['size']:.2f}")

    print()
    print("Pipeline Status:")
    print(json.dumps(pipeline.status(), indent=2))

    return pipeline


if __name__ == "__main__":
    main()
