"""
INTEGRAFIX - The Integration Framework
======================================

Everything exists. Nothing was connected.
Now it is.

COMPONENTS:
- methodology.py      - The science of wiring islands
- fair_price_estimator.py - Breaking circular edge detection
- process_coordinator.py  - Wiring blind processes
- trading_pipeline.py     - End-to-end trading flow
- ai_memory.py           - Continuity across AI sessions
- cron_coordinator.py    - Coordinating autonomous jobs
- recursive_engine.py    - Master integrator

USAGE:
    from integrafix.recursive_engine import get_engine
    engine = get_engine()
    engine.run_cycle()

THE EQUATION:
    Integration = Σ(connections) / Σ(potential_connections)

    When Integration → 1.0, the system becomes whole.

Created: 2024-12-03
Author: Claude (with Yair)
"""

__version__ = "1.0.0"

# Quick imports
from integrafix.methodology import get_methodology, IntegrafixMethodology
from integrafix.fair_price_estimator import get_estimator, FairPriceEstimator
from integrafix.process_coordinator import get_coordinator, ProcessCoordinator
from integrafix.trading_pipeline import get_pipeline, TradingPipeline
from integrafix.ai_memory import get_memory, AIMemory
from integrafix.cron_coordinator import get_coordinator as get_cron_coordinator
from integrafix.recursive_engine import get_engine, RecursiveIntegrafixEngine

__all__ = [
    "get_methodology",
    "get_estimator",
    "get_coordinator",
    "get_pipeline",
    "get_memory",
    "get_cron_coordinator",
    "get_engine",
    "IntegrafixMethodology",
    "FairPriceEstimator",
    "ProcessCoordinator",
    "TradingPipeline",
    "AIMemory",
    "RecursiveIntegrafixEngine",
]
