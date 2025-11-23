#!/usr/bin/env python3
"""
AI Intake Handler for Hands-Off Engine

Handles commands posted as issue comments on the designated AI Intake issue.
Currently supports: /plan, /collaborate, /status
Enables multi-AI coordination for continuous collaboration.
"""
import json
import os
import sys
from pathlib import Path

import requests
from openai import OpenAI

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from multi_ai_coordinator import MultiAICoordinator


def load_text(path: str) -> str:
    """Load text from a file, return warning if not found."""
    p = Path(path)
    if not p.is_file():
        return f"[WARN] File not found: {path}"
    return p.read_text(encoding="utf-8")


def post_comment(repo: str, issue_number: int, body: str) -> None:
    """Post a comment back to the issue via GitHub API."""
    token = os.environ["GITHUB_TOKEN"]
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")

    url = f"{api_url}/repos/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"body": body}

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()


def run_plan(event: dict) -> None:
    """Handle /plan command: generate a roadmap-aligned plan."""
    repo = os.environ["GITHUB_REPOSITORY"]
    issue = event["issue"]
    issue_number = issue["number"]
    comment_body = event["comment"]["body"]

    # Load policy + research report
    policy_text = load_text("AI_POLICY.md")
    report_text = load_text(
        "termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md"
    )
    issue_description = issue.get("body") or ""

    # Set up OpenAI client
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    system_msg = (
        "You are the planning assistant for the 'Hands-Off Engine' repository. "
        "Your job is to propose concrete, implementable steps that follow the "
        "AI policy and the research roadmap. You output clear, numbered steps "
        "and reference repo paths where relevant."
    )

    user_prompt = f"""
You were invoked by a /plan command on the AI Intake issue.

[AI_POLICY.md]
{policy_text}

[RESEARCH_REPORT]
{report_text}

[ISSUE_DESCRIPTION]
{issue_description}

[COMMENT]
{comment_body}

TASK:
- Produce a concise plan of next steps for this repository.
- Focus on high-leverage automation work (not just docs).
- Output a short intro, then a numbered list of concrete tasks.
- For each task, mention which files/folders are likely involved.
- Keep it short enough to fit comfortably in a single GitHub comment.
""".strip()

    # Call OpenAI Chat Completion (modern SDK)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    plan_text = response.choices[0].message.content

    comment = (
        "### 🤖 AI Intake – Plan\n\n"
        "Here is a roadmap-aligned plan based on the current AI policy and "
        "research report:\n\n"
        f"{plan_text}\n\n"
        "---\n"
        "_Generated automatically by `ai_intake_handler.py`._"
    )

    post_comment(repo, issue_number, comment)


def run_collaborate(event: dict) -> None:
    """Handle /collaborate command: start multi-AI collaboration."""
    repo = os.environ["GITHUB_REPOSITORY"]
    issue = event["issue"]
    issue_number = issue["number"]
    comment_body = event["comment"]["body"]
    comment_user = event["comment"]["user"]["login"]
    
    # Parse the command: /collaborate <topic> [participants]
    lines = comment_body.strip().split('\n')
    command_line = lines[0].strip()
    
    # Extract topic and participants
    parts = command_line.split(maxsplit=1)
    if len(parts) < 2:
        topic = "General collaboration"
        participants = ["chatgpt", "claude-cli", "copilot"]
    else:
        # Topic is everything after /collaborate
        topic = parts[1].strip()
        participants = ["chatgpt", "claude-cli", "copilot"]
    
    # Get additional context from remaining lines
    additional_context = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
    
    # Initialize coordinator
    repo_root = Path(__file__).parent.parent
    coordinator = MultiAICoordinator(repo_root)
    
    # Start collaboration
    collab_id = coordinator.start_collaboration(
        topic=topic,
        initiating_ai=comment_user,
        participants=participants,
        context={
            'issue_number': issue_number,
            'issue_title': issue.get('title', ''),
            'additional_context': additional_context
        },
        priority='normal'
    )
    
    # Post initial message to collaboration
    coordinator.add_message(
        collaboration_id=collab_id,
        from_ai=comment_user,
        to_ai=None,  # Broadcast
        message=f"Starting collaboration on: {topic}\n\n{additional_context}",
        message_type='initiation'
    )
    
    # Respond to the issue
    comment = (
        f"### 🤝 Multi-AI Collaboration Started\n\n"
        f"**Topic:** {topic}\n\n"
        f"**Collaboration ID:** `{collab_id[:8]}...`\n\n"
        f"**Participants:** {', '.join(participants)}\n\n"
        f"This collaboration will continue autonomously across AI systems. "
        f"Each AI will check for messages and contribute when invoked.\n\n"
        f"Use `/collaborate-status {collab_id[:8]}` to check progress.\n\n"
        "---\n"
        "_Powered by Multi-AI Coordinator_"
    )
    
    post_comment(repo, issue_number, comment)


