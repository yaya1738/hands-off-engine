"""
Part 3: Expansion Hole to User (Connector Stub)

This is a STUB showing where Part 3 UI connector would attach.

Part 3 is the expansion layer that keeps user and system "alive in lockstep":
- User messages → UserEvent → ai/history → kernels → CPU
- CPU decisions → kernels → SystemToUserMessage → User UI

Two implementation options:
    1. Sandboxed UI + Connector (bridge between ChatGPT/Claude UI and system)
    2. System-native Unified UI (direct access to CPU + kernels)

See: docs/SPARK_PLUG_ARCHITECTURE_v0.1.md (Part 3)

**IMPORTANT:** This is NOT implemented yet. Just architectural placeholders.
"""

from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ai_nexus.spark_plug_types import (
    UserEvent,
    SystemToUserMessage,
    CpuInstance
)
from ai_nexus.memory_kernels import load_kernel, append_kernel_update

# Paths
REPO_ROOT = Path(__file__).parent.parent
USER_EVENTS_FILE = REPO_ROOT / "ai" / "history" / "user" / "events.jsonl"
SYSTEM_MESSAGES_FILE = REPO_ROOT / "ai" / "history" / "system" / "messages.jsonl"


# =============================================================================
# Part 3.1: Sandboxed UI + Connector Option
# =============================================================================

def read_user_message_from_ui(ui_source: str) -> Optional[UserEvent]:
    """
    Read user message from sandboxed UI (ChatGPT, Claude, etc.)

    Implementation depends on UI:
        - ChatGPT: Export conversation, parse JSON
        - Claude: Web scraping or API (if available)
        - Unified: Direct access

    Returns:
        UserEvent if new message found, None otherwise

    TODO: Implement per UI source
    """
    raise NotImplementedError(
        "Part 3 connector not implemented. "
        "This would read from UI-specific sources (export files, APIs, web scraping)."
    )


def write_system_message_to_ui(message: SystemToUserMessage, ui_target: str) -> None:
    """
    Write system message back to user's UI

    Implementation depends on UI:
        - ChatGPT: Inject via API (if available) or display in alternate channel
        - Claude: Same
        - Unified: Direct write to UI thread

    TODO: Implement per UI target
    """
    raise NotImplementedError(
        "Part 3 connector not implemented. "
        "This would write to UI-specific targets (APIs, web injection, direct display)."
    )


# =============================================================================
# Part 3.2: System-Native Unified UI Option
# =============================================================================

def unified_ui_get_user_input() -> Optional[UserEvent]:
    """
    Get user input from unified UI (web or TUI)

    No sandbox boundary - direct input.

    TODO: Implement unified UI (web server or terminal UI)
    """
    raise NotImplementedError("Unified UI not implemented")


def unified_ui_display_message(message: SystemToUserMessage) -> None:
    """
    Display system message in unified UI

    No sandbox boundary - direct display.

    TODO: Implement unified UI (web server or terminal UI)
    """
    raise NotImplementedError("Unified UI not implemented")


# =============================================================================
# Integration Points (Where Part 3 Attaches)
# =============================================================================

def ingest_user_event(event: UserEvent) -> None:
    """
    Integration point: Ingest UserEvent into system

    Flow:
        1. UserEvent → ai/history/user/events.jsonl
        2. Contraction engine reads events
        3. Events get contracted into relevant kernels
        4. CPU can access via kernel wire

    This is the entry point for user → system flow.
    """
    # TODO: Ensure directory exists
    USER_EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Append to events log
    with open(USER_EVENTS_FILE, 'a') as f:
        f.write(event.to_jsonl_line() + '\n')

    # TODO: Trigger contraction engine to update kernels
    # For now, contraction is manual via memory_kernels.py API


