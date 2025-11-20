#!/usr/bin/env python3
"""
AI Intake Handler for Hands-Off Engine

Handles commands posted as issue comments on the designated AI Intake issue.
Currently supports: /plan
"""
import json
import os
import sys
from pathlib import Path

import requests
from openai import OpenAI

# Add audit logging
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from audit import get_audit_logger
    audit = get_audit_logger(component="ai.intake_handler")
except ImportError:
    audit = None


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
    import datetime
    session_id = f"ai_intake_plan_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    repo = os.environ["GITHUB_REPOSITORY"]
    issue = event["issue"]
    issue_number = issue["number"]
    comment_body = event["comment"]["body"]

    # Audit the request
    if audit:
        audit.log_action(
            action_type="ai_intake_command",
            action_data={
                "command": "/plan",
                "issue_number": issue_number,
                "repository": repo
            },
            session_id=session_id
        )

    # Load policy + research report
    policy_text = load_text("AI_POLICY.md")
    report_text = load_text(
        "termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md"
    )
    issue_description = issue.get("body") or ""

    # Audit data loading
    if audit:
        audit.log_data_fetch(
            source="policy_and_reports",
            params={
                "policy_file": "AI_POLICY.md",
                "report_file": "termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md"
            },
            success=True,
            session_id=session_id
        )

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
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )

        plan_text = response.choices[0].message.content
        
        # Audit AI decision
        if audit:
            audit.log_decision(
                decision_type="ai_plan_generation",
                inputs={
                    "model": "gpt-4o-mini",
                    "temperature": 0.3,
                    "prompt_length": len(user_prompt)
                },
                outputs={
                    "plan_length": len(plan_text),
                    "plan_preview": plan_text[:200] + "..." if len(plan_text) > 200 else plan_text
                },
                metadata={
                    "issue_number": issue_number,
                    "command": "/plan"
                },
                session_id=session_id
            )
    except Exception as e:
        # Audit AI error
        if audit:
            audit.log_error(
                error_type="OpenAI API Error",
                error_message=str(e),
                context={
                    "model": "gpt-4o-mini",
                    "command": "/plan",
                    "issue_number": issue_number
                },
                session_id=session_id
            )
        raise

    comment = (
        "### 🤖 AI Intake – Plan\n\n"
        "Here is a roadmap-aligned plan based on the current AI policy and "
        "research report:\n\n"
        f"{plan_text}\n\n"
        "---\n"
        "_Generated automatically by `ai_intake_handler.py`._"
    )

    post_comment(repo, issue_number, comment)
    
    # Audit comment posting
    if audit:
        audit.log_action(
            action_type="github_comment_posted",
            action_data={
                "issue_number": issue_number,
                "comment_length": len(comment)
            },
            result="success",
            session_id=session_id
        )


def main() -> None:
    """Main entry point for the AI Intake handler."""
    import datetime
    session_id = f"ai_intake_main_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
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

    # Audit command detection
    if audit:
        audit.log_action(
            action_type="ai_intake_invoked",
            action_data={
                "command": first_line,
                "issue_number": issue_number,
                "comment_length": len(comment_body)
            },
            session_id=session_id
        )

    if first_line.startswith("/plan"):
        print("Handling /plan command...")
        try:
            run_plan(event)
            if audit:
                audit.log_action(
                    action_type="ai_intake_command_completed",
                    action_data={
                        "command": "/plan",
                        "issue_number": issue_number
                    },
                    result="success",
                    session_id=session_id
                )
        except Exception as e:
            if audit:
                audit.log_error(
                    error_type="Command Execution Error",
                    error_message=str(e),
                    context={
                        "command": "/plan",
                        "issue_number": issue_number
                    },
                    session_id=session_id
                )
            raise
    else:
        print(f"Command {first_line} not implemented yet, skipping for now.")
        if audit:
            audit.log_action(
                action_type="ai_intake_command_not_implemented",
                action_data={
                    "command": first_line,
                    "issue_number": issue_number
                },
                session_id=session_id
            )


if __name__ == "__main__":
    main()
