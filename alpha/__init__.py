"""
Alpha Module: Unified Signal Sources for Automated Trading
==========================================================

This module provides all alpha signal sources for the Hands-Off Engine:

1. integrations_hub - Central hub that orchestrates all signal sources
2. espn_live_alpha - Live game alpha (destroy Polymarket during live games)
3. commercial_ai_receiver - Mispricing signals from ChatGPT, Claude, etc.
4. yair_insights - Golden sprinkle human expert insights
5. signal_router - Unified router that connects everything to the executor

Quick Start:
    from alpha.signal_router import UnifiedSignalRouter, ExecutionMode

    router = UnifiedSignalRouter(execution_mode=ExecutionMode.DRYRUN)

    # Submit signals from various sources
    router.submit_ai_signal("market-id", "YES", fair_price=0.65)
    router.submit_yair_insight("buy YES on market, looks good")

    # Run a collection cycle
    result = router.run_cycle()

For continuous operation:
    router.start_continuous(interval_seconds=60)
"""

from alpha.integrations_hub import (
    IntegrationsHub,
    SignalSource,
    SignalUrgency,
    UnifiedAlphaSignal,
    AlphaSourceAdapter,
    create_signal
)

from alpha.signal_router import (
    UnifiedSignalRouter,
    ExecutionMode,
    RoutingDecision,
    CycleResult
)

__all__ = [
    # Hub
    'IntegrationsHub',
    'SignalSource',
    'SignalUrgency',
    'UnifiedAlphaSignal',
    'AlphaSourceAdapter',
    'create_signal',
    # Router
    'UnifiedSignalRouter',
    'ExecutionMode',
    'RoutingDecision',
    'CycleResult'
]
