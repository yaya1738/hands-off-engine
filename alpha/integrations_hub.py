#!/usr/bin/env python3
"""
Alpha Integrations Hub: Central Orchestrator for All Signal Sources
====================================================================

This is the brain that connects ALL alpha sources:
- Polymarket native signals (existing)
- ESPN live game alpha (new)
- Commercial AI mispricing detection (new)
- Yair's golden sprinkle insights (new)
- Any future alpha sources

The hub normalizes all signals to the canonical format and routes them
to the Decider for automated execution.

Philosophy: "Hook everything together for optimal wealth extraction"
"""

import json
import sys
import os
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod

# Add parent directory for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from audit import get_audit_logger
except ImportError:
    get_audit_logger = None

try:
    from ai_nexus.history_log import log_kernel_history_event
except ImportError:
    log_kernel_history_event = None


class SignalSource(Enum):
    """Enumeration of all alpha signal sources"""
    POLYMARKET_NATIVE = "polymarket_native"      # Existing edge detection
    ESPN_LIVE = "espn_live"                       # Live game destruction mode
    COMMERCIAL_AI = "commercial_ai"               # ChatGPT, Claude, etc. mispricing
    YAIR_INSIGHTS = "yair_insights"               # Golden sprinkle human intel
    ODDS_ARBITRAGE = "odds_arbitrage"             # Cross-platform arb (future)
    NEWS_SENTIMENT = "news_sentiment"             # News-driven alpha (future)


class SignalUrgency(Enum):
    """How quickly the signal needs to be acted on"""
    IMMEDIATE = "immediate"    # Live game - act NOW (seconds)
    HIGH = "high"              # Time-sensitive - act within minutes
    NORMAL = "normal"          # Standard - act within hours
    LOW = "low"                # Research phase - no rush


@dataclass
class UnifiedAlphaSignal:
    """
    Canonical alpha signal format that ALL sources output.
    This is the lingua franca of the integrations hub.
    """
    # Identity
    signal_id: str                    # Unique identifier for this signal
    source: SignalSource              # Where this signal came from
    timestamp: str                    # ISO 8601 UTC timestamp

    # Market targeting
    market_id: str                    # Polymarket market slug
    market_name: str                  # Human-readable market question
    market_category: str              # sports, politics, crypto, etc.

    # Trading signal
    side: str                         # "YES" or "NO"
    fair_price: float                 # Model's estimated fair probability
    market_price: float               # Current market price
    edge: float                       # fair_price - market_price (or abs)
    confidence: float                 # 0.0 to 1.0

    # Execution hints
    urgency: SignalUrgency            # How fast to act
    max_stake_usd: Optional[float]    # Suggested max stake
    liquidity: Optional[float]        # Market liquidity estimate

    # Context
    reasoning: str                    # Why this is a good trade
    raw_data: Optional[Dict]          # Original source data

    def to_dict(self) -> Dict:
        """Convert to dictionary with enum handling"""
        d = asdict(self)
        d['source'] = self.source.value
        d['urgency'] = self.urgency.value
        return d

    def to_model_format(self) -> Dict:
        """Convert to polymarket-model.json format for Decider compatibility"""
        return {
            'market_id': self.market_id,
            'question': self.market_name,
            'query_category': self.market_category,
            'side': self.side,
            'model_edge': self.edge,
            'model_confidence': self.confidence,
            'fair_price': self.fair_price,
            'market_price': self.market_price,
            'best_bid': self.market_price - 0.02,  # Estimate
            'liquidity': self.liquidity or 1000.0,
            'signal_source': self.source.value,
            'urgency': self.urgency.value,
            'reasoning': self.reasoning
        }


class AlphaSourceAdapter(ABC):
    """
    Abstract base class for alpha source adapters.
    Each signal source implements this interface.
    """

    @property
    @abstractmethod
    def source_type(self) -> SignalSource:
        """Return the source type for this adapter"""
        pass

    @abstractmethod
    def fetch_signals(self) -> List[UnifiedAlphaSignal]:
        """Fetch and return normalized signals from this source"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this source is currently available"""
        pass


