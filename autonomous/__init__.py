"""
Autonomous Systems - Complete Self-Managing Infrastructure

The unified autonomous system that manages ALL infrastructure
without user intervention.

Components:
- unified_system: Master controller combining hardware + infrastructure
- Integration with approval queue for business decisions
- Trading protection at all times

Usage:
    # Start the live autonomous system
    from autonomous import start_live_system
    start_live_system(budget=500, dry_run=False)

    # Or from command line:
    python -m autonomous.unified_system --budget 500

Standard: Yair Siegel Master Level Operations - Full Self-Control
"""

from autonomous.unified_system import (
    UnifiedAutonomousSystem,
    start_live_system,
)

__all__ = [
    'UnifiedAutonomousSystem',
    'start_live_system',
]
