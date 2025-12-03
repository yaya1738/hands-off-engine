#!/usr/bin/env python3
"""
INTEGRAFIX: AI Memory System
============================

PROBLEM SOLVED:
Each Claude session starts with zero memory of previous sessions.
170+ AI sessions have run but none learned from each other.

SOLUTION:
A memory system that:
1. Persists key learnings between sessions
2. Stores important context and decisions
3. Loads relevant memory at session start
4. Compresses old memories to maintain relevance
5. Enables continuity across sessions

This wire connects AI sessions through time.
"""

import json
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
MEMORY_DIR = STATE_DIR / "ai_memory"
MEMORY_INDEX = MEMORY_DIR / "index.json"
CONTEXT_FILE = MEMORY_DIR / "current_context.json"


class MemoryType(Enum):
    """Types of memories."""
    DECISION = "decision"         # A decision that was made
    LEARNING = "learning"         # Something learned
    ERROR = "error"               # An error encountered
    SUCCESS = "success"           # A successful outcome
    CONTEXT = "context"           # Important context
    TODO = "todo"                 # Task that needs doing
    INSIGHT = "insight"           # An insight discovered
    CODE_CHANGE = "code_change"   # A code change made


class MemoryPriority(Enum):
    """Priority of memories for retrieval."""
    CRITICAL = 5    # Always load
    HIGH = 4        # Load in related contexts
    MEDIUM = 3      # Load if space permits
    LOW = 2         # Compress after 24h
    EPHEMERAL = 1   # Discard after session


@dataclass
class Memory:
    """A single memory."""
    id: str
    memory_type: MemoryType
    priority: MemoryPriority
    content: str
    context: str                  # What triggered this memory
    tags: List[str]
    created_at: str
    session_id: str
    relevance_score: float = 1.0
    access_count: int = 0
    last_accessed: Optional[str] = None
    compressed: bool = False
    compressed_content: Optional[str] = None


@dataclass
class SessionSummary:
    """Summary of an AI session."""
    session_id: str
    started_at: str
    ended_at: Optional[str]
    task_description: str
    decisions_made: int
    learnings_recorded: int
    errors_encountered: int
    successes: int
    key_outcomes: List[str]
    next_actions: List[str]


