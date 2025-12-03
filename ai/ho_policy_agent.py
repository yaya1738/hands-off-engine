#!/usr/bin/env python3
"""
Batch 19: Policy Agent (Policy Brain v1)
Reads brain summary and generates policy recommendations.

Policy agent that:
- Reads brain state
- Builds LLM prompts
- Parses LLM responses (with fallback)
- Generates policy recommendations
- Writes policy JSON file
"""

import json
import argparse
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable


def load_brain_state(state_dir: str) -> Optional[Dict]:
    """
    Load brain state from file.

    Args:
        state_dir: Directory containing state files

    Returns:
        Brain state dict or None if not found
    """
    brain_path = Path(state_dir) / "hands_off_brain.json"

    if not brain_path.exists():
        return None

    try:
        with open(brain_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        return None


def build_llm_prompt(brain_state: Optional[Dict]) -> str:
    """
    Build prompt for LLM policy recommendation.

    Args:
        brain_state: Current brain state (can be None)

    Returns:
        Formatted prompt string
    """
    if brain_state:
        state_summary = json.dumps(brain_state, indent=2)[:2000]  # Truncate
    else:
        state_summary = "Brain state not available"

    prompt = f"""Policy Brain - Autonomous System Policy Agent

You are analyzing the current system state and recommending safe actions.

Current System State:
{state_summary}

Based on this state, provide policy recommendations in JSON format:
{{
    "brain_status": "ok|warning|error",
    "proposed_actions": [
        {{"type": "summary"}},
        {{"type": "health-check"}},
        {{"type": "autoloop", "mode": "DRYRUN"}}
    ],
    "notes": ["explanation 1", "explanation 2"]
}}

Valid action types:
- summary: Generate status summary
- health-check: Run system health check
- autoloop: Run automation loop (always use mode: "DRYRUN")
- polymarket-analysis: Analyze market data
- analyze-history: Analyze historical data

Return ONLY valid JSON. All actions must be safe DRYRUN operations.
"""
    return prompt


def parse_llm_response(response: str) -> Dict:
    """
    Parse LLM response into structured policy.

    Args:
        response: Raw LLM response string

    Returns:
        Parsed policy dict with proposed_actions, notes, errors
    """
    result = {
        "brain_status": "unknown",
        "proposed_actions": [],
        "notes": [],
        "errors": []
    }

    if not response:
        result["errors"].append("Empty LLM response")
        result["proposed_actions"] = [{"type": "summary"}]
        return result

    # Try to parse as JSON first
    try:
        # Find JSON in response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            parsed = json.loads(json_match.group())

            result["brain_status"] = parsed.get("brain_status", "ok")
            result["proposed_actions"] = parsed.get("proposed_actions", [])
            result["notes"] = parsed.get("notes", [])

            # Validate actions
            if not result["proposed_actions"]:
                result["proposed_actions"] = [{"type": "summary"}]

            return result
    except json.JSONDecodeError:
        pass

    # Fallback: Parse bullet points
    result["errors"].append("Could not parse JSON, attempting bullet point parsing")

    lines = response.split('\n')
    actions = []

    for line in lines:
        line_lower = line.lower().strip()

        # Look for action keywords
        if 'autoloop' in line_lower or 'auto-loop' in line_lower:
            actions.append({"type": "autoloop", "mode": "DRYRUN"})
        elif 'summary' in line_lower:
            actions.append({"type": "summary"})
        elif 'health' in line_lower and 'check' in line_lower:
            actions.append({"type": "health-check"})
        elif 'history' in line_lower and 'analy' in line_lower:
            actions.append({"type": "analyze-history"})
        elif 'polymarket' in line_lower:
            actions.append({"type": "polymarket-analysis"})

    if actions:
        result["proposed_actions"] = actions
        result["brain_status"] = "ok"
    else:
        # Ultimate fallback
        result["proposed_actions"] = [{"type": "summary"}]
        result["brain_status"] = "unknown"

    return result


def build_policy_recommendation(
    state_dir: str,
    llm_fn: Optional[Callable[[str], str]] = None,
    model_name: str = "default"
) -> Dict:
    """
    Build policy recommendation.

    Args:
        state_dir: Directory containing state files
        llm_fn: Optional function to call LLM (prompt -> response)
        model_name: Name of the model being used

    Returns:
        Policy recommendation dict
    """
    errors = []

    # Load brain state
    brain_state = load_brain_state(state_dir)
    if brain_state is None:
        errors.append("Brain file not found or could not be loaded")

    # Build prompt
    prompt = build_llm_prompt(brain_state)

    # Get LLM response
    if llm_fn:
        try:
            response = llm_fn(prompt)
            parsed = parse_llm_response(response)
        except Exception as e:
            errors.append(f"LLM call failed: {e}")
            parsed = {
                "brain_status": "error",
                "proposed_actions": [{"type": "summary"}],
                "notes": [],
                "errors": [str(e)]
            }
    else:
        # No LLM function - return fallback
        parsed = {
            "brain_status": "unknown",
            "proposed_actions": [{"type": "summary"}],
            "notes": ["No LLM function provided, using fallback"],
            "errors": []
        }
        model_name = "none (fallback)"

    # Build final policy
    policy = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "model_name": model_name,
        "brain_status": parsed.get("brain_status", "unknown"),
        "proposed_actions": parsed.get("proposed_actions", [{"type": "summary"}]),
        "notes": parsed.get("notes", []),
        "errors": errors + parsed.get("errors", [])
    }

    return policy


def write_policy_recommendation(
    state_dir: str,
    llm_fn: Optional[Callable[[str], str]] = None,
    model_name: str = "default"
) -> Dict:
    """
    Build and write policy recommendation.

    Args:
        state_dir: Directory containing state files
        llm_fn: Optional function to call LLM
        model_name: Name of the model being used

    Returns:
        Policy recommendation dict (also written to file)
    """
    policy = build_policy_recommendation(state_dir, llm_fn, model_name)

    # Write to file
    state_path = Path(state_dir)
    state_path.mkdir(parents=True, exist_ok=True)
    policy_path = state_path / "brain_policy.json"

    with open(policy_path, 'w') as f:
        json.dump(policy, f, indent=2)

    return policy


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Policy Agent - Generate policy recommendations")
    parser.add_argument("--state-dir", default="state", help="State directory path")
    parser.add_argument("--model", default="stub", help="Model name")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Run without LLM (stub mode)
    policy = write_policy_recommendation(
        state_dir=args.state_dir,
        llm_fn=None,
        model_name=args.model
    )

    if args.verbose:
        print("\n" + "=" * 60)
        print("POLICY RECOMMENDATION")
        print("=" * 60)
        print(json.dumps(policy, indent=2))
        print("=" * 60)
    else:
        print(f"Policy generated: {args.state_dir}/brain_policy.json")
