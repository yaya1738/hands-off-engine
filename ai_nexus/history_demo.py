"""
History Demo CLI v0.1 (Part 3: User Expansion)

Simple CLI to demonstrate history event logging.

Usage:
    # Interactive mode
    python -m ai_nexus.history_demo

    # Log a quick event
    python -m ai_nexus.history_demo log --type user_message --source "user:froggy" --content "What's the Kelly fraction?"

    # Show recent history
    python -m ai_nexus.history_demo show --limit 10

    # Show stats
    python -m ai_nexus.history_demo stats
"""

import sys
import argparse
from datetime import datetime

from ai_nexus.spark_plug_types import create_history_event
from ai_nexus.history_logger import (
    append_history_event,
    load_history_events,
    get_history_stats,
    get_event_types,
    count_history_events
)


# =============================================================================
# CLI Commands
# =============================================================================

def cmd_interactive():
    """Interactive mode: prompt user for event details"""
    print("=" * 60)
    print("History Event Logger - Interactive Mode")
    print("=" * 60)
    print()

    # Get event type
    print("Event Types:")
    print("  1. user_message")
    print("  2. system_decision")
    print("  3. trade_outcome")
    print("  4. model_update")
    print("  5. manual_override")
    print("  6. cpu_conclusion")
    print("  7. observation")
    print("  8. other")
    print()

    type_choice = input("Choose event type (1-8): ").strip()
    type_map = {
        "1": "user_message",
        "2": "system_decision",
        "3": "trade_outcome",
        "4": "model_update",
        "5": "manual_override",
        "6": "cpu_conclusion",
        "7": "observation",
        "8": "other"
    }
    event_type = type_map.get(type_choice, "other")

    # Get source
    source = input("Source (e.g., 'user:froggy', 'cpu_risk_01'): ").strip()
    if not source:
        source = "unknown"

    # Get content
    print("Content (multi-line supported, end with empty line):")
    content_lines = []
    while True:
        line = input()
        if not line:
            break
        content_lines.append(line)
    content = "\n".join(content_lines)

    if not content:
        print("Error: Content cannot be empty")
        sys.exit(1)

    # Get optional context
    print("\nOptional context (key=value pairs, one per line, empty to finish):")
    context = {}
    while True:
        line = input().strip()
        if not line:
            break
        if "=" in line:
            key, value = line.split("=", 1)
            context[key.strip()] = value.strip()

    # Create and log event
    event = create_history_event(
        event_type=event_type,
        source=source,
        content=content,
        **context
    )

    append_history_event(event)

    print()
    print("✓ Event logged successfully!")
    print(f"  Event ID: {event.event_id}")
    print(f"  Timestamp: {event.timestamp}")
    print()


def cmd_log(args):
    """Log event from command-line arguments"""
    if not args.content:
        print("Error: --content is required")
        sys.exit(1)

    # Parse context from key=value pairs
    context = {}
    if args.context:
        for pair in args.context:
            if "=" in pair:
                key, value = pair.split("=", 1)
                context[key.strip()] = value.strip()

    event = create_history_event(
        event_type=args.type,
        source=args.source,
        content=args.content,
        **context
    )

    append_history_event(event)

    print(f"✓ Event logged: {event.event_id}")


def cmd_show(args):
    """Show recent history events"""
    events = load_history_events(
        limit=args.limit,
        event_type=args.type if hasattr(args, 'type') else None
    )

    if not events:
        print("No history events found.")
        return

    print(f"Recent History ({len(events)} events)")
    print("=" * 70)
    print()

    for event in events:
        print(f"[{event.timestamp}]")
        print(f"  Type: {event.event_type}")
        print(f"  Source: {event.source}")
        print(f"  Content: {event.content[:80]}{'...' if len(event.content) > 80 else ''}")
        if event.context:
            print(f"  Context: {event.context}")
        print()


def cmd_stats(args):
    """Show history statistics"""
    stats = get_history_stats()

    print("History Statistics")
    print("=" * 50)
    print()
    print(f"Total Events: {stats['total_events']}")
    print()

    if stats['total_events'] > 0:
        print("Event Types:")
        for event_type, count in stats['event_types'].items():
            print(f"  {event_type}: {count}")
        print()
        print(f"Oldest Event: {stats['oldest_timestamp']}")
        print(f"Newest Event: {stats['newest_timestamp']}")
    print()


def cmd_types(args):
    """Show all event types in history"""
    types = get_event_types()

    print("Event Types in History")
    print("=" * 50)
    print()

    if not types:
        print("No events found.")
        return

    for event_type in types:
        count = count_history_events(event_type=event_type)
        print(f"  {event_type}: {count} events")

    print()


# =============================================================================
# Main CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="History Event Logger Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python -m ai_nexus.history_demo

  # Log a user message
  python -m ai_nexus.history_demo log --type user_message --source "user:froggy" --content "What's the Kelly fraction?"

  # Log with context
  python -m ai_nexus.history_demo log --type system_decision --source "cpu_risk_01" --content "Updated Kelly to 0.15" --context kernel_id=risk_v2

  # Show last 20 events
  python -m ai_nexus.history_demo show --limit 20

  # Show statistics
  python -m ai_nexus.history_demo stats
        """
    )

    subparsers = parser.add_subparsers(dest="command")

    # Interactive command (default)
    parser_interactive = subparsers.add_parser("interactive", help="Interactive mode")

    # Log command
    parser_log = subparsers.add_parser("log", help="Log an event")
    parser_log.add_argument("--type", default="other", help="Event type (default: other)")
    parser_log.add_argument("--source", default="manual", help="Event source (default: manual)")
    parser_log.add_argument("--content", required=True, help="Event content")
    parser_log.add_argument("--context", nargs="*", help="Context as key=value pairs")

    # Show command
    parser_show = subparsers.add_parser("show", help="Show recent events")
    parser_show.add_argument("--limit", type=int, default=10, help="Number of events to show")
    parser_show.add_argument("--type", help="Filter by event type")

    # Stats command
    parser_stats = subparsers.add_parser("stats", help="Show statistics")

    # Types command
    parser_types = subparsers.add_parser("types", help="Show all event types")

    args = parser.parse_args()

    # Handle commands
    if args.command == "log":
        cmd_log(args)
    elif args.command == "show":
        cmd_show(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "types":
        cmd_types(args)
    elif args.command == "interactive":
        cmd_interactive()
    else:
        # Default to interactive if no command given
        cmd_interactive()


if __name__ == "__main__":
    main()
