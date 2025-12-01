#!/usr/bin/env python3
"""
Agent Session Order Validator

Ensures that agent sessions follow the correct order and don't skip ahead
of established dependencies. Validates that prerequisites are met before
allowing sessions to proceed.

Usage:
    from ai.session_order_validator import validate_session_order, register_session
    
    # Before starting a session
    if validate_session_order(session_id, prerequisites):
        # Session can proceed
        register_session(session_id, agent, dependencies)
    else:
        # Session must wait for prerequisites
        print("Prerequisites not met")
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Set

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

# UNIFIED AI - All systems serve Yair Siegel
try:
    from ai.unified_ai import MASTER, get_master, log_action
except ImportError:
    # Fallback when unified_ai module is not available
    MASTER = "Yair Siegel"
    def log_action(action, details): pass
    def get_master(): return MASTER
except (PermissionError, OSError) as e:
    # In CI/test environments where /root access is restricted
    # Log the issue but continue with fallback
    import sys
    print(f"Warning: Could not load unified_ai module ({e}), using fallback", file=sys.stderr)
    MASTER = "Yair Siegel"
    def log_action(action, details): pass
    def get_master(): return MASTER


class SessionOrderValidator:
    """Manages and validates agent session execution order"""
    
    def __init__(self, repo_root: Path = None):
        self.repo_root = repo_root or REPO_ROOT
        self.order_file = self.repo_root / 'ai' / 'coordination' / 'session_order.json'
        self.order_file.parent.mkdir(parents=True, exist_ok=True)
        
    def load_order_state(self) -> Dict:
        """Load current session order state"""
        if not self.order_file.exists():
            return self._create_default_state()
        
        try:
            with open(self.order_file) as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse {self.order_file}, creating new state")
            return self._create_default_state()
    
    def _create_default_state(self) -> Dict:
        """Create default session order state"""
        return {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "description": "Tracks agent session execution order and dependencies",
            "active_sessions": [],
            "completed_sessions": [],
            "session_dependencies": {},
            "enforcement_rules": {
                "require_prerequisite_completion": True,
                "allow_parallel_independent_sessions": True,
                "block_dependency_violations": True
            },
            "notes": "Ensures agent sessions execute in correct order"
        }
    
    def save_order_state(self, state: Dict):
        """Save session order state"""
        state['last_updated'] = datetime.now(timezone.utc).isoformat()
        with open(self.order_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def validate_session_order(
        self,
        session_id: str,
        prerequisites: Optional[List[str]] = None,
        agent: Optional[str] = None
    ) -> bool:
        """
        Validate that a session can start based on prerequisites
        
        Args:
            session_id: Unique identifier for this session
            prerequisites: List of session IDs that must be completed first
            agent: Agent name starting the session
            
        Returns:
            True if session can proceed, False if prerequisites not met
        """
        state = self.load_order_state()
        
        # If no prerequisites, session can proceed
        if not prerequisites:
            log_action("session_validation", {
                "session_id": session_id,
                "agent": agent,
                "result": "approved_no_prerequisites"
            })
            return True
        
        # Check if enforcement is enabled
        if not state['enforcement_rules'].get('require_prerequisite_completion', True):
            log_action("session_validation", {
                "session_id": session_id,
                "agent": agent,
                "result": "approved_enforcement_disabled"
            })
            return True
        
        # Get completed sessions
        completed_session_ids = {s['session_id'] for s in state['completed_sessions']}
        
        # Check if all prerequisites are completed
        missing_prerequisites = []
        for prereq_id in prerequisites:
            if prereq_id not in completed_session_ids:
                missing_prerequisites.append(prereq_id)
        
        if missing_prerequisites:
            print(f"⚠️  Session {session_id} blocked - missing prerequisites:")
            for prereq in missing_prerequisites:
                print(f"   - {prereq}")
            
            log_action("session_validation", {
                "session_id": session_id,
                "agent": agent,
                "result": "blocked_missing_prerequisites",
                "missing": missing_prerequisites
            })
            return False
        
        log_action("session_validation", {
            "session_id": session_id,
            "agent": agent,
            "result": "approved_prerequisites_met"
        })
        return True
    
    def register_session(
        self,
        session_id: str,
        agent: str,
        dependencies: Optional[List[str]] = None,
        task_id: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Register a new active session
        
        Args:
            session_id: Unique identifier for this session
            agent: Agent name (copilot, claude-code, chatgpt, etc.)
            dependencies: List of session IDs this session depends on
            task_id: Optional task ID this session is working on
            description: Optional description of session purpose
        """
        state = self.load_order_state()
        
        # Check if session already exists
        existing_active = [s for s in state['active_sessions'] if s['session_id'] == session_id]
        if existing_active:
            print(f"Warning: Session {session_id} already registered as active")
            return
        
        existing_completed = [s for s in state['completed_sessions'] if s['session_id'] == session_id]
        if existing_completed:
            print(f"Warning: Session {session_id} already registered as completed")
            return
        
        # Add to active sessions
        session_record = {
            "session_id": session_id,
            "agent": agent,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "description": description,
            "status": "active"
        }
        
        state['active_sessions'].append(session_record)
        
        # Record dependencies
        if dependencies:
            state['session_dependencies'][session_id] = {
                "prerequisites": dependencies,
                "recorded_at": datetime.now(timezone.utc).isoformat()
            }
        
        self.save_order_state(state)
        
        print(f"✓ Registered session: {session_id} (agent: {agent})")
        if dependencies:
            print(f"  Dependencies: {', '.join(dependencies)}")
        
        log_action("session_registered", {
            "session_id": session_id,
            "agent": agent,
            "dependencies": dependencies
        })
    
    def complete_session(
        self,
        session_id: str,
        outcome: str = "success",
        notes: Optional[str] = None
    ):
        """
        Mark a session as completed
        
        Args:
            session_id: Session ID to complete
            outcome: Outcome status (success, failed, partial, etc.)
            notes: Optional completion notes
        """
        state = self.load_order_state()
        
        # Find and remove from active sessions
        active_session = None
        remaining_active = []
        
        for session in state['active_sessions']:
            if session['session_id'] == session_id:
                active_session = session
            else:
                remaining_active.append(session)
        
        if not active_session:
            print(f"Warning: Session {session_id} not found in active sessions")
            return
        
        # Add to completed sessions
        completion_record = {
            **active_session,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "outcome": outcome,
            "notes": notes,
            "status": "completed"
        }
        
        state['active_sessions'] = remaining_active
        state['completed_sessions'].append(completion_record)
        
        self.save_order_state(state)
        
        print(f"✓ Session completed: {session_id} (outcome: {outcome})")
        
        log_action("session_completed", {
            "session_id": session_id,
            "outcome": outcome,
            "duration_seconds": self._calculate_duration(
                active_session.get('started_at'),
                completion_record['completed_at']
            )
        })
    
    def _calculate_duration(self, start_time: str, end_time: str) -> Optional[int]:
        """Calculate session duration in seconds"""
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            return int((end - start).total_seconds())
        except (ValueError, TypeError, AttributeError) as e:
            # Handle invalid datetime formats or None values
            return None
    
    def get_blocked_sessions(self) -> List[Dict]:
        """
        Get list of sessions that are blocked by missing prerequisites
        
        Returns:
            List of session records that can't proceed
        """
        state = self.load_order_state()
        completed_ids = {s['session_id'] for s in state['completed_sessions']}
        blocked = []
        
        for session_id, dep_info in state['session_dependencies'].items():
            # Skip if already completed
            if session_id in completed_ids:
                continue
            
            # Check if in active sessions
            is_active = any(s['session_id'] == session_id for s in state['active_sessions'])
            
            # Check prerequisites
            prerequisites = dep_info.get('prerequisites', [])
            missing = [p for p in prerequisites if p not in completed_ids]
            
            if missing:
                blocked.append({
                    "session_id": session_id,
                    "is_active": is_active,
                    "missing_prerequisites": missing,
                    "recorded_at": dep_info.get('recorded_at')
                })
        
        return blocked
    
    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Get current status of a session"""
        state = self.load_order_state()
        
        # Check active sessions
        for session in state['active_sessions']:
            if session['session_id'] == session_id:
                return {**session, "state": "active"}
        
        # Check completed sessions
        for session in state['completed_sessions']:
            if session['session_id'] == session_id:
                return {**session, "state": "completed"}
        
        return None
    
    def display_status(self):
        """Display current session order status"""
        state = self.load_order_state()
        
        print("\n" + "="*60)
        print("AGENT SESSION ORDER STATUS")
        print("="*60)
        
        # Active sessions
        if state['active_sessions']:
            print(f"\nACTIVE SESSIONS ({len(state['active_sessions'])}):")
            for session in state['active_sessions']:
                print(f"\n  [{session['session_id'][:30]}] {session['agent']}")
                print(f"  Started: {session['started_at']}")
                if session.get('description'):
                    print(f"  Description: {session['description'][:80]}")
                if session.get('task_id'):
                    print(f"  Task ID: {session['task_id']}")
        else:
            print("\nACTIVE SESSIONS: None")
        
        # Blocked sessions
        blocked = self.get_blocked_sessions()
        if blocked:
            print(f"\nBLOCKED SESSIONS ({len(blocked)}):")
            for session in blocked:
                print(f"\n  [{session['session_id'][:30]}]")
                print(f"  Active: {'Yes' if session['is_active'] else 'Queued'}")
                print(f"  Missing prerequisites:")
                for prereq in session['missing_prerequisites']:
                    print(f"    - {prereq}")
        
        # Recently completed
        recent_completed = sorted(
            state['completed_sessions'],
            key=lambda s: s.get('completed_at', ''),
            reverse=True
        )[:5]
        
        if recent_completed:
            print(f"\nRECENTLY COMPLETED ({len(recent_completed)} of {len(state['completed_sessions'])}):")
            for session in recent_completed:
                print(f"\n  [{session['session_id'][:30]}] {session['agent']}")
                print(f"  Outcome: {session.get('outcome', 'unknown')}")
                print(f"  Completed: {session['completed_at']}")
                if session.get('notes'):
                    print(f"  Notes: {session['notes'][:60]}")
        
        print("\n" + "="*60 + "\n")


# Convenience functions for easy import
_validator = None

def get_validator() -> SessionOrderValidator:
    """Get singleton validator instance"""
    global _validator
    if _validator is None:
        _validator = SessionOrderValidator()
    return _validator


def validate_session_order(
    session_id: str,
    prerequisites: Optional[List[str]] = None,
    agent: Optional[str] = None
) -> bool:
    """Validate that a session can start (convenience function)"""
    return get_validator().validate_session_order(session_id, prerequisites, agent)


def register_session(
    session_id: str,
    agent: str,
    dependencies: Optional[List[str]] = None,
    task_id: Optional[str] = None,
    description: Optional[str] = None
):
    """Register a new session (convenience function)"""
    get_validator().register_session(session_id, agent, dependencies, task_id, description)


def complete_session(
    session_id: str,
    outcome: str = "success",
    notes: Optional[str] = None
):
    """Complete a session (convenience function)"""
    get_validator().complete_session(session_id, outcome, notes)


def get_blocked_sessions() -> List[Dict]:
    """Get blocked sessions (convenience function)"""
    return get_validator().get_blocked_sessions()


def main():
    """CLI interface"""
    import sys
    
    validator = SessionOrderValidator()
    
    if len(sys.argv) < 2:
        validator.display_status()
        return
    
    command = sys.argv[1]
    
    if command == 'status':
        validator.display_status()
    
    elif command == 'validate':
        if len(sys.argv) < 3:
            print("Usage: session_order_validator.py validate <session_id> [prereq1,prereq2,...]")
            return
        
        session_id = sys.argv[2]
        prerequisites = sys.argv[3].split(',') if len(sys.argv) > 3 else None
        
        if validate_session_order(session_id, prerequisites):
            print(f"✓ Session {session_id} can proceed")
        else:
            print(f"✗ Session {session_id} blocked by prerequisites")
            sys.exit(1)
    
    elif command == 'register':
        if len(sys.argv) < 4:
            print("Usage: session_order_validator.py register <session_id> <agent> [deps] [description]")
            return
        
        session_id = sys.argv[2]
        agent = sys.argv[3]
        dependencies = sys.argv[4].split(',') if len(sys.argv) > 4 and sys.argv[4] else None
        description = sys.argv[5] if len(sys.argv) > 5 else None
        
        register_session(session_id, agent, dependencies, description=description)
    
    elif command == 'complete':
        if len(sys.argv) < 3:
            print("Usage: session_order_validator.py complete <session_id> [outcome] [notes]")
            return
        
        session_id = sys.argv[2]
        outcome = sys.argv[3] if len(sys.argv) > 3 else "success"
        notes = sys.argv[4] if len(sys.argv) > 4 else None
        
        complete_session(session_id, outcome, notes)
    
    elif command == 'blocked':
        blocked = get_blocked_sessions()
        if not blocked:
            print("No blocked sessions")
        else:
            print(f"\nBLOCKED SESSIONS ({len(blocked)}):")
            for session in blocked:
                print(f"\n  Session: {session['session_id']}")
                print(f"  Active: {session['is_active']}")
                print(f"  Missing: {', '.join(session['missing_prerequisites'])}")
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: status, validate, register, complete, blocked")
        sys.exit(1)


if __name__ == '__main__':
    main()
