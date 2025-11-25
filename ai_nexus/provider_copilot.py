"""GitHub Copilot Agent Backend Provider (Best-Effort)"""

import os
import json
from typing import List, Dict, Optional

def call_github_copilot(
    agent_id: str,
    prior_messages: List[Dict],
    session_goal: str,
    max_tokens: int = 2048
) -> Dict:
    """
    Call GitHub Copilot Agent backend for tri-agent session

    Note: This is best-effort. GitHub Copilot Agent primarily works through
    GitHub UI/workflows. Direct API access may be limited.

    Args:
        agent_id: Agent identifier ("github_copilot_agent")
        prior_messages: List of prior messages in thread
        session_goal: Description of session purpose
        max_tokens: Maximum tokens in response

    Returns:
        Dict with 'content', 'model', 'tokens' keys
    """

    # v0.1: GitHub Copilot Agent doesn't have a direct backend API
    # This is a stub that can be enhanced when/if API access becomes available

    return {
        "content": f"""[GitHub Copilot Agent - Participation Limited in v0.1]

I'm currently designed to work through GitHub Issues and PRs rather than direct backend calls.

Session goal understood: {session_goal}

For v0.1, I recommend:
1. Post session summary to GitHub Issue for my review
2. I can respond via issue comments
3. Or create PRs based on discussion outcomes

Future versions may enable direct backend participation.
""",
        "model": "github_copilot_agent_stub_v0.1",
        "tokens": 100,
        "error": "stub_implementation"
    }

    # Future implementation might look like:
    # - Use GitHub API with Copilot endpoints (if/when available)
    # - Or trigger AI-intake workflow programmatically
    # - Or use GitHub Copilot Chat API (if exposed)
