#!/usr/bin/env python3
"""
Claude Code CLI Audit Verification Tool

This script audits and verifies that Claude Code CLI actions are being
properly tracked in the audit system. It checks:

1. ClaudeProvider integration with audit logger
2. Audit log completeness for Claude actions
3. Financial ledger entries for Claude costs
4. Session tracking for Claude operations
5. Gaps in audit coverage

Usage:
    python3 audit/claude_audit_checker.py
    python3 audit/claude_audit_checker.py --session <session-id>
    python3 audit/claude_audit_checker.py --verbose
"""

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audit.audit_logger import AuditLogger
from audit.ledger import FinancialLedger


class ClaudeAuditChecker:
    """Audit checker for Claude Code CLI integration"""

    def __init__(self, audit_dir: str = "audit/logs"):
        self.audit_dir = Path(audit_dir)
        self.logger = AuditLogger(log_dir=audit_dir)
        self.ledger = FinancialLedger()
        self.issues: List[Dict] = []
        self.warnings: List[Dict] = []
        self.info: List[Dict] = []

    def check_provider_integration(self) -> bool:
        """
        Check if ClaudeProvider is properly integrated with audit system
        
        Returns:
            True if integration is correct
        """
        print("Checking ClaudeProvider integration...")
        
        try:
            from ai_nexus.provider_claude import ClaudeProvider
            
            # Check if ClaudeProvider has required methods
            required_methods = ['log_action', 'execute', 'estimate_cost']
            missing_methods = [m for m in required_methods if not hasattr(ClaudeProvider, m)]
            
            if missing_methods:
                self.issues.append({
                    'type': 'missing_methods',
                    'severity': 'high',
                    'message': f"ClaudeProvider missing methods: {', '.join(missing_methods)}"
                })
                return False
            
            # Check if log_action is implemented correctly
            import inspect
            log_action_sig = inspect.signature(ClaudeProvider.log_action)
            expected_params = ['self', 'action', 'files_changed', 'lines_added', 
                             'lines_removed', 'tokens_used', 'session_id', 'metadata']
            
            actual_params = list(log_action_sig.parameters.keys())
            if actual_params != expected_params:
                self.warnings.append({
                    'type': 'signature_mismatch',
                    'severity': 'medium',
                    'message': f"log_action signature differs from expected: {actual_params}"
                })
            
            self.info.append({
                'type': 'integration_check',
                'message': 'ClaudeProvider integration check passed'
            })
            return True
            
        except ImportError as e:
            self.issues.append({
                'type': 'import_error',
                'severity': 'critical',
                'message': f"Cannot import ClaudeProvider: {e}"
            })
            return False

    def check_audit_logs(self, session_id: Optional[str] = None) -> Dict:
        """
        Check audit logs for Claude actions
        
        Args:
            session_id: Optional session ID to check
            
        Returns:
            Dictionary with audit log statistics
        """
        print("Checking audit logs for Claude actions...")
        
        claude_events = self.logger.get_events(component="ai.claude")
        
        stats = {
            'total_events': len(claude_events),
            'actions': {},
            'time_range': None,
            'sessions': set(),
            'total_cost': 0.0
        }
        
        if not claude_events:
            self.warnings.append({
                'type': 'no_events',
                'severity': 'high',
                'message': 'No Claude events found in audit logs'
            })
            return stats
        
        # Analyze events
        for event in claude_events:
            # Track actions
            action = event.action
            if action not in stats['actions']:
                stats['actions'][action] = 0
            stats['actions'][action] += 1
            
            # Track sessions
            stats['sessions'].add(event.session_id)
            
            # Track costs
            if event.cost:
                stats['total_cost'] += event.cost
        
        # Time range
        if claude_events:
            stats['time_range'] = {
                'start': claude_events[0].timestamp,
                'end': claude_events[-1].timestamp
            }
        
        # Check for missing metadata
        events_missing_metadata = [
            e for e in claude_events 
            if not e.metadata or not e.metadata.get('files_changed')
        ]
        
        if events_missing_metadata:
            self.warnings.append({
                'type': 'missing_metadata',
                'severity': 'medium',
                'message': f"{len(events_missing_metadata)}/{len(claude_events)} events missing detailed metadata"
            })
        
        # Check for events without costs
        events_missing_cost = [e for e in claude_events if not e.cost]
        
        if events_missing_cost:
            self.warnings.append({
                'type': 'missing_cost',
                'severity': 'high',
                'message': f"{len(events_missing_cost)}/{len(claude_events)} events missing cost data"
            })
        
        self.info.append({
            'type': 'audit_check',
            'message': f"Found {len(claude_events)} Claude events across {len(stats['sessions'])} sessions"
        })
        
        return stats

    def check_ledger_entries(self) -> Dict:
        """
        Check financial ledger for Claude cost entries
        
        Returns:
            Dictionary with ledger statistics
        """
        print("Checking financial ledger for Claude entries...")
        
        try:
            # Get Claude-specific ledger entries
            claude_entries = self.ledger.get_entries(component='ai.claude')
            
            stats = {
                'total_entries': len(claude_entries),
                'total_cost': sum(e.amount for e in claude_entries if e.category == 'cost'),
                'total_revenue': sum(e.amount for e in claude_entries if e.category == 'revenue'),
                'actions': {}
            }
            
            # Analyze by action
            for entry in claude_entries:
                action = entry.action
                if action not in stats['actions']:
                    stats['actions'][action] = {'count': 0, 'total_cost': 0.0}
                
                stats['actions'][action]['count'] += 1
                if entry.category == 'cost':
                    stats['actions'][action]['total_cost'] += entry.amount
            
            if not claude_entries:
                self.warnings.append({
                    'type': 'no_ledger_entries',
                    'severity': 'high',
                    'message': 'No Claude entries found in financial ledger'
                })
            else:
                self.info.append({
                    'type': 'ledger_check',
                    'message': f"Found {len(claude_entries)} ledger entries for Claude"
                })
            
            return stats
            
        except Exception as e:
            self.issues.append({
                'type': 'ledger_error',
                'severity': 'high',
                'message': f"Error reading ledger: {e}"
            })
            return {'total_entries': 0, 'total_cost': 0.0, 'total_revenue': 0.0, 'actions': {}}

    def check_integration_gaps(self) -> List[str]:
        """
        Identify gaps in Claude Code CLI integration
        
        Returns:
            List of identified gaps
        """
        print("Checking for integration gaps...")
        
        gaps = []
        
        # Check if there's a wrapper script for Claude Code CLI
        claude_scripts = [
            Path("scripts/claude_orchestrator.py"),
            Path("scripts/claude_sync.sh"),
            Path("scripts/claude_task_processor.sh")
        ]
        
        for script in claude_scripts:
            if script.exists():
                # Check if script calls audit logging
                content = script.read_text()
                if 'audit' not in content.lower() and 'log_action' not in content:
                    gaps.append(f"{script} does not appear to integrate with audit system")
                    self.warnings.append({
                        'type': 'no_audit_integration',
                        'severity': 'medium',
                        'message': f"{script.name} missing audit integration"
                    })
        
        # Check if .claude directory has audit hooks
        claude_dir = Path(".claude")
        if claude_dir.exists():
            instruction_files = list(claude_dir.glob("*.md"))
            for inst_file in instruction_files:
                content = inst_file.read_text()
                if 'audit' not in content.lower():
                    gaps.append(f"{inst_file} does not mention audit logging")
        
        return gaps

    def generate_report(self, verbose: bool = False) -> str:
        """
        Generate comprehensive audit report
        
        Args:
            verbose: Include detailed information
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 80)
        report.append(" CLAUDE CODE CLI AUDIT REPORT")
        report.append("=" * 80)
        report.append(f"\nGenerated: {datetime.now(timezone.utc).isoformat()}\n")
        
        # Integration check
        report.append("-" * 80)
        report.append(" INTEGRATION STATUS")
        report.append("-" * 80)
        integration_ok = self.check_provider_integration()
        report.append(f"ClaudeProvider Integration: {'✅ PASS' if integration_ok else '❌ FAIL'}\n")
        
        # Audit logs check
        report.append("-" * 80)
        report.append(" AUDIT LOGS")
        report.append("-" * 80)
        audit_stats = self.check_audit_logs()
        report.append(f"Total Claude Events: {audit_stats['total_events']}")
        report.append(f"Unique Sessions: {len(audit_stats['sessions'])}")
        report.append(f"Total Cost Tracked: ${audit_stats['total_cost']:.4f}")
        
        if audit_stats['actions']:
            report.append("\nActions Logged:")
            for action, count in sorted(audit_stats['actions'].items()):
                report.append(f"  • {action}: {count}")
        
        if audit_stats['time_range']:
            report.append(f"\nTime Range:")
            report.append(f"  Start: {audit_stats['time_range']['start']}")
            report.append(f"  End: {audit_stats['time_range']['end']}")
        
        report.append("")
        
        # Ledger check
        report.append("-" * 80)
        report.append(" FINANCIAL LEDGER")
        report.append("-" * 80)
        ledger_stats = self.check_ledger_entries()
        report.append(f"Total Ledger Entries: {ledger_stats['total_entries']}")
        report.append(f"Total Cost: ${ledger_stats['total_cost']:.4f}")
        report.append(f"Total Revenue: ${ledger_stats['total_revenue']:.4f}")
        
        if ledger_stats['actions']:
            report.append("\nBy Action:")
            for action, stats in sorted(ledger_stats['actions'].items()):
                report.append(f"  • {action}: {stats['count']} entries, ${stats['total_cost']:.4f}")
        
        report.append("")
        
        # Integration gaps
        report.append("-" * 80)
        report.append(" INTEGRATION GAPS")
        report.append("-" * 80)
        gaps = self.check_integration_gaps()
        if gaps:
            for gap in gaps:
                report.append(f"  ⚠️  {gap}")
        else:
            report.append("  ✅ No major integration gaps detected")
        
        report.append("")
        
        # Issues
        if self.issues:
            report.append("-" * 80)
            report.append(" ISSUES (CRITICAL)")
            report.append("-" * 80)
            for issue in self.issues:
                severity = issue.get('severity', 'unknown').upper()
                report.append(f"  ❌ [{severity}] {issue['message']}")
            report.append("")
        
        # Warnings
        if self.warnings:
            report.append("-" * 80)
            report.append(" WARNINGS")
            report.append("-" * 80)
            for warning in self.warnings:
                severity = warning.get('severity', 'unknown').upper()
                report.append(f"  ⚠️  [{severity}] {warning['message']}")
            report.append("")
        
        # Info (if verbose)
        if verbose and self.info:
            report.append("-" * 80)
            report.append(" INFORMATION")
            report.append("-" * 80)
            for info in self.info:
                report.append(f"  ℹ️  {info['message']}")
            report.append("")
        
        # Summary
        report.append("-" * 80)
        report.append(" SUMMARY")
        report.append("-" * 80)
        
        total_problems = len(self.issues) + len(self.warnings)
        if total_problems == 0:
            report.append("  ✅ Claude Code CLI audit integration appears healthy")
        else:
            report.append(f"  ⚠️  Found {len(self.issues)} issues and {len(self.warnings)} warnings")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Audit Claude Code CLI integration with audit system"
    )
    parser.add_argument(
        "--session",
        help="Check specific session ID"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed information"
    )
    parser.add_argument(
        "--audit-dir",
        default="audit/logs",
        help="Audit log directory (default: audit/logs)"
    )
    parser.add_argument(
        "--output",
        help="Save report to file"
    )
    
    args = parser.parse_args()
    
    # Run checker
    checker = ClaudeAuditChecker(audit_dir=args.audit_dir)
    report = checker.generate_report(verbose=args.verbose)
    
    # Output report
    print(report)
    
    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
        print(f"\nReport saved to: {output_path}")
    
    # Exit with appropriate code
    if checker.issues:
        sys.exit(1)  # Critical issues found
    elif checker.warnings:
        sys.exit(2)  # Warnings found
    else:
        sys.exit(0)  # All good


if __name__ == "__main__":
    main()
