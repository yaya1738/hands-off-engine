"""
Spark Plug Core Types v0.1

Defines core abstractions for the 3-part Spark Plug infrastructure:
- Part 1: CPU (CpuInstance, CpuMessage)
- Part 2: Memory Kernels (MemoryKernel, KernelUpdate, Decision, FailedPath)
- Part 3: User Expansion (UserEvent, SystemToUserMessage)

See: docs/SPARK_PLUG_ARCHITECTURE_v0.1.md
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Literal
from datetime import datetime
import json


# =============================================================================
# Part 1: CPU Types
# =============================================================================

@dataclass
class CpuConfig:
    """Configuration for a CPU instance"""
    max_rounds: Optional[int] = None          # For burst mode (None = continuous)
    max_cost_usd: float = 1.0                 # Spending limit
    allowed_nodes: List[str] = field(default_factory=lambda: ["chatgpt", "claude_cli", "github_copilot_agent"])
    safety_profile: str = "design_only"       # No execution access

    # v0.2: Continuous mode caps
    max_steps: Optional[int] = 20             # Max steps for continuous mode (v0.2)
    max_duration_seconds: Optional[int] = 900  # Max wall-clock seconds (v0.2)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "CpuConfig":
        return cls(**data)


@dataclass
class CpuInstance:
    """
    Represents one running CPU context (tri-agent discussion)

    Modes:
        - burst: Run for N rounds then stop (max_rounds set)
        - continuous: Loop on input queue indefinitely (max_rounds = None)

    Safety:
        - Isolated from trading/execution (design_only)
        - No decider, executor, or risk management access
    """
    cpu_id: str                                      # e.g., "cpu_risk_20251125_01"
    mode: Literal["burst", "continuous"]             # Burst or continuous mode
    bound_kernels: List[str] = field(default_factory=list)  # Memory kernel IDs (from Part 2)
    intercom_path: str = ""                          # Path to thread.jsonl
    input_queue: Optional[str] = None                # For continuous mode
    output_queue: Optional[str] = None               # For continuous mode
    status: Literal["idle", "running", "paused", "stopped"] = "idle"
    config: CpuConfig = field(default_factory=CpuConfig)
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    # v0.2: Continuous mode tracking
    steps_completed: int = 0                         # Total steps taken (v0.2)
    duration_seconds: float = 0.0                    # Total duration in seconds (v0.2)
    kernel_updates_applied: bool = False             # Whether kernel updates were written (v0.2)

    # Session ordering and dependency tracking
    previous_session_id: Optional[str] = None        # ID of previous session that must complete first
    depends_on: List[str] = field(default_factory=list)  # List of session IDs this depends on
    session_order: Optional[int] = None              # Explicit order number if part of a sequence

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['config'] = self.config.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "CpuInstance":
        config = CpuConfig.from_dict(data.pop('config', {}))
        return cls(config=config, **data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "CpuInstance":
        return cls.from_dict(json.loads(json_str))


@dataclass
class CpuMessage:
    """
    Single message in a CPU intercom thread

    Format matches TRI_AGENT_INTERCOM_v0.1.md with enhancements:
        - Added 'role' for OpenAI/Anthropic compatibility
        - Added 'meta' for extended metadata
    """
    msg_id: str                                      # e.g., "msg-0042"
    timestamp: str                                   # ISO 8601 timestamp
    from_: str                                       # Source: agent ID, "system", "user"
    role: Literal["system", "user", "assistant"]     # OpenAI-style role
    content: str                                     # Natural language message
    meta: Dict = field(default_factory=dict)         # tokens, cost_usd, tags, related_kernels, model

    def to_dict(self) -> Dict:
        data = asdict(self)
        # Map from_ back to 'from' for JSON
        data['from'] = data.pop('from_')
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "CpuMessage":
        # Map 'from' to from_ for Python
        if 'from' in data:
            data['from_'] = data.pop('from')
        return cls(**data)

    def to_jsonl_line(self) -> str:
        """Convert to single JSONL line"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_jsonl_line(cls, line: str) -> "CpuMessage":
        """Parse from single JSONL line"""
        return cls.from_dict(json.loads(line))


# =============================================================================
# Part 2: Memory Kernel Types
# =============================================================================

@dataclass
class Decision:
    """A key decision captured in a memory kernel"""
    decision: str                    # What was decided
    rationale: str                   # Why
    source: str                      # Which agent/CPU/conversation
    date: str                        # ISO 8601
    status: str = "approved"         # approved, pending, rejected

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Decision":
        return cls(**data)


@dataclass
class FailedPath:
    """A failed attempt - learning from mistakes"""
    attempt: str                     # What was tried
    failure: str                     # What went wrong
    lesson: str                      # What was learned
    date: str                        # ISO 8601

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "FailedPath":
        return cls(**data)


@dataclass
class MemoryKernel:
    """
    Topic-specific compressed memory from historical interactions

    A kernel is built from:
        - User ↔ ChatGPT interactions
        - User ↔ Claude CLI interactions
        - Multi-agent CPU discussions
        - System actions and decisions

    Kernels are:
        - Topic-focused (risk, alpha, infra, coordination, etc.)
        - Compressed (tight summaries, not raw logs)
        - Source-linked (references to ai/history/* files)
        - Weighted (source_weights define trust per agent)
    """
    kernel_id: str                                   # e.g., "risk_model_v2"
    topic: str                                       # Human-readable topic
    summary: str                                     # Tight narrative of what's known/decided
    key_decisions: List[Decision] = field(default_factory=list)
    failed_paths: List[FailedPath] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    source_weights: Dict[str, float] = field(default_factory=lambda: {
        "chatgpt": 1.0,
        "claude_cli": 0.8,
        "github_copilot_agent": 0.6
    })
    raw_refs: List[str] = field(default_factory=list)  # Links to ai/history/* files
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['key_decisions'] = [d.to_dict() for d in self.key_decisions]
        data['failed_paths'] = [f.to_dict() for f in self.failed_paths]
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "MemoryKernel":
        decisions = [Decision.from_dict(d) for d in data.get('key_decisions', [])]
        failed_paths = [FailedPath.from_dict(f) for f in data.get('failed_paths', [])]
        data['key_decisions'] = decisions
        data['failed_paths'] = failed_paths
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "MemoryKernel":
        return cls.from_dict(json.loads(json_str))


