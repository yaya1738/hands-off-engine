#!/usr/bin/env python3
"""
Unified Signal Router: The Grand Conductor of Alpha Sources
============================================================

This is the final piece that connects EVERYTHING together:
- Polymarket native edge detection
- ESPN live game alpha
- Commercial AI mispricing signals
- Yair's golden sprinkle insights

The router:
1. Initializes and manages all adapters
2. Runs collection cycles on schedule
3. Applies Yair's vetoes and modifiers
4. Routes filtered signals to the Decider/Executor
5. Handles immediate vs batch execution
6. Provides real-time monitoring dashboard

This is where the automation comes to life.

Philosophy: "Hook everything together for fully optimal wealth extraction"
"""

import json
import sys
import os
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

# Add parent directory for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import all alpha components
from alpha.integrations_hub import (
    IntegrationsHub,
    SignalSource,
    SignalUrgency,
    UnifiedAlphaSignal
)
from alpha.espn_live_alpha import ESPNLiveAlphaAdapter, Sport
from alpha.commercial_ai_receiver import CommercialAIReceiver, AIProvider
from alpha.yair_insights import YairInsightsAdapter

try:
    from audit import AuditLogger
except ImportError:
    get_audit_logger = None

try:
    from ai_nexus.history_log import log_kernel_history_event
except ImportError:
    log_kernel_history_event = None


class ExecutionMode(Enum):
    """Trading execution modes"""
    DRYRUN = "dryrun"           # Log but don't execute
    PAPER = "paper"             # Simulate with fake money
    LIVE_MICRO = "live_micro"   # Real money, tiny stakes ($5-10)
    LIVE_SMALL = "live_small"   # Real money, small stakes ($10-50)
    LIVE_NORMAL = "live_normal" # Real money, normal stakes


@dataclass
class RoutingDecision:
    """Result of routing a signal through the system"""
    signal: UnifiedAlphaSignal
    passed_filters: bool
    vetoed: bool
    veto_reason: Optional[str]
    modifier_applied: bool
    final_edge: float
    final_confidence: float
    recommended_stake: float
    execution_priority: int  # 1 = highest


@dataclass
class CycleResult:
    """Result of a complete collection/routing cycle"""
    timestamp: str
    total_signals: int
    passed_filters: int
    vetoed: int
    immediate_signals: int
    routed_to_executor: int
    execution_mode: ExecutionMode
    signals: List[RoutingDecision]


