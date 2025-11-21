#!/usr/bin/env python3
"""
LLM Error Detector

Detects logical errors and inconsistencies in LLM analyses:
- Missing required fields
- Impossible values
- Contradictory recommendations
- Logic violations
"""
from __future__ import annotations

import re
from typing import Any, Dict, List


def detect_errors(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect errors and inconsistencies in an LLM analysis.

    Args:
        analysis: Dict containing analysis fields like:
            - fair_probability
            - edge_bps
            - action/recommendation
            - reasoning
            - confidence

    Returns:
        Dict with:
            - errors: list[str] - error messages
            - severity: 'ok' | 'warn' | 'error'
            - error_count: int
            - checks_passed: int
            - total_checks: int

    Never crashes on malformed input.
    """
    if not isinstance(analysis, dict):
        return {
            'errors': ['Input is not a dict'],
            'severity': 'error',
            'error_count': 1,
            'checks_passed': 0,
            'total_checks': 1
        }

    errors = []
    warnings = []

    # Run all checks
    _check_missing_probability(analysis, errors, warnings)
    _check_impossible_probability(analysis, errors, warnings)
    _check_contradictory_action(analysis, errors, warnings)
    _check_contradictory_reasoning(analysis, errors, warnings)
    _check_confidence_alignment(analysis, errors, warnings)
    _check_edge_calculation(analysis, errors, warnings)

    # Count checks
    total_checks = 6
    error_count = len(errors)
    warning_count = len(warnings)
    checks_passed = total_checks - error_count - warning_count

    # Determine severity
    if error_count > 0:
        severity = 'error'
    elif warning_count > 0:
        severity = 'warn'
    else:
        severity = 'ok'

    # Combine errors and warnings
    all_issues = errors + warnings

    return {
        'errors': all_issues,
        'severity': severity,
        'error_count': error_count,
        'warning_count': warning_count,
        'checks_passed': checks_passed,
        'total_checks': total_checks,
        'has_errors': error_count > 0,
        'has_warnings': warning_count > 0
    }


def _check_missing_probability(analysis: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """Check if probability is missing but reasoning is present"""
    has_reasoning = bool(analysis.get('reasoning', '').strip())
    has_probability = analysis.get('fair_probability') is not None

    if has_reasoning and not has_probability:
        errors.append("Missing probability but reasoning is present")


def _check_impossible_probability(analysis: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """Check for impossible probability values"""
    prob = analysis.get('fair_probability')

    if prob is None:
        return

    try:
        prob_float = float(prob)

        # Check if it's in 0-100 range (convert to 0-1)
        if prob_float > 1.0 and prob_float <= 100.0:
            prob_float = prob_float / 100.0

        if prob_float < 0.0:
            errors.append(f"Impossible probability: {prob} (< 0)")
        elif prob_float > 1.0:
            errors.append(f"Impossible probability: {prob} (> 1.0 or > 100)")

    except (ValueError, TypeError):
        errors.append(f"Invalid probability format: {prob}")


def _check_contradictory_action(analysis: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """Check if action contradicts edge"""
    action = analysis.get('action') or analysis.get('recommendation', '')
    edge_bps = analysis.get('edge_bps')

    if not action or edge_bps is None:
        return

    try:
        edge_float = float(edge_bps)
        action_lower = str(action).lower()

        # Check for contradictions
        if 'buy_yes' in action_lower and edge_float < -100:
            errors.append(
                f"Action '{action}' recommends buy_yes but edge is negative ({edge_float} bps)"
            )
        elif 'buy_no' in action_lower and edge_float > 100:
            errors.append(
                f"Action '{action}' recommends buy_no but edge is positive ({edge_float} bps)"
            )
        elif 'buy' in action_lower and abs(edge_float) < 50:
            warnings.append(
                f"Action '{action}' recommends buying but edge is small ({edge_float} bps)"
            )

    except (ValueError, TypeError):
        pass  # Skip if edge is not numeric


def _check_contradictory_reasoning(analysis: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """Check for contradictions within reasoning text"""
    reasoning = analysis.get('reasoning', '')

    if not isinstance(reasoning, str) or not reasoning:
        return

    reasoning_lower = reasoning.lower()

    # Define contradiction patterns
    contradictions = [
        (r'overvalued.*undervalued|undervalued.*overvalued', 'valuation contradiction'),
        (r'bullish.*bearish.*(?!but|however)|bearish.*bullish.*(?!but|however)', 'sentiment contradiction'),
        (r'high probability.*low probability|low probability.*high probability', 'probability contradiction'),
        (r'likely to happen.*unlikely|unlikely.*likely to happen', 'likelihood contradiction'),
    ]

    for pattern, description in contradictions:
        if re.search(pattern, reasoning_lower):
            warnings.append(f"Contradictory reasoning: {description}")


def _check_confidence_alignment(analysis: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """Check if confidence aligns with reasoning quality"""
    confidence = analysis.get('confidence', '').lower()
    reasoning = analysis.get('reasoning', '')

    if not reasoning or not confidence:
        return

    reasoning_length = len(reasoning.split())

    # Check if high confidence but very short reasoning
    if confidence == 'high' and reasoning_length < 10:
        warnings.append(
            f"High confidence claimed but reasoning is too brief ({reasoning_length} words)"
        )

    # Check if low confidence but very detailed reasoning
    if confidence == 'low' and reasoning_length > 100:
        warnings.append(
            f"Low confidence claimed but reasoning is very detailed ({reasoning_length} words)"
        )


def _check_edge_calculation(analysis: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """Check if edge calculation is consistent with probabilities"""
    fair_prob = analysis.get('fair_probability')
    market_price = analysis.get('market_price') or analysis.get('yes_price')
    edge_bps = analysis.get('edge_bps')

    # Need all three to check
    if fair_prob is None or market_price is None or edge_bps is None:
        return

    try:
        fair_float = float(fair_prob)
        market_float = float(market_price)
        edge_float = float(edge_bps)

        # Normalize probabilities to 0-1
        if fair_float > 1.0:
            fair_float = fair_float / 100.0
        if market_float > 1.0:
            market_float = market_float / 100.0

        # Calculate expected edge
        expected_edge_bps = (fair_float - market_float) * 10000

        # Check if reported edge matches calculation (within tolerance)
        if abs(expected_edge_bps - edge_float) > 100:  # 1 percentage point tolerance
            warnings.append(
                f"Edge calculation mismatch: reported {edge_float} bps, "
                f"expected ~{expected_edge_bps:.0f} bps based on probabilities"
            )

    except (ValueError, TypeError):
        pass  # Skip if values are not numeric
