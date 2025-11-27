"""
Business Integration Package for Hands-Off Engine

This package provides unified access to all financial and business data.
"""

from .finance_hub import (
    FinanceHub,
    FinancialSummary,
    AccountBalance,
    CreditCard,
    TradingPosition,
)

__all__ = [
    "FinanceHub",
    "FinancialSummary",
    "AccountBalance",
    "CreditCard",
    "TradingPosition",
]

__version__ = "1.0.0"
