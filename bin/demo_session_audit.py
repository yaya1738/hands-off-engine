#!/usr/bin/env python3
"""
Demonstration script for agent session audit functionality

This script shows how to:
1. List all agent sessions
2. Get summaries for individual sessions
3. Get summaries for all sessions
"""
import sys
from pathlib import Path

# Add audit directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "audit"))

from audit_logger import AuditLogger


def demonstrate_session_audit():
    """Demonstrate the session audit functionality"""
    
    print("=" * 80)
    print("AGENT SESSION AUDIT DEMONSTRATION")
    print("=" * 80)
    
    # Initialize logger
    logger = AuditLogger(log_dir="audit/logs")
    
    # 1. List all sessions
    print("\n1. LISTING ALL AVAILABLE SESSIONS")
    print("-" * 80)
    sessions = logger.get_all_sessions()
    
    if not sessions:
        print("No sessions found in audit/logs")
        return
    
    print(f"Found {len(sessions)} session(s):\n")
    for session_id in sessions:
        print(f"  - {session_id}")
    
    # 2. Get summary for each session
    print("\n2. SESSION SUMMARIES")
    print("-" * 80)
    for session_id in sessions:
        summary = logger.get_session_summary(session_id)
        
        print(f"\nSession: {session_id}")
        print(f"  Total Events:  {summary['total_events']}")
        print(f"  Total Cost:    ${summary['total_cost']:.2f}")
        print(f"  Total Revenue: ${summary['total_revenue']:.2f}")
        print(f"  Net Profit:    ${summary['net_profit']:.2f}")
        
        if summary['total_cost'] > 0:
            print(f"  ROI:           {summary['roi']:.2f}%")
        
        if summary['component_stats']:
            print(f"\n  Components:")
            for comp, stats in summary['component_stats'].items():
                print(f"    {comp}:")
                print(f"      Events:  {stats['event_count']}")
                print(f"      Cost:    ${stats['cost']:.2f}")
                print(f"      Revenue: ${stats['revenue']:.2f}")
                if stats['errors'] > 0:
                    print(f"      Errors:  {stats['errors']}")
    
    # 3. Aggregate statistics across all sessions
    print("\n3. AGGREGATE STATISTICS (ALL SESSIONS)")
    print("-" * 80)
    total_events = 0
    total_cost = 0.0
    total_revenue = 0.0
    all_components = set()
    
    for session_id in sessions:
        summary = logger.get_session_summary(session_id)
        total_events += summary['total_events']
        total_cost += summary['total_cost']
        total_revenue += summary['total_revenue']
        all_components.update(summary['component_stats'].keys())
    
    print(f"\nTotal Sessions:    {len(sessions)}")
    print(f"Total Events:      {total_events}")
    print(f"Total Cost:        ${total_cost:.2f}")
    print(f"Total Revenue:     ${total_revenue:.2f}")
    print(f"Net Profit:        ${total_revenue - total_cost:.2f}")
    print(f"Unique Components: {len(all_components)}")
    print(f"Components:        {', '.join(sorted(all_components))}")
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    
    print("\nUSAGE EXAMPLES:")
    print("-" * 80)
    print("# List all sessions:")
    print("  python3 audit/audit_viewer.py --list-sessions")
    print("\n# Show summary for a specific session:")
    print(f"  python3 audit/audit_viewer.py --session {sessions[0]} --summary")
    print("\n# Show summaries for all sessions:")
    print("  python3 audit/audit_viewer.py --all-sessions")
    print("\n# Show events for a specific component:")
    print("  python3 audit/audit_viewer.py --component trading.polymarket")
    print()


if __name__ == "__main__":
    demonstrate_session_audit()
