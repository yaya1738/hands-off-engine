"""
reports module

Read-only reporting utilities for Hands-Off DRYRUN pipelines.
"""

from .ho_polymarket_report import render_polymarket_report, run_polymarket_pipeline_and_report

__all__ = ["render_polymarket_report", "run_polymarket_pipeline_and_report"]