class IntegrationsHub:
    """
    Central hub that orchestrates all alpha sources.

    This is the conductor that:
    1. Collects signals from all adapters
    2. Normalizes and validates them
    3. Applies priority/urgency sorting
    4. Routes to the unified signal queue
    5. Logs everything for audit trail
    """

    def __init__(self, state_dir: Path = None):
        self.state_dir = state_dir or Path(__file__).parent.parent / 'state'
        self.adapters: Dict[SignalSource, AlphaSourceAdapter] = {}
        self.signal_queue: List[UnifiedAlphaSignal] = []

        # Audit logging
        if get_audit_logger:
            self.audit = get_audit_logger(component="integrations_hub")
        else:
            self.audit = None

        # Output paths
        self.unified_signals_path = self.state_dir / 'unified-alpha-signals.json'
        self.signal_history_path = self.state_dir / 'alpha-signal-history.jsonl'

        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def register_adapter(self, adapter: AlphaSourceAdapter):
        """Register an alpha source adapter"""
        self.adapters[adapter.source_type] = adapter
        print(f"[Hub] Registered adapter: {adapter.source_type.value}")

    def collect_all_signals(self, sources: List[SignalSource] = None) -> List[UnifiedAlphaSignal]:
        """
        Collect signals from all (or specified) adapters.

        Args:
            sources: Optional list of sources to collect from.
                    If None, collects from all registered adapters.

        Returns:
            List of unified alpha signals, sorted by urgency then edge
        """
        all_signals = []

        sources_to_query = sources or list(self.adapters.keys())

        for source in sources_to_query:
            adapter = self.adapters.get(source)
            if not adapter:
                print(f"[Hub] Warning: No adapter for {source.value}")
                continue

            if not adapter.is_available():
                print(f"[Hub] {source.value} not available, skipping")
                continue

            try:
                signals = adapter.fetch_signals()
                all_signals.extend(signals)
                print(f"[Hub] Collected {len(signals)} signals from {source.value}")
            except Exception as e:
                print(f"[Hub] Error collecting from {source.value}: {e}")
                if self.audit:
                    self.audit.log_error(
                        error_type="signal_collection_failed",
                        error_message=str(e),
                        context={"source": source.value}
                    )

        # Sort by urgency (IMMEDIATE first), then by edge (highest first)
        urgency_order = {
            SignalUrgency.IMMEDIATE: 0,
            SignalUrgency.HIGH: 1,
            SignalUrgency.NORMAL: 2,
            SignalUrgency.LOW: 3
        }

        all_signals.sort(key=lambda s: (urgency_order[s.urgency], -s.edge))

        self.signal_queue = all_signals
        return all_signals

    def filter_signals(
        self,
        signals: List[UnifiedAlphaSignal] = None,
        min_edge: float = 0.03,
        min_confidence: float = 0.5,
        max_signals: int = 20,
        urgency_filter: List[SignalUrgency] = None
    ) -> List[UnifiedAlphaSignal]:
        """
        Filter signals based on quality thresholds.

        Args:
            signals: Signals to filter (uses queue if None)
            min_edge: Minimum edge threshold (default 3%)
            min_confidence: Minimum confidence (default 50%)
            max_signals: Maximum signals to return
            urgency_filter: Only include these urgency levels

        Returns:
            Filtered list of signals
        """
        signals = signals or self.signal_queue

        filtered = []
        for signal in signals:
            # Edge filter
            if signal.edge < min_edge:
                continue

            # Confidence filter
            if signal.confidence < min_confidence:
                continue

            # Urgency filter
            if urgency_filter and signal.urgency not in urgency_filter:
                continue

            filtered.append(signal)

        return filtered[:max_signals]

    def export_to_model_format(
        self,
        signals: List[UnifiedAlphaSignal] = None,
        output_path: Path = None
    ) -> Dict:
        """
        Export signals to polymarket-model.json format for Decider consumption.

        This maintains backwards compatibility with the existing pipeline.
        """
        signals = signals or self.signal_queue
        output_path = output_path or self.unified_signals_path

        model = {
            'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'hub_version': '1.0.0',
            'total_signals': len(signals),
            'sources_used': list(set(s.source.value for s in signals)),
            'markets': [s.to_model_format() for s in signals]
        }

        # Write atomically
        output_tmp = output_path.with_suffix('.tmp')
        with open(output_tmp, 'w') as f:
            json.dump(model, f, indent=2)
        output_tmp.replace(output_path)

        return model

    def append_to_history(self, signals: List[UnifiedAlphaSignal]):
        """Append signals to history log for analysis"""
        with open(self.signal_history_path, 'a') as f:
            for signal in signals:
                entry = signal.to_dict()
                entry['logged_at'] = datetime.now(timezone.utc).isoformat()
                f.write(json.dumps(entry) + '\n')

    def get_immediate_signals(self) -> List[UnifiedAlphaSignal]:
        """Get signals that need immediate action (live games, etc.)"""
        return [s for s in self.signal_queue if s.urgency == SignalUrgency.IMMEDIATE]

    def run_collection_cycle(
        self,
        export_model: bool = True,
        log_history: bool = True
    ) -> Dict:
        """
        Run a full collection cycle:
        1. Collect from all sources
        2. Filter by quality
        3. Export to model format
        4. Log to history
        5. Return summary
        """
        print("\n" + "="*60)
        print("[Hub] Starting signal collection cycle")
        print("="*60 + "\n")

        # Collect all signals
        all_signals = self.collect_all_signals()
        print(f"\n[Hub] Total signals collected: {len(all_signals)}")

        # Filter for quality
        filtered = self.filter_signals(all_signals)
        print(f"[Hub] Signals after filtering: {len(filtered)}")

        # Check for immediate signals
        immediate = self.get_immediate_signals()
        if immediate:
            print(f"\n*** IMMEDIATE ACTION REQUIRED: {len(immediate)} signals ***")
            for sig in immediate:
                print(f"  - {sig.market_name[:50]}... | {sig.side} @ {sig.edge:.1%} edge")

        # Export
        if export_model and filtered:
            model = self.export_to_model_format(filtered)
            print(f"\n[Hub] Exported to: {self.unified_signals_path}")
        else:
            model = {'markets': []}

        # Log history
        if log_history and filtered:
            self.append_to_history(filtered)

        # Audit log
        if self.audit:
            self.audit.log_data_fetch(
                data_source="integrations_hub",
                data_type="unified_signals",
                record_count=len(filtered),
                context={
                    'sources': [s.source.value for s in filtered],
                    'immediate_count': len(immediate)
                }
            )

        # Log to Spark Plug kernels
        if log_kernel_history_event and filtered:
            try:
                log_kernel_history_event(
                    kernel_ids=["alpha_polymarket_core", "trading_philosophy"],
                    kind="signal_collection",
                    source="integrations_hub",
                    summary=f"Hub collected {len(all_signals)} signals, filtered to {len(filtered)}, {len(immediate)} immediate",
                    details={
                        "total_collected": len(all_signals),
                        "after_filter": len(filtered),
                        "immediate_count": len(immediate),
                        "sources": list(set(s.source.value for s in filtered)),
                        "top_edge": max((s.edge for s in filtered), default=0)
                    },
                    importance=6,
                    tags=["hub", "alpha", "collection"]
                )
            except Exception:
                pass

        summary = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_collected': len(all_signals),
            'after_filter': len(filtered),
            'immediate_count': len(immediate),
            'sources_active': list(self.adapters.keys()),
            'exported': export_model
        }

        print("\n[Hub] Collection cycle complete")
        print("="*60 + "\n")

        return summary