def run_status(event: dict) -> None:
    """Handle /status command: show multi-AI coordination status."""
    repo = os.environ["GITHUB_REPOSITORY"]
    issue = event["issue"]
    issue_number = issue["number"]
    
    # Initialize coordinator
    repo_root = Path(__file__).parent.parent
    coordinator = MultiAICoordinator(repo_root)
    
    # Get active collaborations
    active_collabs = coordinator.get_active_collaborations()
    
    # Build status message
    if not active_collabs:
        status_msg = "### 📊 Multi-AI Status\n\n**No active collaborations**\n\nUse `/collaborate <topic>` to start one."
    else:
        status_msg = "### 📊 Multi-AI Status\n\n**Active Collaborations:**\n\n"
        for collab in active_collabs:
            status_msg += f"- **{collab['topic']}** (`{collab['id'][:8]}...`)\n"
            status_msg += f"  - Participants: {', '.join(collab['participants'])}\n"
            status_msg += f"  - Messages: {collab['message_count']}\n"
            status_msg += f"  - Priority: {collab['priority']}\n\n"
    
    # Add autonomous task queue status
    try:
        sys.path.insert(0, str(repo_root / 'scripts'))
        from autonomous_task_queue import AutonomousTaskQueue
        queue = AutonomousTaskQueue(repo_root)
        pending_tasks = queue.get_all_tasks()
        
        status_msg += f"\n**Autonomous Task Queue:** {len(pending_tasks)} pending tasks\n"
    except (ImportError, ModuleNotFoundError) as e:
        status_msg += f"\n*Could not load task queue module: {e}*\n"
    except (AttributeError, KeyError, TypeError, ValueError) as e:
        status_msg += f"\n*Error reading task queue: {e}*\n"
    except Exception as e:
        # Catch any other unexpected errors
        status_msg += f"\n*Unexpected error loading task queue status: {e}*\n"
    
    status_msg += "\n---\n_Updated automatically by AI Intake Handler_"
    
    post_comment(repo, issue_number, status_msg)


def main() -> None:
    """Main entry point for the AI Intake handler."""
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH not set")

    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    # Only handle issue_comment events
    if event.get("action") != "created":
        print("Not a newly created comment, exiting.")
        return

    issue = event.get("issue") or {}
    issue_number = issue.get("number")
    comment = event.get("comment") or {}
    comment_body = (comment.get("body") or "").strip()

    if issue_number is None or not comment_body:
        print("No issue number or comment body, exiting.")
        return

    # Restrict to the AI Intake issue (default: 1, configurable via env)
    ai_issue_number_env = os.getenv("AI_INTAKE_ISSUE_NUMBER")
    if ai_issue_number_env:
        ai_issue_number = int(ai_issue_number_env)
    else:
        ai_issue_number = 1  # default

    if issue_number != ai_issue_number:
        print(f"Issue #{issue_number} is not AI Intake (#{ai_issue_number}), skipping.")
        return

    # Only react to commands starting with '/'
    first_line = comment_body.splitlines()[0].strip()
    if not first_line.startswith("/"):
        print("No leading slash command, skipping.")
        return

    if first_line.startswith("/plan"):
        print("Handling /plan command...")
        run_plan(event)
    elif first_line.startswith("/collaborate"):
        print("Handling /collaborate command...")
        run_collaborate(event)
    elif first_line.startswith("/status"):
        print("Handling /status command...")
        run_status(event)
    else:
        print(f"Command {first_line} not implemented yet, skipping for now.")


if __name__ == "__main__":
    main()