@dataclass
class KernelUpdate:
    """
    An update to append to a memory kernel

    When CPU (Part 1) makes a decision or learns something new,
    it creates a KernelUpdate that gets merged into the kernel.
    """
    update_type: Literal["decision", "failed_path", "question", "summary_edit"]
    content: Dict                                    # Type-specific content
    source: str                                      # CPU ID or agent ID
    agent: Optional[str] = None                      # Which agent in CPU made this
    date: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "KernelUpdate":
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "KernelUpdate":
        return cls.from_dict(json.loads(json_str))


# =============================================================================
# Part 3: User Expansion Types (Future, Designed Now)
# =============================================================================

@dataclass
class UserEvent:
    """
    User input event from any UI (ChatGPT, Claude, Unified)

    Part 3 connector reads user messages and creates UserEvents.
    These flow into ai/history/ and get contracted into kernels.
    """
    event_id: str                                    # Unique event ID
    timestamp: str                                   # ISO 8601
    source: Literal["chatgpt_ui", "claude_ui", "unified_ui"]
    user_id: str                                     # e.g., "froggy"
    content: str                                     # User's message
    context: Dict = field(default_factory=dict)      # conversation_id, related_kernels

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "UserEvent":
        return cls(**data)

    def to_jsonl_line(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_jsonl_line(cls, line: str) -> "UserEvent":
        return cls.from_dict(json.loads(line))


@dataclass
class SystemToUserMessage:
    """
    System decision/response sent back to user UI

    CPU makes decision → writes to kernel → creates SystemToUserMessage.
    Part 3 connector delivers this to the user's active UI.
    """
    msg_id: str                                      # Unique message ID
    timestamp: str                                   # ISO 8601
    target: Literal["chatgpt_ui", "claude_ui", "unified_ui"]
    user_id: str                                     # e.g., "froggy"
    content: str                                     # System's message
    source: Dict = field(default_factory=dict)       # cpu_id, agent, kernel

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "SystemToUserMessage":
        return cls(**data)

    def to_jsonl_line(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_jsonl_line(cls, line: str) -> "SystemToUserMessage":
        return cls.from_dict(json.loads(line))


@dataclass
class HistoryEvent:
    """
    General-purpose historical event for Part 3 history logging

    Captures any significant event in the system:
        - User messages/questions
        - System decisions
        - Trade outcomes
        - Model updates
        - Manual overrides
        - CPU conclusions

    These events accumulate in ai/history/user_events.jsonl and flow into
    kernels via the history-to-kernels connector.
    """
    event_id: str                                    # Unique event ID
    timestamp: str                                   # ISO 8601
    event_type: Literal[
        "user_message",
        "system_decision",
        "trade_outcome",
        "model_update",
        "manual_override",
        "cpu_conclusion",
        "observation",
        "other"
    ]
    source: str                                      # e.g., "user:froggy", "cpu_risk_01", "manual"
    content: str                                     # Natural language description
    context: Dict = field(default_factory=dict)      # Additional metadata (kernel_id, outcome, etc.)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "HistoryEvent":
        return cls(**data)

    def to_jsonl_line(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_jsonl_line(cls, line: str) -> "HistoryEvent":
        return cls.from_dict(json.loads(line))


# =============================================================================
# Utility Functions
# =============================================================================

def create_cpu_message(
    msg_id: str,
    from_: str,
    content: str,
    role: str = "assistant",
    **meta_kwargs
) -> CpuMessage:
    """Helper to create a CpuMessage with timestamp and meta"""
    return CpuMessage(
        msg_id=msg_id,
        timestamp=datetime.utcnow().isoformat() + "Z",
        from_=from_,
        role=role,
        content=content,
        meta=meta_kwargs
    )


def create_kernel_update_decision(
    decision: str,
    rationale: str,
    source: str,
    agent: Optional[str] = None
) -> KernelUpdate:
    """Helper to create a decision-type KernelUpdate"""
    return KernelUpdate(
        update_type="decision",
        content={
            "decision": decision,
            "rationale": rationale
        },
        source=source,
        agent=agent
    )


def create_kernel_update_failed_path(
    attempt: str,
    failure: str,
    lesson: str,
    source: str,
    agent: Optional[str] = None
) -> KernelUpdate:
    """Helper to create a failed_path-type KernelUpdate"""
    return KernelUpdate(
        update_type="failed_path",
        content={
            "attempt": attempt,
            "failure": failure,
            "lesson": lesson
        },
        source=source,
        agent=agent
    )


def create_history_event(
    event_type: str,
    source: str,
    content: str,
    event_id: Optional[str] = None,
    **context_kwargs
) -> "HistoryEvent":
    """Helper to create a HistoryEvent with auto-generated ID and timestamp"""
    if event_id is None:
        event_id = f"evt_{datetime.utcnow().timestamp()}"

    return HistoryEvent(
        event_id=event_id,
        timestamp=datetime.utcnow().isoformat() + "Z",
        event_type=event_type,
        source=source,
        content=content,
        context=context_kwargs
    )