# ============================================================================
# Utility functions for creating signals from various sources
# ============================================================================

def create_signal(
    market_id: str,
    market_name: str,
    source: SignalSource,
    side: str,
    fair_price: float,
    market_price: float,
    confidence: float,
    urgency: SignalUrgency = SignalUrgency.NORMAL,
    category: str = "general",
    reasoning: str = "",
    raw_data: Dict = None
) -> UnifiedAlphaSignal:
    """
    Factory function to create a UnifiedAlphaSignal with defaults.
    """
    edge = abs(fair_price - market_price)

    return UnifiedAlphaSignal(
        signal_id=f"{source.value}_{market_id}_{int(datetime.now().timestamp())}",
        source=source,
        timestamp=datetime.now(timezone.utc).isoformat(),
        market_id=market_id,
        market_name=market_name,
        market_category=category,
        side=side,
        fair_price=fair_price,
        market_price=market_price,
        edge=edge,
        confidence=confidence,
        urgency=urgency,
        max_stake_usd=None,
        liquidity=None,
        reasoning=reasoning or f"Signal from {source.value}: {side} with {edge:.1%} edge",
        raw_data=raw_data
    )


# ============================================================================
# Main entry point
# ============================================================================

def main():
    """Demo/test the integrations hub"""
    print("Alpha Integrations Hub")
    print("=" * 40)

    hub = IntegrationsHub()

    # Without any adapters registered, this will be empty
    # The actual adapters are in separate files:
    # - espn_live_alpha.py
    # - commercial_ai_receiver.py
    # - yair_insights.py

    print("\nNo adapters registered yet.")
    print("Register adapters using hub.register_adapter()")
    print("\nAvailable signal sources:")
    for source in SignalSource:
        print(f"  - {source.value}")


if __name__ == '__main__':
    main()
