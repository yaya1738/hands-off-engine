#!/usr/bin/env python3
"""
AI Intake Handler for Hands-Off Engine

Handles commands posted as issue comments on the designated AI Intake issue.
Currently supports: /plan

Now integrated with AI Nexus audit logging and financial tracking.
"""
import json
import os
import sys
from pathlib import Path

import requests
from openai import OpenAI

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audit import AuditLogger, FinancialLedger
from ai_nexus import AIProvider, AIRequest, AIResponse, NexusCore, AIProviderType, OpenAIProvider


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

    # Initialize AI Nexus for audit logging and cost tracking
    audit_logger = AuditLogger()
    ledger = FinancialLedger()
    nexus = NexusCore(audit_logger=audit_logger, ledger=ledger)

    # Register OpenAI provider
    openai_provider = OpenAIProvider(audit_logger, ledger)
    nexus.register_provider(openai_provider)

    # Log the /plan command invocation
    audit_logger.log_event(
        component="ai.intake_handler",
        action="plan_command_invoked",
        metadata={
            "repo": repo,
            "issue_number": issue_number,
            "comment_length": len(comment_body)
        }
    )

    # Load policy + research report
    policy_text = load_text("AI_POLICY.md")
    report_text = load_text(
        "termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md"
    )
    issue_description = issue.get("body") or ""

    # Log data loading
    audit_logger.log_event(
        component="ai.intake_handler",
        action="load_policy_data",
        metadata={
            "policy_length": len(policy_text),
            "report_length": len(report_text),
            "issue_description_length": len(issue_description)
        }
    )

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

    # Create AI request through Nexus
    ai_request = AIRequest(
        provider_type=AIProviderType.OPENAI,
        action="plan_generation",
        prompt=user_prompt,
        system_message=system_msg,
        model="gpt-4o-mini",
        temperature=0.3,
        metadata={
            "repo": repo,
            "issue_number": issue_number
        }
    )

    # Execute through Nexus (logs costs automatically)
    ai_response = nexus.execute_request(ai_request)

    if not ai_response.success:
        error_msg = f"Failed to generate plan: {ai_response.error}"
        audit_logger.log_event(
            component="ai.intake_handler",
            action="plan_generation_failed",
            metadata={"error": ai_response.error},
            error=error_msg
        )
        # Post error comment
        post_comment(repo, issue_number, f"❌ Error generating plan: {ai_response.error}")
        return

    plan_text = ai_response.content

    # Log plan generation success
    audit_logger.log_event(
        component="ai.intake_handler",
        action="plan_generated",
        metadata={
            "model": ai_response.model_used,
            "tokens": ai_response.tokens_used,
            "cost": ai_response.cost,
            "plan_length": len(plan_text)
        },
        cost=ai_response.cost,
        outcome="success"
    )

    # Add cost information to the comment
    cost_info = (
        f"\n\n---\n"
        f"📊 **AI Nexus Metrics:**\n"
        f"- Model: {ai_response.model_used}\n"
        f"- Tokens: {ai_response.tokens_used['total']:,}\n"
        f"- Cost: ${ai_response.cost:.4f}\n"
        f"- Session: `{nexus.session_id[:8]}...`\n"
    )

    comment = (
        "### 🤖 AI Intake – Plan\n\n"
        "Here is a roadmap-aligned plan based on the current AI policy and "
        "research report:\n\n"
        f"{plan_text}\n\n"
        f"{cost_info}\n"
        "---\n"
        "_Generated automatically by `ai_intake_handler.py` via AI Nexus._"
    )

    try:
        post_comment(repo, issue_number, comment)
        # Log successful comment posting
        audit_logger.log_event(
            component="ai.intake_handler",
            action="comment_posted",
            metadata={
                "issue_number": issue_number,
                "comment_length": len(comment)
            },
            outcome="success"
        )
    except Exception as e:
        # Log error
        audit_logger.log_event(
            component="ai.intake_handler",
            action="comment_posting_failed",
            metadata={"issue_number": issue_number},
            error=str(e)
        )
        raise

    # Print session summary
    print("\n" + "="*80)
    print("AI NEXUS SESSION SUMMARY")
    print("="*80)
    summary = nexus.get_session_metrics()
    print(f"Session ID: {summary['session_id']}")
    print(f"Total Cost: ${summary['financial']['total_costs']:.4f}")
    print(f"ROI: {summary['financial']['roi_percent']:.2f}%")
    print("="*80 + "\n")


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
    else:
        print(f"Command {first_line} not implemented yet, skipping for now.")


if __name__ == "__main__":
    main()