class AIMemory:
    """
    Persistent memory for AI sessions.

    Enables Claude to remember across sessions.
    """

    def __init__(self, session_id: Optional[str] = None):
        self.memory_dir = MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.memories: Dict[str, Memory] = {}
        self.sessions: Dict[str, SessionSummary] = {}

        self._load_index()
        self._load_relevant_memories()

    def _load_index(self):
        """Load memory index."""
        if MEMORY_INDEX.exists():
            with open(MEMORY_INDEX) as f:
                data = json.load(f)

            for sid, sdata in data.get("sessions", {}).items():
                self.sessions[sid] = SessionSummary(**sdata)

    def _save_index(self):
        """Save memory index."""
        data = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_memories": len(self.memories),
            "total_sessions": len(self.sessions),
            "sessions": {sid: asdict(s) for sid, s in self.sessions.items()},
        }
        with open(MEMORY_INDEX, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_relevant_memories(self):
        """Load memories relevant to current session."""
        # Load all memory files
        for f in self.memory_dir.glob("memory_*.json"):
            try:
                with open(f) as fp:
                    mdata = json.load(fp)
                    mdata["memory_type"] = MemoryType(mdata["memory_type"])
                    mdata["priority"] = MemoryPriority(mdata["priority"])
                    mem = Memory(**mdata)

                    # Only load non-ephemeral or recent ephemeral
                    if mem.priority != MemoryPriority.EPHEMERAL:
                        self.memories[mem.id] = mem
                    elif self._is_recent(mem.created_at, hours=24):
                        self.memories[mem.id] = mem
            except Exception:
                pass

    def _is_recent(self, timestamp: str, hours: int = 24) -> bool:
        """Check if a timestamp is recent."""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            age = datetime.now(timezone.utc) - dt
            return age < timedelta(hours=hours)
        except:
            return False

    def _generate_id(self, content: str) -> str:
        """Generate memory ID."""
        hash_input = f"{content}:{datetime.now().isoformat()}"
        return f"mem_{hashlib.md5(hash_input.encode()).hexdigest()[:12]}"

    # ==================== REMEMBER ====================

    def remember(
        self,
        content: str,
        memory_type: MemoryType,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        context: str = "",
        tags: Optional[List[str]] = None,
    ) -> Memory:
        """
        Store a memory.

        Args:
            content: What to remember
            memory_type: Type of memory
            priority: How important
            context: What triggered this
            tags: Searchable tags
        """
        mem = Memory(
            id=self._generate_id(content),
            memory_type=memory_type,
            priority=priority,
            content=content,
            context=context,
            tags=tags or [],
            created_at=datetime.now(timezone.utc).isoformat(),
            session_id=self.session_id,
        )

        self.memories[mem.id] = mem

        # Save to file
        with open(self.memory_dir / f"memory_{mem.id}.json", 'w') as f:
            mdict = asdict(mem)
            mdict["memory_type"] = mem.memory_type.value
            mdict["priority"] = mem.priority.value
            json.dump(mdict, f, indent=2)

        self._save_index()
        return mem

    def remember_decision(self, decision: str, reasoning: str, outcome: str = ""):
        """Remember a decision."""
        content = f"Decision: {decision}\nReasoning: {reasoning}"
        if outcome:
            content += f"\nOutcome: {outcome}"
        return self.remember(
            content=content,
            memory_type=MemoryType.DECISION,
            priority=MemoryPriority.HIGH,
            tags=["decision"],
        )

    def remember_learning(self, what_learned: str, how_learned: str):
        """Remember something learned."""
        return self.remember(
            content=f"{what_learned}\n\nLearned from: {how_learned}",
            memory_type=MemoryType.LEARNING,
            priority=MemoryPriority.HIGH,
            tags=["learning"],
        )

    def remember_error(self, error: str, solution: str = ""):
        """Remember an error."""
        content = f"Error: {error}"
        if solution:
            content += f"\n\nSolution: {solution}"
        return self.remember(
            content=content,
            memory_type=MemoryType.ERROR,
            priority=MemoryPriority.HIGH,
            tags=["error"],
        )

    def remember_success(self, what_worked: str, why_worked: str):
        """Remember a success."""
        return self.remember(
            content=f"Success: {what_worked}\n\nWhy it worked: {why_worked}",
            memory_type=MemoryType.SUCCESS,
            priority=MemoryPriority.HIGH,
            tags=["success"],
        )

    def remember_code_change(self, file_path: str, description: str, reason: str):
        """Remember a code change."""
        return self.remember(
            content=f"File: {file_path}\nChange: {description}\nReason: {reason}",
            memory_type=MemoryType.CODE_CHANGE,
            priority=MemoryPriority.MEDIUM,
            tags=["code", file_path.split("/")[-1]],
        )

    # ==================== RECALL ====================

    def recall(
        self,
        query: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Memory]:
        """
        Recall memories.

        Args:
            query: Search query (searches content)
            memory_type: Filter by type
            tags: Filter by tags
            limit: Max memories to return
        """
        results = []

        for mem in self.memories.values():
            # Filter by type
            if memory_type and mem.memory_type != memory_type:
                continue

            # Filter by tags
            if tags and not any(t in mem.tags for t in tags):
                continue

            # Filter by query
            if query:
                query_lower = query.lower()
                if (query_lower not in mem.content.lower() and
                    query_lower not in mem.context.lower()):
                    continue

            results.append(mem)

        # Sort by relevance and priority
        results.sort(key=lambda m: (
            m.priority.value,
            m.relevance_score,
            m.created_at,
        ), reverse=True)

        # Update access counts
        for mem in results[:limit]:
            mem.access_count += 1
            mem.last_accessed = datetime.now(timezone.utc).isoformat()

        return results[:limit]

    def recall_decisions(self, limit: int = 5) -> List[Memory]:
        """Recall recent decisions."""
        return self.recall(memory_type=MemoryType.DECISION, limit=limit)

    def recall_learnings(self, limit: int = 5) -> List[Memory]:
        """Recall learnings."""
        return self.recall(memory_type=MemoryType.LEARNING, limit=limit)

    def recall_errors(self, limit: int = 5) -> List[Memory]:
        """Recall errors and their solutions."""
        return self.recall(memory_type=MemoryType.ERROR, limit=limit)

    def recall_about(self, topic: str, limit: int = 5) -> List[Memory]:
        """Recall memories about a topic."""
        return self.recall(query=topic, limit=limit)

    # ==================== SESSION MANAGEMENT ====================

    def start_session(self, task_description: str):
        """Start a new session."""
        summary = SessionSummary(
            session_id=self.session_id,
            started_at=datetime.now(timezone.utc).isoformat(),
            ended_at=None,
            task_description=task_description,
            decisions_made=0,
            learnings_recorded=0,
            errors_encountered=0,
            successes=0,
            key_outcomes=[],
            next_actions=[],
        )
        self.sessions[self.session_id] = summary
        self._save_index()

        # Remember session start
        self.remember(
            content=f"Starting session: {task_description}",
            memory_type=MemoryType.CONTEXT,
            priority=MemoryPriority.MEDIUM,
            tags=["session_start"],
        )

    def end_session(self, outcomes: List[str], next_actions: List[str]):
        """End current session with summary."""
        if self.session_id in self.sessions:
            summary = self.sessions[self.session_id]
            summary.ended_at = datetime.now(timezone.utc).isoformat()
            summary.key_outcomes = outcomes
            summary.next_actions = next_actions

            # Count memory types from this session
            session_mems = [m for m in self.memories.values()
                          if m.session_id == self.session_id]
            summary.decisions_made = sum(
                1 for m in session_mems if m.memory_type == MemoryType.DECISION
            )
            summary.learnings_recorded = sum(
                1 for m in session_mems if m.memory_type == MemoryType.LEARNING
            )
            summary.errors_encountered = sum(
                1 for m in session_mems if m.memory_type == MemoryType.ERROR
            )
            summary.successes = sum(
                1 for m in session_mems if m.memory_type == MemoryType.SUCCESS
            )

            self._save_index()

        # Remember session end
        self.remember(
            content=f"Session ended.\nOutcomes: {outcomes}\nNext: {next_actions}",
            memory_type=MemoryType.CONTEXT,
            priority=MemoryPriority.HIGH,
            tags=["session_end"],
        )

    def get_session_history(self, limit: int = 5) -> List[SessionSummary]:
        """Get recent session summaries."""
        sessions = list(self.sessions.values())
        sessions.sort(key=lambda s: s.started_at, reverse=True)
        return sessions[:limit]

    # ==================== CONTEXT BUILDING ====================

    def build_context(self) -> str:
        """
        Build context string for new session.

        This is what gets loaded at the start of a Claude session
        to provide continuity.
        """
        context_parts = []

        # Recent session summary
        recent_sessions = self.get_session_history(3)
        if recent_sessions:
            context_parts.append("=== PREVIOUS SESSIONS ===")
            for s in recent_sessions:
                context_parts.append(
                    f"\n[{s.started_at[:10]}] {s.task_description}\n"
                    f"  Outcomes: {', '.join(s.key_outcomes[:3])}\n"
                    f"  Next actions: {', '.join(s.next_actions[:3])}"
                )

        # Key learnings
        learnings = self.recall_learnings(5)
        if learnings:
            context_parts.append("\n\n=== KEY LEARNINGS ===")
            for l in learnings:
                context_parts.append(f"\n- {l.content[:200]}")

        # Recent errors and solutions
        errors = self.recall_errors(3)
        if errors:
            context_parts.append("\n\n=== RECENT ERRORS (avoid repeating) ===")
            for e in errors:
                context_parts.append(f"\n- {e.content[:200]}")

        # Recent successes
        successes = self.recall(memory_type=MemoryType.SUCCESS, limit=3)
        if successes:
            context_parts.append("\n\n=== WHAT WORKED ===")
            for s in successes:
                context_parts.append(f"\n- {s.content[:200]}")

        return "\n".join(context_parts)

    def save_context(self):
        """Save current context for next session."""
        context = self.build_context()
        with open(CONTEXT_FILE, 'w') as f:
            json.dump({
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "session_id": self.session_id,
                "context": context,
            }, f, indent=2)

    @staticmethod
    def load_context() -> str:
        """Load context from previous session."""
        if CONTEXT_FILE.exists():
            with open(CONTEXT_FILE) as f:
                data = json.load(f)
                return data.get("context", "")
        return ""

    # ==================== COMPRESSION ====================

    def compress_old_memories(self, older_than_days: int = 7):
        """
        Compress old memories to save space.

        Old memories get summarized and original discarded.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)

        for mem in self.memories.values():
            if mem.compressed:
                continue

            created = datetime.fromisoformat(mem.created_at.replace('Z', '+00:00'))
            if created < cutoff and mem.priority.value < MemoryPriority.HIGH.value:
                # Compress by truncating
                mem.compressed = True
                mem.compressed_content = mem.content[:100] + "..."

                # Save compressed version
                with open(self.memory_dir / f"memory_{mem.id}.json", 'w') as f:
                    mdict = asdict(mem)
                    mdict["memory_type"] = mem.memory_type.value
                    mdict["priority"] = mem.priority.value
                    json.dump(mdict, f, indent=2)

    def status(self) -> Dict:
        """Get memory system status."""
        return {
            "session_id": self.session_id,
            "total_memories": len(self.memories),
            "total_sessions": len(self.sessions),
            "memories_by_type": {
                mt.value: sum(1 for m in self.memories.values()
                            if m.memory_type == mt)
                for mt in MemoryType
            },
            "compressed_memories": sum(
                1 for m in self.memories.values() if m.compressed
            ),
        }


# Singleton instance
_memory = None

def get_memory(session_id: Optional[str] = None) -> AIMemory:
    global _memory
    if _memory is None or session_id:
        _memory = AIMemory(session_id)
    return _memory


def main():
    """Test the AI memory system."""
    memory = get_memory()

    print("=" * 70)
    print("INTEGRAFIX: AI Memory System Test")
    print("=" * 70)
    print()

    # Start session
    memory.start_session("Testing the AI memory system")

    # Remember some things
    memory.remember_decision(
        decision="Use file-based storage for memories",
        reasoning="Simple, persistent, works across sessions",
        outcome="Works well",
    )

    memory.remember_learning(
        what_learned="Edge detection was circular",
        how_learned="Analyzed sync_polymarket_model.py and found fair_price = market_price + noise",
    )

    memory.remember_error(
        error="Process coordinator needs file locking",
        solution="Used fcntl.flock for atomic state operations",
    )

    memory.remember_success(
        what_worked="Creating integrafix methodology",
        why_worked="Systematic approach to identifying and fixing integration gaps",
    )

    # Recall
    print("Recent decisions:")
    for d in memory.recall_decisions(3):
        print(f"  - {d.content[:60]}...")

    print("\nLearnings:")
    for l in memory.recall_learnings(3):
        print(f"  - {l.content[:60]}...")

    # Build context
    print("\n" + "=" * 70)
    print("CONTEXT FOR NEXT SESSION:")
    print("=" * 70)
    print(memory.build_context())

    # End session
    memory.end_session(
        outcomes=["Created memory system", "Tested all functions"],
        next_actions=["Integrate with Claude sessions", "Add context loading to startup"],
    )

    print("\n" + "=" * 70)
    print("Status:")
    print(json.dumps(memory.status(), indent=2))

    return memory


if __name__ == "__main__":
    main()
