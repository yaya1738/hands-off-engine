#!/usr/bin/env python3
"""
LLM Consensus Engine

Builds consensus from multiple LLM analyses by:
- Weighted averaging of probabilities based on confidence
- Merging reasoning from multiple models
- Detecting disagreements and adjusting confidence accordingly
"""
from __future__ import annotations

from typing import Any, Dict, List


# Confidence weights for probability averaging
CONFIDENCE_WEIGHTS = {
    'high': 3.0,
    'medium': 2.0,
    'low': 1.0,
    'unknown': 0.5
}

# Disagreement threshold (percentage points)
SHARP_DISAGREEMENT_THRESHOLD = 25.0

# Confidence level order for downgrading
CONFIDENCE_LEVELS = ['high', 'medium', 'low']


def build_consensus(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build consensus from multiple LLM analyses.

    Args:
        analyses: List of analysis dicts, each containing:
            - fair_probability: float (0-100 or 0-1)
            - confidence: str ('low', 'medium', 'high')
            - reasoning: str

    Returns:
        Dict with:
            - consensus_probability: float (0-1)
            - confidence: str
            - reasoning: str (merged)
            - num_analyses: int
            - probability_range: dict (min, max, spread)

    Never crashes on malformed input - returns safe defaults.
    """
    if not analyses or not isinstance(analyses, list):
        return _empty_consensus("No analyses provided")

    # Filter to valid analyses
    valid_analyses = []
    for analysis in analyses:
        if not isinstance(analysis, dict):
            continue

        prob = analysis.get('fair_probability')
        if prob is None:
            continue

        try:
            prob_float = float(prob)
            # Normalize to 0-1 range if in 0-100
            if prob_float > 1.0:
                prob_float = prob_float / 100.0

            # Validate range
            if 0.0 <= prob_float <= 1.0:
                valid_analyses.append({
                    'probability': prob_float,
                    'confidence': analysis.get('confidence', 'unknown'),
                    'reasoning': analysis.get('reasoning', '')
                })
        except (ValueError, TypeError):
            continue

    if not valid_analyses:
        return _empty_consensus("No valid analyses found")

    # Calculate weighted average probability
    consensus_prob = _calculate_weighted_average(valid_analyses)

    # Determine base confidence level
    base_confidence = _determine_base_confidence(valid_analyses)

    # Check for sharp disagreements
    prob_values = [a['probability'] for a in valid_analyses]
    prob_range = {
        'min': min(prob_values),
        'max': max(prob_values),
        'spread': max(prob_values) - min(prob_values)
    }

    # Downgrade confidence if sharp disagreement
    final_confidence = base_confidence
    if prob_range['spread'] > (SHARP_DISAGREEMENT_THRESHOLD / 100.0):
        final_confidence = _downgrade_confidence(base_confidence)

    # Merge reasoning
    merged_reasoning = _merge_reasoning(valid_analyses)

    return {
        'consensus_probability': consensus_prob,
        'confidence': final_confidence,
        'reasoning': merged_reasoning,
        'num_analyses': len(valid_analyses),
        'probability_range': prob_range,
        'disagreement_detected': prob_range['spread'] > (SHARP_DISAGREEMENT_THRESHOLD / 100.0)
    }


def _empty_consensus(reason: str) -> Dict[str, Any]:
    """Return safe default consensus when no valid input"""
    return {
        'consensus_probability': 0.5,
        'confidence': 'low',
        'reasoning': f'No consensus available: {reason}',
        'num_analyses': 0,
        'probability_range': {'min': 0.5, 'max': 0.5, 'spread': 0.0},
        'disagreement_detected': False
    }


def _calculate_weighted_average(analyses: List[Dict[str, Any]]) -> float:
    """Calculate weighted average of probabilities based on confidence"""
    total_weight = 0.0
    weighted_sum = 0.0

    for analysis in analyses:
        confidence = analysis['confidence'].lower()
        weight = CONFIDENCE_WEIGHTS.get(confidence, CONFIDENCE_WEIGHTS['unknown'])

        total_weight += weight
        weighted_sum += analysis['probability'] * weight

    if total_weight == 0:
        return 0.5  # Default if no valid weights

    return weighted_sum / total_weight


def _determine_base_confidence(analyses: List[Dict[str, Any]]) -> str:
    """Determine base confidence level from analyses"""
    if not analyses:
        return 'low'

    # Count confidence levels
    confidence_counts = {'high': 0, 'medium': 0, 'low': 0, 'unknown': 0}

    for analysis in analyses:
        confidence = analysis['confidence'].lower()
        if confidence in confidence_counts:
            confidence_counts[confidence] += 1
        else:
            confidence_counts['unknown'] += 1

    total = len(analyses)

    # If majority are high confidence, return high
    if confidence_counts['high'] / total >= 0.6:
        return 'high'

    # If majority are medium or high, return medium
    if (confidence_counts['high'] + confidence_counts['medium']) / total >= 0.6:
        return 'medium'

    # Otherwise low
    return 'low'


def _downgrade_confidence(confidence: str) -> str:
    """Downgrade confidence by one level due to disagreement"""
    confidence_lower = confidence.lower()

    if confidence_lower not in CONFIDENCE_LEVELS:
        return 'low'

    current_idx = CONFIDENCE_LEVELS.index(confidence_lower)

    # Move down one level (or stay at low)
    if current_idx < len(CONFIDENCE_LEVELS) - 1:
        return CONFIDENCE_LEVELS[current_idx + 1]

    return confidence_lower


def _merge_reasoning(analyses: List[Dict[str, Any]]) -> str:
    """Merge reasoning from multiple analyses"""
    if not analyses:
        return "No reasoning available"

    # Take top reasoning lines from each analysis
    reasoning_parts = []

    for i, analysis in enumerate(analyses[:3], 1):  # Limit to top 3
        reasoning = analysis.get('reasoning', '').strip()
        if reasoning:
            # Truncate long reasoning
            if len(reasoning) > 200:
                reasoning = reasoning[:197] + "..."

            confidence = analysis['confidence']
            prob = analysis['probability']

            reasoning_parts.append(
                f"Analysis {i} ({confidence}, p={prob:.2f}): {reasoning}"
            )

    if not reasoning_parts:
        return "No detailed reasoning provided"

    # Add summary if multiple analyses
    if len(analyses) > 1:
        prob_values = [a['probability'] for a in analyses]
        avg_prob = sum(prob_values) / len(prob_values)
        spread = max(prob_values) - min(prob_values)

        summary = (
            f"Consensus from {len(analyses)} analyses: "
            f"avg={avg_prob:.2f}, spread={spread:.2f}."
        )
        reasoning_parts.insert(0, summary)

    return " | ".join(reasoning_parts)
