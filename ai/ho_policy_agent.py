#!/usr/bin/env python3
"""
HANDS-OFF ENGINE — BATCH 19
LLM Decision Agent (Policy Brain v1)

DRYRUN-only • Safe • Offline-capable • High-level reasoning layer

This module provides the first AI decision agent that:
1. Reads state/hands_off_brain.json
2. Builds an LLM prompt summarizing system state
3. Produces a proposed action plan stored as state/brain_policy.json

SAFETY GUARANTEES:
- DRYRUN ONLY - no trades, no executor changes, no Polymarket calls
- NO network usage (LLM function must be injected)
- ONLY reads hands_off_brain.json
- ONLY writes brain_policy.json
- NEVER crashes on malformed LLM output
"""

import json
import os
import re
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional


def load_brain_state(state_dir: str = "state") -> tuple[Dict[str, Any], List[str]]:
    """
    Load the brain state from hands_off_brain.json.

    Returns:
        (brain_data, errors) tuple
        - brain_data: dict with brain state (empty dict if missing/malformed)
        - errors: list of error messages
    """
    errors = []
    brain_path = os.path.join(state_dir, "hands_off_brain.json")

    if not os.path.exists(brain_path):
        errors.append(f"Brain file not found: {brain_path}")
        return {}, errors

    try:
        with open(brain_path, 'r') as f:
            brain_data = json.load(f)
        return brain_data, errors
    except json.JSONDecodeError as e:
        errors.append(f"Malformed brain JSON: {e}")
        return {}, errors
    except Exception as e:
        errors.append(f"Error reading brain file: {e}")
        return {}, errors


def build_llm_prompt(brain_data: Dict[str, Any]) -> str:
    """
    Build an LLM prompt from the brain state.

    Args:
        brain_data: The loaded brain state

    Returns:
        Formatted prompt string for the LLM
    """
    prompt = """You are the Policy Brain for the Hands-Off Engine.

Your role is to analyze the current system state and propose a safe action plan.

CRITICAL CONSTRAINTS:
- DRYRUN ONLY - no live trades or executor modifications
- Propose only safe, observational, or analytical actions
- Focus on health checks, summaries, and DRYRUN autoloop modes

CURRENT SYSTEM STATE:
"""

    if not brain_data:
        prompt += "\n[Brain state unavailable or empty]\n"
    else:
        # Add brain status if available
        if "status" in brain_data:
            prompt += f"\nStatus: {brain_data['status']}\n"

        # Add health information
        if "health" in brain_data:
            prompt += f"\nHealth: {json.dumps(brain_data['health'], indent=2)}\n"

        # Add summary
        if "summary" in brain_data:
            prompt += f"\nSummary: {json.dumps(brain_data['summary'], indent=2)}\n"

        # Add recent history analytics
        if "history_analytics" in brain_data:
            prompt += f"\nHistory Analytics: {json.dumps(brain_data['history_analytics'], indent=2)}\n"

        # Add AI loop status
        if "ai_loop" in brain_data:
            prompt += f"\nAI Loop Status: {json.dumps(brain_data['ai_loop'], indent=2)}\n"

        # Add polymarket pipeline info
        if "polymarket_pipeline" in brain_data:
            prompt += f"\nPolymarket Pipeline: {json.dumps(brain_data['polymarket_pipeline'], indent=2)}\n"

    prompt += """

TASK:
Based on the above state, propose a list of safe actions the system should take next.

Return your response as a JSON object with this structure:
{
  "brain_status": "ok|warn|error|null",
  "proposed_actions": [
    {"type": "summary"},
    {"type": "health-check"},
    {"type": "autoloop", "mode": "DRYRUN"}
  ],
  "notes": ["Brief explanations of your reasoning"]
}

Valid action types:
- "summary" - Generate a new brain summary
- "health-check" - Run system health diagnostics
- "autoloop" - Run AI loop (MUST specify mode: "DRYRUN")
- "analyze-history" - Analyze historical data
- "polymarket-analysis" - Analyze Polymarket data (DRYRUN only)

Remember: DRYRUN ONLY. No live trades or modifications.

Respond with the JSON object:"""

    return prompt