def emit_system_message(
    content: str,
    target_ui: str,
    user_id: str,
    cpu_id: str,
    kernel_id: Optional[str] = None
) -> SystemToUserMessage:
    """
    Integration point: Emit system message to user

    Flow:
        1. CPU makes decision
        2. Decision written to kernel (Part 2)
        3. emit_system_message() creates SystemToUserMessage
        4. Message written to ai/history/system/messages.jsonl
        5. Part 3 connector reads and delivers to user UI

    This is the exit point for system → user flow.
    """
    message = SystemToUserMessage(
        msg_id=f"sys_msg_{datetime.utcnow().timestamp()}",
        timestamp=datetime.utcnow().isoformat() + "Z",
        target=target_ui,
        user_id=user_id,
        content=content,
        source={
            "cpu_id": cpu_id,
            "kernel": kernel_id
        }
    )

    # TODO: Ensure directory exists
    SYSTEM_MESSAGES_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Append to system messages log
    with open(SYSTEM_MESSAGES_FILE, 'a') as f:
        f.write(message.to_jsonl_line() + '\n')

    # TODO: Part 3 connector would read this file and deliver to UI

    return message


# =============================================================================
# Invariant Checking (Ensures No Desync)
# =============================================================================

def check_ui_kernel_sync(user_id: str, ui_source: str) -> bool:
    """
    Check if user's UI conversation is in sync with kernel memory

    Invariant: UI story and kernel memory must match

    Returns:
        True if in sync, False if desync detected

    TODO: Implement sync checking logic
    """
    raise NotImplementedError("Sync checking not implemented")


def repair_desync(user_id: str, ui_source: str) -> None:
    """
    Repair desync between UI and kernel memory

    Options:
        1. Re-ingest UI conversation into kernels
        2. Reset UI to match kernel state
        3. Manual merge with conflict resolution

    TODO: Implement desync repair
    """
    raise NotImplementedError("Desync repair not implemented")


# =============================================================================
# Example Integration (Pseudo-code)
# =============================================================================

def example_part3_integration():
    """
    Example showing how Part 3 would integrate with Parts 1 & 2

    This is PSEUDO-CODE only - not functional.
    """

    # Option 1: Sandboxed UI + Connector
    # ----------------------------------
    # while True:
    #     # Read from user's ChatGPT UI
    #     user_event = read_user_message_from_ui("chatgpt_ui")
    #     if user_event:
    #         # Ingest into system
    #         ingest_user_event(user_event)
    #
    #     # Check for system messages to deliver
    #     system_msg = read_latest_system_message()
    #     if system_msg:
    #         # Write back to user's UI
    #         write_system_message_to_ui(system_msg, "chatgpt_ui")

    # Option 2: System-Native Unified UI
    # -----------------------------------
    # while True:
    #     # Get user input directly
    #     user_event = unified_ui_get_user_input()
    #     if user_event:
    #         ingest_user_event(user_event)
    #
    #     # Display system messages directly
    #     system_msg = generate_system_response(user_event)
    #     unified_ui_display_message(system_msg)

    pass


# =============================================================================
# Status & Next Steps
# =============================================================================

"""
Part 3 Status: DESIGNED, NOT IMPLEMENTED

What's Ready:
✅ UserEvent and SystemToUserMessage types defined (spark_plug_types.py)
✅ Integration points clearly identified (this file)
✅ Two implementation options documented
✅ Invariants specified (no desync between UI and kernels)

What's NOT Ready:
❌ Actual UI connector code
❌ Sandboxed UI reading/writing logic
❌ Unified UI implementation
❌ Sync checking and repair
❌ Contraction engine auto-trigger on UserEvent

Next Steps (When Ready to Implement Part 3):
1. Choose implementation option (3.1 or 3.2)
2. If 3.1: Build connector for specific UI (ChatGPT, Claude)
3. If 3.2: Build unified UI (web or TUI)
4. Implement ingest_user_event() fully
5. Wire emit_system_message() to UI delivery
6. Add sync checking to prevent desync
7. Test with real user conversations

Design Principle:
    Parts 1 & 2 are built so Part 3 can attach WITHOUT redesign.
    This stub proves the integration points exist and are clear.
"""
