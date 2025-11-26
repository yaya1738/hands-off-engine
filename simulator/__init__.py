"""
Simulator package for Hands-Off Engine

Provides backtesting and simulation capabilities for testing strategies
"""

from .market import MarketSimulator
from .executor import ExecutionSimulator
from .backtest import BacktestEngine
from .metrics import PerformanceMetrics
from .reports import ReportGenerator

__all__ = [
    'MarketSimulator',
    'ExecutionSimulator', 
    'BacktestEngine',
    'PerformanceMetrics',
    'ReportGenerator'
]