def parse_llm_response(response: str) -> tuple[Dict[str, Any], List[str]]:
    """
    Parse LLM response into structured policy data.

    Attempts multiple parsing strategies:
    1. Extract JSON block from response
    2. Parse bullet points heuristically
    3. Return minimal fallback

    Args:
        response: Raw LLM output string

    Returns:
        (policy_dict, errors) tuple
    """
    errors = []

    # Strategy 1: Try to extract and parse JSON block
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            json_str = json_match.group(0)
            parsed = json.loads(json_str)

            # Validate required fields
            if "proposed_actions" not in parsed:
                parsed["proposed_actions"] = []
            if not isinstance(parsed["proposed_actions"], list):
                errors.append("proposed_actions is not a list, converting")
                parsed["proposed_actions"] = []

            if "notes" not in parsed:
                parsed["notes"] = []
            if not isinstance(parsed["notes"], list):
                parsed["notes"] = [str(parsed["notes"])] if parsed["notes"] else []

            if "brain_status" not in parsed:
                parsed["brain_status"] = "null"

            return parsed, errors

        except json.JSONDecodeError as e:
            errors.append(f"JSON parse failed: {e}")

    # Strategy 2: Heuristic parsing of bullet points
    policy = {
        "brain_status": "null",
        "proposed_actions": [],
        "notes": []
    }

    lines = response.split('\n')
    for line in lines:
        line = line.strip()

        # Look for action-like patterns
        if re.match(r'^[-*•]\s*(run\s+)?autoloop', line, re.IGNORECASE):
            policy["proposed_actions"].append({"type": "autoloop", "mode": "DRYRUN"})
        elif re.match(r'^[-*•]\s*(run\s+|generate\s+)?summary', line, re.IGNORECASE):
            policy["proposed_actions"].append({"type": "summary"})
        elif re.match(r'^[-*•]\s*(run\s+)?health', line, re.IGNORECASE):
            policy["proposed_actions"].append({"type": "health-check"})
        elif re.match(r'^[-*•]\s*analyze.*history', line, re.IGNORECASE):
            policy["proposed_actions"].append({"type": "analyze-history"})
        elif re.match(r'^[-*•]\s*polymarket', line, re.IGNORECASE):
            policy["proposed_actions"].append({"type": "polymarket-analysis", "mode": "DRYRUN"})

        # Collect notes (non-action lines)
        elif line and not line.startswith('{') and not line.startswith('}'):
            if len(policy["notes"]) < 10:  # Limit notes
                policy["notes"].append(line)

    # Strategy 3: Fallback if nothing parsed
    if not policy["proposed_actions"]:
        errors.append("Could not parse LLM output, using fallback")
        policy["proposed_actions"] = [{"type": "summary"}]
        policy["notes"] = ["LLM output was unparseable, defaulting to summary action"]

    return policy, errors


def build_policy_recommendation(
    state_dir: str = "state",
    llm_fn: Optional[Callable[[str], str]] = None,
    model_name: str = "claude-3.5-sonnet"
) -> Dict[str, Any]:
    """
    Build a policy recommendation by analyzing the brain state.

    This is the core function that:
    1. Loads hands_off_brain.json
    2. Builds an LLM prompt summarizing system state
    3. Calls the provided llm_fn(prompt) -> string
    4. Parses model output into structured policy dict
    5. Returns the policy dict

    Args:
        state_dir: Directory containing state files (default: "state")
        llm_fn: Function that takes a prompt string and returns LLM response
                If None, returns minimal fallback policy
        model_name: Name of the model being used (for metadata)

    Returns:
        Policy dict with structure:
        {
          "generated_at": "ISO timestamp",
          "model_name": "...",
          "brain_status": "ok|warn|error|null",
          "proposed_actions": [...],
          "notes": [...],
          "errors": [...]
        }
    """
    errors = []

    # Load brain state
    brain_data, load_errors = load_brain_state(state_dir)
    errors.extend(load_errors)

    # If no LLM function provided, return fallback
    if llm_fn is None:
        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "model_name": "none (fallback)",
            "brain_status": "null",
            "proposed_actions": [{"type": "summary"}],
            "notes": ["No LLM function provided, using fallback policy"],
            "errors": errors
        }

    # Build prompt
    prompt = build_llm_prompt(brain_data)

    # Call LLM
    try:
        response = llm_fn(prompt)
    except Exception as e:
        errors.append(f"LLM call failed: {e}")
        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "model_name": model_name,
            "brain_status": "error",
            "proposed_actions": [{"type": "summary"}],
            "notes": ["LLM call failed, using fallback"],
            "errors": errors
        }

    # Parse response
    parsed_policy, parse_errors = parse_llm_response(response)
    errors.extend(parse_errors)

    # Build final policy dict
    policy = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "model_name": model_name,
        "brain_status": parsed_policy.get("brain_status", "null"),
        "proposed_actions": parsed_policy.get("proposed_actions", []),
        "notes": parsed_policy.get("notes", []),
        "errors": errors
    }

    return policy


