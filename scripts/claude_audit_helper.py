#!/usr/bin/env python3
"""
Claude Audit Helper

Helper script to log Claude Code CLI actions to the audit system.
Can be called from shell scripts or used as a library.

Usage:
    # From command line
    python3 scripts/claude_audit_helper.py log_action \
        --action "code_generation" \
        --files-changed 3 \
        --lines-added 150 \
        --lines-removed 50
    
    # From Python
    from scripts.claude_audit_helper import log_claude_action
    log_claude_action("code_review", files_changed=2, lines_added=10)
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from audit import AuditLogger, FinancialLedger
    from ai_nexus import ClaudeProvider
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False
    print("Warning: Audit system not available", file=sys.stderr)


def log_claude_action(
    action: str,
    files_changed: int = 0,
    lines_added: int = 0,
    lines_removed: int = 0,
    tokens_used: Optional[int] = None,
    session_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    verbose: bool = False
) -> bool:
    """
    Log a Claude Code CLI action to the audit system
    
    Args:
        action: Action performed (e.g., "code_generation", "code_review")
        files_changed: Number of files modified
        lines_added: Lines of code added
        lines_removed: Lines of code removed
        tokens_used: Tokens used (if known)
        session_id: Optional session ID
        metadata: Additional metadata
        verbose: Print details
        
    Returns:
        True if logged successfully
    """
    if not AUDIT_AVAILABLE:
        if verbose:
            print("Audit system not available - skipping logging", file=sys.stderr)
        return False
    
    try:
        # Initialize audit system
        audit_logger = AuditLogger()
        ledger = FinancialLedger()
        claude_provider = ClaudeProvider(audit_logger, ledger)
        
        # Log the action
        claude_provider.log_action(
            action=action,
            files_changed=files_changed,
            lines_added=lines_added,
            lines_removed=lines_removed,
            tokens_used=tokens_used,
            session_id=session_id,
            metadata=metadata
        )
        
        if verbose:
            print(f"✓ Logged Claude action: {action}")
            print(f"  Files changed: {files_changed}")
            print(f"  Lines added: {lines_added}")
            print(f"  Lines removed: {lines_removed}")
            if tokens_used:
                print(f"  Tokens used: {tokens_used}")
        
        return True
        
    except Exception as e:
        print(f"Error logging Claude action: {e}", file=sys.stderr)
        return False


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description="Log Claude Code CLI actions to audit system"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # log_action command
    log_parser = subparsers.add_parser('log_action', help='Log a Claude action')
    log_parser.add_argument(
        '--action',
        required=True,
        help='Action performed (e.g., code_generation, code_review, optimization)'
    )
    log_parser.add_argument(
        '--files-changed',
        type=int,
        default=0,
        help='Number of files modified'
    )
    log_parser.add_argument(
        '--lines-added',
        type=int,
        default=0,
        help='Lines of code added'
    )
    log_parser.add_argument(
        '--lines-removed',
        type=int,
        default=0,
        help='Lines of code removed'
    )
    log_parser.add_argument(
        '--tokens-used',
        type=int,
        help='Tokens used (if known)'
    )
    log_parser.add_argument(
        '--session-id',
        help='Session ID'
    )
    log_parser.add_argument(
        '--metadata',
        help='Additional metadata as JSON string'
    )
    log_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'log_action':
        # Parse metadata if provided
        metadata = None
        if args.metadata:
            import json
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError as e:
                print(f"Error parsing metadata JSON: {e}", file=sys.stderr)
                sys.exit(1)
        
        # Log the action
        success = log_claude_action(
            action=args.action,
            files_changed=args.files_changed,
            lines_added=args.lines_added,
            lines_removed=args.lines_removed,
            tokens_used=args.tokens_used,
            session_id=args.session_id,
            metadata=metadata,
            verbose=args.verbose
        )
        
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