class UnifiedSignalRouter:
    """
    The grand conductor that orchestrates all alpha sources.

    This is the main entry point for the automated trading system.
    """

    def __init__(
        self,
        execution_mode: ExecutionMode = ExecutionMode.DRYRUN,
        state_dir: Path = None
    ):
        self.execution_mode = execution_mode
        self.state_dir = state_dir or Path(__file__).parent.parent / 'state'

        # Initialize the hub
        self.hub = IntegrationsHub(self.state_dir)

        # Initialize all adapters
        self._init_adapters()

        # Yair adapter needs special access for vetoes/modifiers
        self.yair_adapter = self.adapters.get(SignalSource.YAIR_INSIGHTS)

        # Audit logging
        if get_audit_logger:
            self.audit = AuditLogger()
        else:
            self.audit = None

        # Execution callback (set externally)
        self.execution_callback: Optional[Callable] = None

        # Monitoring state
        self.is_running = False
        self.last_cycle_result: Optional[CycleResult] = None
        self.cycle_history: List[CycleResult] = []

        # Output paths
        self.routed_signals_path = self.state_dir / 'routed-signals.json'
        self.immediate_queue_path = self.state_dir / 'immediate-execution-queue.json'

    def _init_adapters(self):
        """Initialize and register all alpha source adapters"""
        self.adapters = {}

        # 1. ESPN Live Game Alpha
        espn_adapter = ESPNLiveAlphaAdapter(
            sports=[Sport.NBA, Sport.NFL, Sport.MLB]
        )
        self.hub.register_adapter(espn_adapter)
        self.adapters[SignalSource.ESPN_LIVE] = espn_adapter

        # 2. Commercial AI Receiver
        ai_receiver = CommercialAIReceiver(
            inbox_dir=self.state_dir / 'ai-signals-inbox',
            min_confidence=0.5
        )
        self.hub.register_adapter(ai_receiver)
        self.adapters[SignalSource.COMMERCIAL_AI] = ai_receiver

        # 3. Yair Insights
        yair_adapter = YairInsightsAdapter(
            insights_dir=self.state_dir / 'yair-insights'
        )
        self.hub.register_adapter(yair_adapter)
        self.adapters[SignalSource.YAIR_INSIGHTS] = yair_adapter

        print(f"[Router] Initialized {len(self.adapters)} adapters")

    def set_execution_callback(self, callback: Callable):
        """
        Set the callback function for executing trades.

        The callback receives a list of RoutingDecision objects.
        """
        self.execution_callback = callback

    def run_cycle(
        self,
        min_edge: float = 0.03,
        min_confidence: float = 0.5,
        max_signals: int = 20,
        execute: bool = True
    ) -> CycleResult:
        """
        Run a complete collection and routing cycle.

        This is the main loop that:
        1. Collects signals from all sources
        2. Applies filters and Yair's modifiers/vetoes
        3. Routes to executor if enabled
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"\n{'='*60}")
        print(f"[Router] Starting cycle at {timestamp}")
        print(f"[Router] Mode: {self.execution_mode.value}")
        print(f"{'='*60}\n")

        # 1. Collect from all sources
        all_signals = self.hub.collect_all_signals()
        print(f"[Router] Collected {len(all_signals)} raw signals")

        # 2. Route each signal through the pipeline
        routing_decisions = []
        passed_count = 0
        vetoed_count = 0
        immediate_count = 0

        for signal in all_signals:
            decision = self._route_signal(signal, min_edge, min_confidence)
            routing_decisions.append(decision)

            if decision.vetoed:
                vetoed_count += 1
            elif decision.passed_filters:
                passed_count += 1
                if signal.urgency == SignalUrgency.IMMEDIATE:
                    immediate_count += 1

        # 3. Sort by priority
        routing_decisions.sort(key=lambda d: (d.execution_priority, -d.final_edge))

        # 4. Take top signals
        actionable = [d for d in routing_decisions if d.passed_filters and not d.vetoed]
        top_signals = actionable[:max_signals]

        print(f"\n[Router] Routing summary:")
        print(f"  - Total collected: {len(all_signals)}")
        print(f"  - Passed filters: {passed_count}")
        print(f"  - Vetoed: {vetoed_count}")
        print(f"  - Immediate priority: {immediate_count}")
        print(f"  - Actionable (top {max_signals}): {len(top_signals)}")

        # 5. Execute if enabled
        routed_to_executor = 0
        if execute and top_signals:
            routed_to_executor = self._execute_signals(top_signals)

        # 6. Build result
        result = CycleResult(
            timestamp=timestamp,
            total_signals=len(all_signals),
            passed_filters=passed_count,
            vetoed=vetoed_count,
            immediate_signals=immediate_count,
            routed_to_executor=routed_to_executor,
            execution_mode=self.execution_mode,
            signals=top_signals
        )

        # 7. Save state
        self._save_cycle_result(result)
        self.last_cycle_result = result
        self.cycle_history.append(result)

        # Keep only last 100 cycles in memory
        if len(self.cycle_history) > 100:
            self.cycle_history = self.cycle_history[-100:]

        # 8. Audit log
        if self.audit:
            self.audit.log_data_fetch(
                data_source="signal_router",
                data_type="routing_cycle",
                record_count=len(top_signals),
                context={
                    'total': len(all_signals),
                    'passed': passed_count,
                    'vetoed': vetoed_count,
                    'executed': routed_to_executor,
                    'mode': self.execution_mode.value
                }
            )

        print(f"\n[Router] Cycle complete")
        print(f"{'='*60}\n")

        return result

    def _route_signal(
        self,
        signal: UnifiedAlphaSignal,
        min_edge: float,
        min_confidence: float
    ) -> RoutingDecision:
        """
        Route a single signal through the pipeline.

        Applies:
        - Edge/confidence filters
        - Yair's vetoes
        - Yair's modifiers
        - Stake sizing
        """
        # Start with signal values
        final_edge = signal.edge
        final_confidence = signal.confidence
        vetoed = False
        veto_reason = None
        modifier_applied = False

        # 1. Check Yair vetoes
        if self.yair_adapter:
            veto_check = self.yair_adapter.should_veto(signal.market_id)
            if veto_check:
                vetoed = True
                veto_reason = veto_check
                print(f"[Router] VETOED: {signal.market_id} - {veto_reason}")

        # 2. Apply Yair modifiers (if not vetoed)
        if not vetoed and self.yair_adapter:
            modified_signal = self.yair_adapter.apply_modifiers(signal)
            if modified_signal.edge != signal.edge:
                modifier_applied = True
                final_edge = modified_signal.edge
                final_confidence = modified_signal.confidence
                print(f"[Router] Modified {signal.market_id}: edge {signal.edge:.1%} -> {final_edge:.1%}")

        # 3. Apply filters
        passed_filters = (
            final_edge >= min_edge and
            final_confidence >= min_confidence and
            not vetoed
        )

        # 4. Calculate stake (based on execution mode)
        recommended_stake = self._calculate_stake(final_edge, final_confidence)

        # 5. Determine priority
        if signal.urgency == SignalUrgency.IMMEDIATE:
            execution_priority = 1
        elif signal.urgency == SignalUrgency.HIGH:
            execution_priority = 2
        else:
            execution_priority = 3

        return RoutingDecision(
            signal=signal,
            passed_filters=passed_filters,
            vetoed=vetoed,
            veto_reason=veto_reason,
            modifier_applied=modifier_applied,
            final_edge=final_edge,
            final_confidence=final_confidence,
            recommended_stake=recommended_stake,
            execution_priority=execution_priority
        )

    def _calculate_stake(self, edge: float, confidence: float) -> float:
        """
        Calculate recommended stake based on edge, confidence, and mode.

        Uses simplified Kelly criterion with mode-based caps.
        """
        # Base Kelly fraction
        kelly = edge * confidence

        # Mode-based caps
        mode_caps = {
            ExecutionMode.DRYRUN: 100.0,      # Unlimited for simulation
            ExecutionMode.PAPER: 100.0,        # Paper money
            ExecutionMode.LIVE_MICRO: 10.0,    # Max $10
            ExecutionMode.LIVE_SMALL: 50.0,    # Max $50
            ExecutionMode.LIVE_NORMAL: 100.0   # Max $100 per risk model
        }

        max_stake = mode_caps.get(self.execution_mode, 10.0)

        # Kelly-based stake (assuming $1000 bankroll)
        bankroll = 1000.0
        kelly_stake = bankroll * min(kelly, 0.10)  # Cap at 10% Kelly

        return min(kelly_stake, max_stake)

    def _execute_signals(self, decisions: List[RoutingDecision]) -> int:
        """
        Execute the routed signals.

        In DRYRUN mode: just logs
        In LIVE modes: calls the execution callback
        """
        executed = 0

        # Handle immediate signals first
        immediate = [d for d in decisions if d.execution_priority == 1]
        if immediate:
            print(f"\n*** IMMEDIATE EXECUTION: {len(immediate)} signals ***")
            for d in immediate:
                print(f"  {d.signal.market_id}: {d.signal.side} @ ${d.recommended_stake:.2f}")

        # Write to immediate queue
        if immediate:
            immediate_data = []
            for d in immediate:
                immediate_data.append({
                    'signal': d.signal.to_dict(),
                    'stake': d.recommended_stake,
                    'edge': d.final_edge,
                    'confidence': d.final_confidence,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            with open(self.immediate_queue_path, 'w') as f:
                json.dump(immediate_data, f, indent=2)

        # Execute based on mode
        if self.execution_mode == ExecutionMode.DRYRUN:
            print(f"\n[Router] DRYRUN mode - logging {len(decisions)} signals")
            executed = len(decisions)
        else:
            if self.execution_callback:
                try:
                    self.execution_callback(decisions)
                    executed = len(decisions)
                except Exception as e:
                    print(f"[Router] Execution error: {e}")
            else:
                print("[Router] No execution callback set - signals not executed")

        return executed

    def _save_cycle_result(self, result: CycleResult):
        """Save cycle result to disk"""
        # Convert to serializable format
        result_data = {
            'timestamp': result.timestamp,
            'total_signals': result.total_signals,
            'passed_filters': result.passed_filters,
            'vetoed': result.vetoed,
            'immediate_signals': result.immediate_signals,
            'routed_to_executor': result.routed_to_executor,
            'execution_mode': result.execution_mode.value,
            'signals': []
        }

        for d in result.signals:
            result_data['signals'].append({
                'market_id': d.signal.market_id,
                'market_name': d.signal.market_name,
                'source': d.signal.source.value,
                'side': d.signal.side,
                'final_edge': d.final_edge,
                'final_confidence': d.final_confidence,
                'recommended_stake': d.recommended_stake,
                'execution_priority': d.execution_priority,
                'vetoed': d.vetoed,
                'modifier_applied': d.modifier_applied
            })

        with open(self.routed_signals_path, 'w') as f:
            json.dump(result_data, f, indent=2)

    # =========================================================================
    # Convenience methods for submitting signals from various sources
    # =========================================================================

    def submit_ai_signal(
        self,
        market_id: str,
        side: str,
        fair_price: float = None,
        confidence: float = None,
        reasoning: str = "",
        provider: AIProvider = AIProvider.CUSTOM
    ) -> str:
        """Submit a signal from a commercial AI product"""
        ai_adapter = self.adapters.get(SignalSource.COMMERCIAL_AI)
        if ai_adapter:
            return ai_adapter.submit_signal(
                market_id, side, fair_price, confidence, reasoning, provider
            )
        return None

    def submit_yair_insight(self, text: str, source_name: str = "yair") -> str:
        """Submit an insight from Yair"""
        if self.yair_adapter:
            return self.yair_adapter.submit_insight(text, source_name)
        return None

    def add_veto(self, pattern: str, reason: str = "Manual veto"):
        """Add a veto pattern"""
        if self.yair_adapter:
            self.yair_adapter.submit_insight(f"avoid {pattern} - {reason}")
            # Process immediately
            self.yair_adapter.fetch_signals()

    def remove_veto(self, pattern: str):
        """Remove a veto pattern"""
        if self.yair_adapter:
            self.yair_adapter.clear_veto(pattern)

    def get_active_vetoes(self) -> List[str]:
        """Get list of active veto patterns"""
        if self.yair_adapter:
            return [v.veto_market_pattern for v in self.yair_adapter._active_vetoes]
        return []

    # =========================================================================
    # Continuous monitoring mode
    # =========================================================================

    def start_continuous(
        self,
        interval_seconds: int = 60,
        live_game_interval: int = 30
    ):
        """
        Start continuous monitoring mode.

        Runs regular cycles at interval_seconds, with faster polling
        during live games.
        """
        self.is_running = True
        print(f"\n[Router] Starting continuous mode")
        print(f"[Router] Regular interval: {interval_seconds}s")
        print(f"[Router] Live game interval: {live_game_interval}s")

        while self.is_running:
            try:
                result = self.run_cycle()

                # If we have immediate signals, poll faster
                if result.immediate_signals > 0:
                    print(f"[Router] Live action detected - fast polling")
                    time.sleep(live_game_interval)
                else:
                    time.sleep(interval_seconds)

            except KeyboardInterrupt:
                print("\n[Router] Stopping continuous mode...")
                self.is_running = False
            except Exception as e:
                print(f"[Router] Error in cycle: {e}")
                time.sleep(interval_seconds)

    def stop_continuous(self):
        """Stop continuous monitoring"""
        self.is_running = False


# ============================================================================
# Wire to the Decider/Executor pipeline
# ============================================================================

def create_decider_execution_callback(decider, executor):
    """
    Create an execution callback that uses the existing Decider/Executor.

    This bridges the new router system with the existing pipeline.
    """
    def callback(decisions: List[RoutingDecision]):
        # Convert RoutingDecisions to alpha signals for decider
        alpha_signals = []
        for d in decisions:
            signal = {
                'market_id': d.signal.market_id,
                'market_name': d.signal.market_name,
                'edge': d.final_edge,
                'current_odds': d.signal.market_price,
                'side': d.signal.side,
                'model_confidence': d.final_confidence,
                'fair_price': d.signal.fair_price
            }
            alpha_signals.append(signal)

        # Run through decider
        planned_actions = decider.plan_actions(alpha_signals)

        # Execute
        for action in planned_actions:
            print(f"[Executor] {action.side} on {action.market_id} @ ${action.amount:.2f}")
            # In LIVE mode, executor would call Polymarket API here

        return len(planned_actions)

    return callback


# ============================================================================
# Main entry point
# ============================================================================

def main():
    """Demo the unified signal router"""
    print("=" * 60)
    print("UNIFIED SIGNAL ROUTER")
    print("Hook Everything Together for Optimal Wealth Extraction")
    print("=" * 60)

    # Initialize router in DRYRUN mode
    router = UnifiedSignalRouter(execution_mode=ExecutionMode.DRYRUN)

    print("\n--- Signal Sources Connected ---")
    for source in router.adapters:
        print(f"  [{source.value}] {router.adapters[source].__class__.__name__}")

    print("\n--- Submitting Test Signals ---")

    # Submit a ChatGPT signal
    router.submit_ai_signal(
        market_id="trump-2024-election",
        side="YES",
        fair_price=0.65,
        confidence=0.80,
        reasoning="ChatGPT analysis shows market underpricing",
        provider=AIProvider.CHATGPT
    )

    # Submit a Yair insight
    router.submit_yair_insight("buy YES on btc-100k market, looks good")
    router.submit_yair_insight("avoid crypto markets this week - too volatile")

    print("\n--- Running Collection Cycle ---")
    result = router.run_cycle()

    print("\n--- Cycle Result ---")
    print(f"Total signals: {result.total_signals}")
    print(f"Passed filters: {result.passed_filters}")
    print(f"Vetoed: {result.vetoed}")
    print(f"Routed to executor: {result.routed_to_executor}")

    if result.signals:
        print("\nTop signals:")
        for d in result.signals[:5]:
            veto_str = "[VETOED]" if d.vetoed else ""
            mod_str = "[MOD]" if d.modifier_applied else ""
            print(f"  {d.signal.market_id}: {d.signal.side} @ {d.final_edge:.1%} {veto_str}{mod_str}")

    print("\n" + "=" * 60)
    print("Router initialized successfully!")
    print("To start continuous mode: router.start_continuous()")
    print("=" * 60)


if __name__ == '__main__':
    main()
