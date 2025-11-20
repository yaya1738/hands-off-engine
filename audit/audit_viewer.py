#!/usr/bin/env python3
"""
Audit Log Viewer for Hands-Off Engine

Query and view audit logs with filtering and formatting options.

Usage:
    audit_viewer.py [--date DATE] [--component COMPONENT] [--event-type TYPE] [--session SESSION] [--tail N]

Examples:
    # View today's logs
    audit_viewer.py
    
    # View logs from specific date
    audit_viewer.py --date 2025-11-20
    
    # Filter by component
    audit_viewer.py --component edge_engine
    
    # Filter by event type
    audit_viewer.py --event-type edge_detection
    
    # Show last 50 entries
    audit_viewer.py --tail 50
    
    # Combine filters
    audit_viewer.py --date 2025-11-20 --event-type order --component executor
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional


def find_audit_logs() -> Path:
    """Find the audit logs directory"""
    # Try multiple possible locations
    locations = [
        Path.home() / "hands-off" / "audit",
        Path(__file__).parent.parent / "logs" / "audit",
        Path("logs") / "audit",
    ]
    
    for loc in locations:
        if loc.exists():
            return loc
    
    # Default to first location if none exist
    return locations[0]


def load_audit_entries(log_dir: Path, date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load audit entries from log files"""
    entries = []
    
    if date:
        # Load specific date
        log_file = log_dir / f"audit_{date}.jsonl"
        if log_file.exists():
            with open(log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
    else:
        # Load all available logs, sorted by date
        log_files = sorted(log_dir.glob("audit_*.jsonl"))
        for log_file in log_files:
            with open(log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
    
    return entries


def filter_entries(entries: List[Dict[str, Any]], 
                  component: Optional[str] = None,
                  event_type: Optional[str] = None,
                  session_id: Optional[str] = None,
                  severity: Optional[str] = None) -> List[Dict[str, Any]]:
    """Filter audit entries based on criteria"""
    filtered = entries
    
    if component:
        filtered = [e for e in filtered if e.get('component', '').lower() == component.lower()]
    
    if event_type:
        filtered = [e for e in filtered if e.get('event_type', '').lower() == event_type.lower()]
    
    if session_id:
        filtered = [e for e in filtered if e.get('session_id', '') == session_id]
    
    if severity:
        filtered = [e for e in filtered if e.get('severity', '').lower() == severity.lower()]
    
    return filtered


def format_entry(entry: Dict[str, Any], verbose: bool = False) -> str:
    """Format an audit entry for display"""
    timestamp = entry.get('timestamp', 'N/A')
    event_type = entry.get('event_type', 'unknown')
    component = entry.get('component', 'unknown')
    severity = entry.get('severity', 'info')
    
    # Color codes
    severity_colors = {
        'debug': '\033[90m',    # gray
        'info': '\033[0m',      # white
        'warning': '\033[93m',  # yellow
        'error': '\033[91m',    # red
        'critical': '\033[95m'  # magenta
    }
    reset = '\033[0m'
    color = severity_colors.get(severity, reset)
    
    # Format header
    header = f"{color}[{timestamp}] {event_type.upper()} ({component}) [{severity}]{reset}"
    
    if not verbose:
        # Compact format - just show key info
        data = entry.get('data', {})
        if event_type == 'edge_detection':
            market = data.get('market', 'unknown')
            edge = data.get('edge', 0)
            action = data.get('action', 'N/A')
            return f"{header}\n  Market: {market}, Edge: {edge:+.3f}, Action: {action}"
        
        elif event_type == 'order':
            market = data.get('market', 'unknown')
            side = data.get('side', 'N/A')
            size = data.get('size', 0)
            dryrun = data.get('dryrun', True)
            mode = "DRYRUN" if dryrun else "LIVE"
            return f"{header}\n  Order: {side} {size} on {market} [{mode}]"
        
        elif event_type == 'decision':
            decision_type = data.get('decision_type', 'unknown')
            outputs = data.get('outputs', {})
            return f"{header}\n  Decision: {decision_type}, Outputs: {json.dumps(outputs)}"
        
        elif event_type == 'data_fetch':
            source = data.get('source', 'unknown')
            success = data.get('success', False)
            count = data.get('record_count', 0)
            status = "✓" if success else "✗"
            return f"{header}\n  Fetch {status}: {source} ({count} records)"
        
        else:
            # Generic format
            return f"{header}\n  Data: {json.dumps(data, indent=2)}"
    else:
        # Verbose format - show full entry
        return f"{header}\n{json.dumps(entry, indent=2)}"


def main():
    parser = argparse.ArgumentParser(
        description="View and query Hands-Off Engine audit logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--date', '-d', help='Filter by date (YYYY-MM-DD)')
    parser.add_argument('--component', '-c', help='Filter by component name')
    parser.add_argument('--event-type', '-e', help='Filter by event type')
    parser.add_argument('--session', '-s', help='Filter by session ID')
    parser.add_argument('--severity', help='Filter by severity (debug, info, warning, error, critical)')
    parser.add_argument('--tail', '-n', type=int, help='Show last N entries')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show full entry details')
    parser.add_argument('--list-components', action='store_true', help='List all components in logs')
    parser.add_argument('--list-event-types', action='store_true', help='List all event types in logs')
    parser.add_argument('--stats', action='store_true', help='Show statistics about logs')
    
    args = parser.parse_args()
    
    # Find audit log directory
    log_dir = find_audit_logs()
    if not log_dir.exists():
        print(f"Error: Audit log directory not found: {log_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Load entries
    entries = load_audit_entries(log_dir, args.date)
    
    if not entries:
        print(f"No audit logs found in {log_dir}")
        if args.date:
            print(f"  (filtered by date: {args.date})")
        sys.exit(0)
    
    # Handle special commands
    if args.list_components:
        components = sorted(set(e.get('component', 'unknown') for e in entries))
        print("Components:")
        for comp in components:
            count = sum(1 for e in entries if e.get('component') == comp)
            print(f"  {comp}: {count} events")
        sys.exit(0)
    
    if args.list_event_types:
        event_types = sorted(set(e.get('event_type', 'unknown') for e in entries))
        print("Event Types:")
        for et in event_types:
            count = sum(1 for e in entries if e.get('event_type') == et)
            print(f"  {et}: {count} events")
        sys.exit(0)
    
    if args.stats:
        print(f"Audit Log Statistics:")
        print(f"  Total entries: {len(entries)}")
        print(f"  Date range: {entries[0].get('timestamp', 'N/A')} to {entries[-1].get('timestamp', 'N/A')}")
        
        components = set(e.get('component', 'unknown') for e in entries)
        print(f"  Components: {len(components)}")
        
        event_types = set(e.get('event_type', 'unknown') for e in entries)
        print(f"  Event types: {len(event_types)}")
        
        severities = {}
        for e in entries:
            sev = e.get('severity', 'info')
            severities[sev] = severities.get(sev, 0) + 1
        print(f"  By severity:")
        for sev, count in sorted(severities.items()):
            print(f"    {sev}: {count}")
        
        sys.exit(0)
    
    # Filter entries
    entries = filter_entries(
        entries,
        component=args.component,
        event_type=args.event_type,
        session_id=args.session,
        severity=args.severity
    )
    
    if not entries:
        print("No entries match the specified filters")
        sys.exit(0)
    
    # Apply tail
    if args.tail:
        entries = entries[-args.tail:]
    
    # Display entries
    print(f"Showing {len(entries)} audit log entries:")
    print("-" * 80)
    for entry in entries:
        print(format_entry(entry, verbose=args.verbose))
        print()


if __name__ == "__main__":
    main()
