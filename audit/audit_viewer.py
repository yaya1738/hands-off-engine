#!/usr/bin/env python3
"""
Audit log viewer and analysis tool
"""
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from audit_logger import AuditLogger


def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp for display"""
    dt = datetime.fromisoformat(iso_timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def format_currency(amount: float) -> str:
    """Format currency for display"""
    return f"${amount:,.2f}"


def print_event(event, show_metadata: bool = False):
    """Pretty print an audit event"""
    print(f"\n{'='*80}")
    print(f"Event ID:   {event.event_id}")
    print(f"Time:       {format_timestamp(event.timestamp)}")
    print(f"Component:  {event.component}")
    print(f"Action:     {event.action}")

    if event.cost:
        print(f"Cost:       {format_currency(event.cost)}")
    if event.revenue:
        print(f"Revenue:    {format_currency(event.revenue)}")
        if event.cost:
            profit = event.revenue - event.cost
            print(f"Profit:     {format_currency(profit)}")

    if event.outcome:
        print(f"Outcome:    {event.outcome}")
    if event.error:
        print(f"Error:      {event.error}")

    if show_metadata and event.metadata:
        print(f"\nMetadata:")
        for key, value in event.metadata.items():
            print(f"  {key}: {value}")


def print_summary(summary: dict):
    """Pretty print session summary"""
    print(f"\n{'='*80}")
    print("SESSION SUMMARY")
    print(f"{'='*80}")
    print(f"\nSession ID: {summary['session_id']}")
    print(f"Total Events: {summary['total_events']}")

    if summary['start_time']:
        print(f"Start Time: {format_timestamp(summary['start_time'])}")
    if summary['end_time']:
        print(f"End Time: {format_timestamp(summary['end_time'])}")

    print(f"\n{'-'*80}")
    print("FINANCIAL SUMMARY")
    print(f"{'-'*80}")
    print(f"Total Cost:    {format_currency(summary['total_cost'])}")
    print(f"Total Revenue: {format_currency(summary['total_revenue'])}")
    print(f"Net Profit:    {format_currency(summary['net_profit'])}")
    print(f"ROI:           {summary['roi']:.2f}%")

    if summary['component_stats']:
        print(f"\n{'-'*80}")
        print("COMPONENT BREAKDOWN")
        print(f"{'-'*80}")

        for component, stats in summary['component_stats'].items():
            print(f"\n{component}:")
            print(f"  Events:  {stats['event_count']}")
            print(f"  Cost:    {format_currency(stats['cost'])}")
            print(f"  Revenue: {format_currency(stats['revenue'])}")
            print(f"  Errors:  {stats['errors']}")


def main():
    parser = argparse.ArgumentParser(
        description="View and analyze audit logs"
    )
    parser.add_argument(
        "--component",
        help="Filter by component (e.g., ai.claude, trading.polymarket)"
    )
    parser.add_argument(
        "--session",
        help="Filter by session ID"
    )
    parser.add_argument(
        "--list-sessions",
        action="store_true",
        help="List all available session IDs"
    )
    parser.add_argument(
        "--all-sessions",
        action="store_true",
        help="Show summary for all sessions"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show session summary instead of individual events"
    )
    parser.add_argument(
        "--metadata",
        action="store_true",
        help="Show event metadata (verbose)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of events to show (default: 50)"
    )
    parser.add_argument(
        "--log-dir",
        default="audit/logs",
        help="Audit log directory (default: audit/logs)"
    )

    args = parser.parse_args()

    # Initialize logger
    logger = AuditLogger(log_dir=args.log_dir)

    # Handle list sessions
    if args.list_sessions:
        session_ids = logger.get_all_sessions()
        if not session_ids:
            print("No sessions found.")
            return
        
        print(f"\nFound {len(session_ids)} session(s):\n")
        for session_id in session_ids:
            # Get basic info about each session
            summary = logger.get_session_summary(session_id)
            print(f"Session: {session_id}")
            print(f"  Events: {summary['total_events']}")
            if summary['start_time']:
                print(f"  Start:  {format_timestamp(summary['start_time'])}")
            if summary['end_time']:
                print(f"  End:    {format_timestamp(summary['end_time'])}")
            print(f"  Cost:   {format_currency(summary['total_cost'])}")
            print(f"  Revenue: {format_currency(summary['total_revenue'])}")
            print(f"  Profit: {format_currency(summary['net_profit'])}")
            print()
        return

    # Handle all sessions summary
    if args.all_sessions:
        session_ids = logger.get_all_sessions()
        if not session_ids:
            print("No sessions found.")
            return
        
        print(f"\nGenerating summaries for {len(session_ids)} session(s)...\n")
        for session_id in session_ids:
            summary = logger.get_session_summary(session_id)
            print_summary(summary)
            print("\n")
        return

    if args.summary:
        # Show summary
        if args.session:
            summary = logger.get_session_summary(args.session)
        else:
            summary = logger.get_session_summary()
        print_summary(summary)
    else:
        # Show events
        events = logger.get_events(
            component=args.component,
            session_id=args.session
        )

        if not events:
            print("No events found matching criteria.")
            return

        print(f"\nFound {len(events)} events")

        # Show latest events first
        events.reverse()

        for event in events[:args.limit]:
            print_event(event, show_metadata=args.metadata)

        if len(events) > args.limit:
            print(f"\n... and {len(events) - args.limit} more events")
            print(f"Use --limit to see more events")


if __name__ == "__main__":
    main()
