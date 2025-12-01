#!/usr/bin/env python3
"""
Session Ordering System

Ensures agent sessions follow instructions from previous sessions and
execute in the correct order, preventing sessions from "jumping ahead"
of their intended sequence.

Key Features:
- Session dependency tracking
- Prerequisite validation before session start
- Session order enforcement
- Dependency chain validation
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, asdict

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

SESSION_ORDERING_FILE = REPO_ROOT / "state" / "session_ordering.json"


@dataclass
class SessionDependency:
    """
    Represents a session with its dependencies
    
    Attributes:
        session_id: Unique identifier for this session
        depends_on: List of session IDs that must complete before this one
        status: Current status (pending, ready, running, completed, failed)
        created_at: When this dependency was registered
        started_at: When session started (if running/completed)
        completed_at: When session completed (if completed)
        metadata: Additional context about the session
    """
    session_id: str
    depends_on: List[str]
    status: str = "pending"  # pending, ready, running, completed, failed
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.metadata is None:
            self.metadata = {}


class SessionOrderingManager:
    """
    Manages session ordering and dependency tracking
    
    Ensures sessions execute in the correct order by:
    1. Tracking dependencies between sessions
    2. Validating prerequisites before session start
    3. Updating session status throughout lifecycle
    4. Detecting and preventing circular dependencies
    """
    
    def __init__(self, ordering_file: Path = SESSION_ORDERING_FILE):
        self.ordering_file = ordering_file
        self.ordering_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_ordering(self) -> Dict[str, SessionDependency]:
        """Load session ordering from disk"""
        if not self.ordering_file.exists():
            return {}
        
        # Check if file is empty
        if self.ordering_file.stat().st_size == 0:
            return {}
        
        with open(self.ordering_file) as f:
            data = json.load(f)
        
        # Convert dicts back to SessionDependency objects
        sessions = {}
        for session_id, session_data in data.get("sessions", {}).items():
            sessions[session_id] = SessionDependency(**session_data)
        
        return sessions
    
    def _save_ordering(self, sessions: Dict[str, SessionDependency]):
        """Save session ordering to disk"""
        data = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "sessions": {
                sid: asdict(session) for sid, session in sessions.items()
            }
        }
        
        with open(self.ordering_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_session(
        self,
        session_id: str,
        depends_on: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Register a new session with its dependencies
        
        Args:
            session_id: Unique identifier for the session
            depends_on: List of session IDs this session depends on
            metadata: Additional context (task details, agent info, etc.)
        
        Returns:
            True if registration successful, False if circular dependency detected
        
        Example:
            manager.register_session(
                "session_003",
                depends_on=["session_001", "session_002"],
                metadata={"task": "analyze results", "agent": "claude"}
            )
        """
        sessions = self._load_ordering()
        
        depends_on = depends_on or []
        
        # Check for circular dependencies
        if self._has_circular_dependency(session_id, depends_on, sessions):
            print(f"⚠️  Circular dependency detected for session {session_id}")
            return False
        
        # Validate that dependencies exist (optional - warn but don't fail)
        for dep_id in depends_on:
            if dep_id not in sessions:
                print(f"⚠️  Warning: Dependency {dep_id} not registered yet")
        
        # Create session dependency entry
        session = SessionDependency(
            session_id=session_id,
            depends_on=depends_on,
            metadata=metadata or {}
        )
        
        sessions[session_id] = session
        self._save_ordering(sessions)
        
        print(f"✓ Registered session {session_id} with {len(depends_on)} dependencies")
        return True
    
    def can_start_session(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a session can start based on its dependencies
        
        Args:
            session_id: Session to check
        
        Returns:
            Tuple of (can_start: bool, reason: Optional[str])
            - (True, None) if session can start
            - (False, reason) if session cannot start with explanation
        
        Example:
            can_start, reason = manager.can_start_session("session_003")
            if not can_start:
                print(f"Cannot start: {reason}")
        """
        sessions = self._load_ordering()
        
        if session_id not in sessions:
            return False, f"Session {session_id} not registered"
        
        session = sessions[session_id]
        
        # Check if already running or completed
        if session.status in ["running", "completed"]:
            return False, f"Session already {session.status}"
        
        # Check all dependencies are completed
        incomplete_deps = []
        for dep_id in session.depends_on:
            if dep_id not in sessions:
                incomplete_deps.append(f"{dep_id} (not registered)")
                continue
            
            dep_session = sessions[dep_id]
            if dep_session.status != "completed":
                incomplete_deps.append(f"{dep_id} (status: {dep_session.status})")
        
        if incomplete_deps:
            reason = f"Waiting for dependencies: {', '.join(incomplete_deps)}"
            return False, reason
        
        return True, None
    
    def start_session(self, session_id: str) -> bool:
        """
        Mark a session as started if prerequisites are met
        
        Args:
            session_id: Session to start
        
        Returns:
            True if session started successfully, False otherwise
        
        Example:
            if manager.start_session("session_003"):
                print("Session started")
                # ... run session ...
                manager.complete_session("session_003")
        """
        can_start, reason = self.can_start_session(session_id)
        
        if not can_start:
            print(f"❌ Cannot start session {session_id}: {reason}")
            return False
        
        sessions = self._load_ordering()
        session = sessions[session_id]
        session.status = "running"
        session.started_at = datetime.now(timezone.utc).isoformat()
        
        self._save_ordering(sessions)
        print(f"▶️  Started session {session_id}")
        return True
    
    def complete_session(self, session_id: str, success: bool = True):
        """
        Mark a session as completed
        
        Args:
            session_id: Session that completed
            success: Whether session completed successfully
        
        Example:
            manager.complete_session("session_003", success=True)
        """
        sessions = self._load_ordering()
        
        if session_id not in sessions:
            print(f"⚠️  Warning: Session {session_id} not registered")
            return
        
        session = sessions[session_id]
        session.status = "completed" if success else "failed"
        session.completed_at = datetime.now(timezone.utc).isoformat()
        
        self._save_ordering(sessions)
        
        status_emoji = "✅" if success else "❌"
        print(f"{status_emoji} Session {session_id} {session.status}")
    
    def get_ready_sessions(self) -> List[str]:
        """
        Get list of sessions that are ready to start
        
        Returns:
            List of session IDs that can start now
        
        Example:
            ready = manager.get_ready_sessions()
            for session_id in ready:
                # Start session
                pass
        """
        sessions = self._load_ordering()
        ready = []
        
        for session_id, session in sessions.items():
            if session.status == "pending":
                can_start, _ = self.can_start_session(session_id)
                if can_start:
                    ready.append(session_id)
        
        return ready
    
    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """
        Get status information for a session
        
        Args:
            session_id: Session to query
        
        Returns:
            Dict with session info, or None if not found
        """
        sessions = self._load_ordering()
        
        if session_id not in sessions:
            return None
        
        session = sessions[session_id]
        return asdict(session)
    
    def _has_circular_dependency(
        self,
        session_id: str,
        depends_on: List[str],
        sessions: Dict[str, SessionDependency],
        visited: Optional[Set[str]] = None
    ) -> bool:
        """
        Check for circular dependencies using DFS
        
        Args:
            session_id: Current session being checked
            depends_on: Dependencies for the current session
            sessions: All registered sessions
            visited: Set of visited sessions (for recursion)
        
        Returns:
            True if circular dependency detected, False otherwise
        """
        if visited is None:
            visited = set()
        
        # Mark current session as visited
        visited.add(session_id)
        
        # Check each dependency
        for dep_id in depends_on:
            # If this dependency eventually depends on session_id, we have a cycle
            if dep_id == session_id:
                return True
            
            # If dependency exists, check its dependencies recursively
            if dep_id in sessions:
                if dep_id in visited:
                    # We've seen this session in the current path, but it's not necessarily a cycle
                    # unless it leads back to session_id
                    continue
                
                dep_session = sessions[dep_id]
                if self._has_circular_dependency(
                    session_id,
                    dep_session.depends_on,
                    sessions,
                    visited.copy()
                ):
                    return True
        
        return False
    
    def display_ordering(self):
        """Display current session ordering status"""
        sessions = self._load_ordering()
        
        if not sessions:
            print("○ No sessions registered")
            return
        
        print(f"\n{'='*60}")
        print(f"SESSION ORDERING STATUS ({len(sessions)} sessions)")
        print('='*60)
        
        # Group by status
        for status in ['running', 'pending', 'completed', 'failed']:
            status_sessions = [
                (sid, s) for sid, s in sessions.items() if s.status == status
            ]
            
            if status_sessions:
                status_emoji = {
                    'running': '▶️',
                    'pending': '⏸️',
                    'completed': '✅',
                    'failed': '❌'
                }
                print(f"\n{status_emoji.get(status, '○')} {status.upper()}:")
                
                for session_id, session in status_sessions:
                    deps = f" (depends on: {', '.join(session.depends_on)})" if session.depends_on else ""
                    print(f"  {session_id}{deps}")
                    
                    if session.status == "pending":
                        can_start, reason = self.can_start_session(session_id)
                        if not can_start:
                            print(f"    ⏳ {reason}")
        
        print(f"\n{'='*60}\n")


def main():
    """CLI interface for session ordering management"""
    import sys
    
    manager = SessionOrderingManager()
    
    if len(sys.argv) < 2:
        manager.display_ordering()
        return
    
    command = sys.argv[1]
    
    if command == 'list':
        manager.display_ordering()
    
    elif command == 'register':
        if len(sys.argv) < 3:
            print("Usage: session_ordering.py register <session_id> [dep1,dep2,...]")
            return
        
        session_id = sys.argv[2]
        depends_on = []
        if len(sys.argv) > 3:
            depends_on = [d.strip() for d in sys.argv[3].split(',')]
        
        manager.register_session(session_id, depends_on)
    
    elif command == 'start':
        if len(sys.argv) < 3:
            print("Usage: session_ordering.py start <session_id>")
            return
        
        session_id = sys.argv[2]
        manager.start_session(session_id)
    
    elif command == 'complete':
        if len(sys.argv) < 3:
            print("Usage: session_ordering.py complete <session_id> [success|fail]")
            return
        
        session_id = sys.argv[2]
        success = True
        if len(sys.argv) > 3:
            success = sys.argv[3].lower() != 'fail'
        
        manager.complete_session(session_id, success)
    
    elif command == 'ready':
        ready = manager.get_ready_sessions()
        if ready:
            print(f"Ready to start: {', '.join(ready)}")
        else:
            print("No sessions ready to start")
    
    elif command == 'status':
        if len(sys.argv) < 3:
            print("Usage: session_ordering.py status <session_id>")
            return
        
        session_id = sys.argv[2]
        status = manager.get_session_status(session_id)
        if status:
            print(json.dumps(status, indent=2))
        else:
            print(f"Session {session_id} not found")
    
    else:
        print(f"Unknown command: {command}")
        print("Commands: list, register, start, complete, ready, status")


if __name__ == '__main__':
    main()
