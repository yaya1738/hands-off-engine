"""GitHub Copilot Agent Backend Provider

Provides integration between GitHub Copilot and the AI Nexus coordination system.
Copilot operates through GitHub's native features (Issues, PRs, Actions) rather
than direct API calls.
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

# Coordination file path
COORDINATION_DIR = Path(__file__).parent.parent / "ai" / "coordination"

# Valid response message types for coordination
COPILOT_RESPONSE_TYPES = ['response', 'info']

# Token estimation multiplier (words * multiplier = approximate tokens)
# Note: This is a rough estimate. For accurate counting, use tiktoken or similar
TOKEN_ESTIMATE_MULTIPLIER = 1.5


def _estimate_tokens(text: str) -> int:
    """
    Estimate token count from text.
    
    Note: This is a rough approximation. For accurate token counting,
    use tiktoken or the provider's tokenizer.
    
    Args:
        text: Text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    word_count = len(text.split())
    return int(word_count * TOKEN_ESTIMATE_MULTIPLIER)


def _truncate_at_word_boundary(text: str, max_chars: int) -> str:
    """
    Truncate text at a word boundary.
    
    Args:
        text: Text to truncate
        max_chars: Maximum characters to keep
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_chars:
        return text
    
    # Find last space before max_chars
    truncation_point = text.rfind(' ', 0, max_chars)
    
    # If no space found, just truncate at max_chars
    if truncation_point == -1:
        truncation_point = max_chars
    
    return text[:truncation_point] + "..."


def call_github_copilot(
    agent_id: str,
    prior_messages: List[Dict],
    session_goal: str,
    max_tokens: int = 2048
) -> Dict:
    """
    Call GitHub Copilot Agent backend for tri-agent session

    GitHub Copilot operates through:
    1. GitHub Issues/PRs - Primary interaction surface
    2. ai/coordination/messages.jsonl - Agent-to-agent communication
    3. GitHub Actions workflows - Automated triggers

    Args:
        agent_id: Agent identifier ("github_copilot_agent")
        prior_messages: List of prior messages in thread
        session_goal: Description of session purpose
        max_tokens: Maximum tokens in response

    Returns:
        Dict with 'content', 'model', 'tokens' keys
    """
    # Check if there's a pending response in coordination messages
    pending_response = _check_coordination_messages(prior_messages, session_goal)
    
    if pending_response:
        return {
            "content": pending_response,
            "model": "github_copilot_via_coordination",
            "tokens": _estimate_tokens(pending_response)
        }

    # Queue the request for Copilot via coordination file
    request_id = _queue_copilot_request(session_goal, prior_messages)
    
    return {
        "content": f"""[GitHub Copilot Agent - Request Queued]

Session goal: {session_goal}
Request ID: {request_id}

**Integration Modes:**

1. **GitHub Actions** (Automatic)
   - Copilot responds via `.github/workflows/agent-coordination-notify.yml`
   - Triggered when coordination files are updated
   - Creates/updates GitHub Issues for visibility

2. **File-Based Coordination** (Async)
   - Check `ai/coordination/messages.jsonl` for responses
   - Copilot writes responses when processing PRs/Issues

3. **Direct GitHub Interface**
   - Post to AI Intake issue for `/plan` commands
   - Copilot can respond via PR reviews and comments

**Current Status:**
- Request queued in coordination system
- Copilot will process when activated via GitHub
- Response will appear in messages.jsonl
""",
        "model": "github_copilot_agent_v0.2",
        "tokens": 150,
        "request_id": request_id,
        "integration_type": "async_coordination"
    }


def _check_coordination_messages(prior_messages: List[Dict], session_goal: str) -> Optional[str]:
    """
    Check if Copilot has already responded in coordination messages
    
    Returns the most recent Copilot response if available
    """
    messages_file = COORDINATION_DIR / "messages.jsonl"
    
    if not messages_file.exists():
        return None
    
    copilot_responses = []
    try:
        with open(messages_file, 'r') as f:
            for line in f:
                if line.strip():
                    msg = json.loads(line)
                    if msg.get('from') == 'copilot' and msg.get('type') in COPILOT_RESPONSE_TYPES:
                        copilot_responses.append(msg)
    except Exception:
        return None
    
    if not copilot_responses:
        return None
    
    # Return the most recent response
    latest = copilot_responses[-1]
    return f"[From Copilot at {latest.get('timestamp', 'unknown')}]\n\n{latest.get('message', '')}"


def _queue_copilot_request(session_goal: str, prior_messages: List[Dict]) -> str:
    """
    Queue a request for Copilot in the coordination system
    
    Returns a request ID for tracking
    """
    request_id = f"req_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    
    messages_file = COORDINATION_DIR / "messages.jsonl"
    
    # Build context from prior messages
    context_summary = "No prior context"
    if prior_messages:
        last_few = prior_messages[-3:]  # Last 3 messages
        context_summary = " | ".join([
            f"{m.get('from_agent', 'unknown')}: {_truncate_at_word_boundary(m.get('content', ''), 100)}"
            for m in last_few
        ])
    
    coordination_message = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "from": "ai_nexus",
        "to": "copilot",
        "type": "request",
        "message": f"Backend session request - Goal: {session_goal}",
        "context": {
            "request_id": request_id,
            "session_goal": session_goal,
            "prior_context": context_summary,
            "source": "tri_agent_session"
        }
    }
    
    try:
        COORDINATION_DIR.mkdir(parents=True, exist_ok=True)
        with open(messages_file, 'a') as f:
            f.write(json.dumps(coordination_message) + '\n')
    except Exception as e:
        # Graceful degradation - log but don't fail
        print(f"Warning: Could not queue Copilot request: {e}")
    
    return request_id


def post_copilot_response(
    message: str,
    response_type: str = "response",
    context: Optional[Dict] = None
) -> bool:
    """
    Post a response from Copilot to the coordination system
    
    This is called by Copilot when processing tasks.
    
    Args:
        message: Response message content
        response_type: Type of message (response, info, request)
        context: Additional context dictionary
        
    Returns:
        True if successfully posted
    """
    messages_file = COORDINATION_DIR / "messages.jsonl"
    
    coordination_message = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "from": "copilot",
        "to": "all",
        "type": response_type,
        "message": message,
        "context": context or {}
    }
    
    try:
        COORDINATION_DIR.mkdir(parents=True, exist_ok=True)
        with open(messages_file, 'a') as f:
            f.write(json.dumps(coordination_message) + '\n')
        return True
    except Exception as e:
        print(f"Error posting Copilot response: {e}")
        return False


def get_copilot_integration_status() -> Dict:
    """
    Get current status of Copilot integration
    
    Returns:
        Dict with integration status information
    """
    status_file = COORDINATION_DIR / "status.json"
    messages_file = COORDINATION_DIR / "messages.jsonl"
    
    # Check for status.json
    copilot_status = "unknown"
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
                copilot_status = status.get('autonomous_mode', {}).get('copilot', False)
        except Exception:
            pass
    
    # Count recent Copilot messages
    copilot_messages = 0
    if messages_file.exists():
        try:
            with open(messages_file, 'r') as f:
                for line in f:
                    if line.strip():
                        msg = json.loads(line)
                        if msg.get('from') == 'copilot':
                            copilot_messages += 1
        except Exception:
            pass
    
    return {
        "autonomous_mode": copilot_status,
        "total_messages": copilot_messages,
        "coordination_file": str(messages_file),
        "integration_version": "0.2",
        "capabilities": [
            "github_issues_prs",
            "file_based_coordination",
            "github_actions_workflows",
            "ai_intake_commands"
        ]
    }