def write_policy_recommendation(
    state_dir: str = "state",
    llm_fn: Optional[Callable[[str], str]] = None,
    model_name: str = "claude-3.5-sonnet"
) -> Dict[str, Any]:
    """
    Build and write policy recommendation to state/brain_policy.json.

    Wrapper function that:
    - Calls build_policy_recommendation()
    - Writes state/brain_policy.json
    - Returns policy dict

    Args:
        state_dir: Directory containing state files (default: "state")
        llm_fn: Function that takes a prompt string and returns LLM response
        model_name: Name of the model being used

    Returns:
        Policy dict (same as build_policy_recommendation)

    Raises:
        Exception: If writing file fails catastrophically
    """
    # Build policy
    policy = build_policy_recommendation(state_dir, llm_fn, model_name)

    # Ensure state directory exists
    os.makedirs(state_dir, exist_ok=True)

    # Write to file
    policy_path = os.path.join(state_dir, "brain_policy.json")
    try:
        with open(policy_path, 'w') as f:
            json.dump(policy, f, indent=2)
    except Exception as e:
        # This is catastrophic - we must report it
        policy["errors"].append(f"Failed to write policy file: {e}")
        raise

    return policy


def main():
    """CLI interface for the policy agent."""
    parser = argparse.ArgumentParser(
        description="Hands-Off Engine Policy Agent (Batch 19) - DRYRUN only"
    )
    parser.add_argument(
        "--state-dir",
        default="state",
        help="Directory containing state files (default: state)"
    )
    parser.add_argument(
        "--model",
        default="claude-3.5-sonnet",
        help="Model name for metadata (default: claude-3.5-sonnet)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    try:
        # Create dummy LLM function (no real LLM in CLI mode)
        def dummy_llm(prompt: str) -> str:
            return json.dumps({
                "brain_status": "ok",
                "proposed_actions": [
                    {"type": "summary"},
                    {"type": "health-check"}
                ],
                "notes": ["Dummy LLM response - provide real llm_fn for actual analysis"]
            })

        # Build and write policy
        policy = write_policy_recommendation(
            state_dir=args.state_dir,
            llm_fn=dummy_llm,
            model_name=args.model
        )

        # Output results
        if args.verbose:
            print("=" * 60)
            print("HANDS-OFF ENGINE - POLICY AGENT (BATCH 19)")
            print("=" * 60)
            print(f"\nGenerated at: {policy['generated_at']}")
            print(f"Model: {policy['model_name']}")
            print(f"Brain status: {policy['brain_status']}")

            print(f"\nProposed actions ({len(policy['proposed_actions'])}):")
            for i, action in enumerate(policy['proposed_actions'], 1):
                print(f"  {i}. {action}")

            if policy['notes']:
                print(f"\nNotes ({len(policy['notes'])}):")
                for note in policy['notes']:
                    print(f"  - {note}")

            if policy['errors']:
                print(f"\nErrors ({len(policy['errors'])}):")
                for error in policy['errors']:
                    print(f"  ! {error}")

            print(f"\nPolicy written to: {args.state_dir}/brain_policy.json")
            print("=" * 60)
        else:
            print(f"Policy generated: {args.state_dir}/brain_policy.json")
            if policy['errors']:
                print(f"Warnings: {len(policy['errors'])} error(s) logged")

        sys.exit(0)

    except Exception as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
