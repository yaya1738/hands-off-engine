#!/usr/bin/env python3
"""
Quick Finance Summary Script

Provides a unified view of all financial data using the FinanceHub.
Can be run directly or imported.

Usage:
    python3 hofinance_unified.py          # Human-readable summary
    python3 hofinance_unified.py --json   # JSON output
"""

import sys
import os

# Add the repository root to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
sys.path.insert(0, repo_root)

from business.finance_hub import FinanceHub, main

if __name__ == "__main__":
    main()
