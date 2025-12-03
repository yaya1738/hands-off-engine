#!/usr/bin/env python3
"""
LLM Reasoning Quality Booster

Scores reasoning quality across multiple dimensions:
- Depth: How thorough is the analysis?
- Coverage: Does it cover key factors?
- Consistency: Are statements internally consistent?
- Evidence: Are claims backed by evidence/logic?

Flags low-quality reasoning for improvement.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


# Scoring thresholds
DEPTH_MAX = 30
COVERAGE_MAX = 30
CONSISTENCY_MAX = 20
EVIDENCE_MAX = 20
TOTAL_MAX = 100

LOW_QUALITY_THRESHOLD = 50

# Keywords that indicate analytical depth
DEPTH_INDICATORS = [
    'because', 'therefore', 'however', 'although', 'considering',
    'given that', 'due to', 'as a result', 'consequently', 'implies',
    'suggests', 'indicates', 'demonstrates', 'evidence', 'analysis'
]

# Key factors to cover
COVERAGE_FACTORS = [
    'price', 'market', 'probability', 'odds', 'value',
    'risk', 'event', 'outcome', 'likelihood', 'chance',
    'time', 'deadline', 'catalyst', 'factor', 'trend'
]

# Consistency red flags
INCONSISTENCY_PATTERNS = [
    (r'likely.*unlikely', 'contradictory likelihood claims'),
    (r'high.*low probability', 'contradictory probability claims'),
    (r'bullish.*bearish', 'contradictory sentiment'),
    (r'buy.*avoid|avoid.*buy', 'contradictory action'),
]

# Evidence indicators
EVIDENCE_INDICATORS = [
    'data shows', 'historically', 'according to', 'studies show',
    'research indicates', 'statistics', 'evidence suggests',
    'past performance', 'track record', 'analysis indicates',
    'recent', 'current', 'latest'
]


def score_reasoning(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score reasoning quality on 0-100 scale.

    Args:
        analysis: Dict containing 'reasoning' field (and optionally other fields)

    Returns:
        Dict with:
            - total_score: int (0-100)
            - depth_score: int (0-30)
            - coverage_score: int (0-30)
            - consistency_score: int (0-20)
            - evidence_score: int (0-20)
            - breakdown: dict with details

    Never crashes on malformed input.
    """
    if not isinstance(analysis, dict):
        return _empty_score("Input is not a dict")

    reasoning = analysis.get('reasoning', '')

    if not reasoning or not isinstance(reasoning, str):
        return _empty_score("No valid reasoning text")

    reasoning_lower = reasoning.lower()

    # Score each dimension
    depth_score = _score_depth(reasoning, reasoning_lower)
    coverage_score = _score_coverage(reasoning, reasoning_lower)
    consistency_score = _score_consistency(reasoning, reasoning_lower)
    evidence_score = _score_evidence(reasoning, reasoning_lower)

    total_score = depth_score + coverage_score + consistency_score + evidence_score

    return {
        'total_score': total_score,
        'depth_score': depth_score,
        'coverage_score': coverage_score,
        'consistency_score': consistency_score,
        'evidence_score': evidence_score,
        'breakdown': {
            'depth': f"{depth_score}/{DEPTH_MAX}",
            'coverage': f"{coverage_score}/{COVERAGE_MAX}",
            'consistency': f"{consistency_score}/{CONSISTENCY_MAX}",
            'evidence': f"{evidence_score}/{EVIDENCE_MAX}"
        },
        'quality_level': _quality_level(total_score)
    }


def boost_if_needed(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if reasoning needs boosting and flag accordingly.

    Args:
        analysis: Analysis dict with reasoning

    Returns:
        Dict with:
            - needs_boost: bool
            - score: int
            - reason: str
            - suggestions: list[str]
    """
    if not isinstance(analysis, dict):
        return {
            'needs_boost': True,
            'score': 0,
            'reason': 'Invalid analysis format',
            'suggestions': ['Provide valid analysis dict']
        }

    score_result = score_reasoning(analysis)
    total_score = score_result['total_score']

    needs_boost = total_score < LOW_QUALITY_THRESHOLD

    suggestions = []
    if score_result['depth_score'] < DEPTH_MAX * 0.5:
        suggestions.append("Add more analytical depth and causal reasoning")

    if score_result['coverage_score'] < COVERAGE_MAX * 0.5:
        suggestions.append("Cover more key factors (price, risk, timing, etc.)")

    if score_result['consistency_score'] < CONSISTENCY_MAX * 0.5:
        suggestions.append("Fix contradictory statements")

    if score_result['evidence_score'] < EVIDENCE_MAX * 0.5:
        suggestions.append("Add more evidence and specific examples")

    return {
        'needs_boost': needs_boost,
        'score': total_score,
        'reason': 'Low reasoning quality' if needs_boost else 'Reasoning quality acceptable',
        'suggestions': suggestions,
        'score_breakdown': score_result
    }


def _empty_score(reason: str) -> Dict[str, Any]:
    """Return zero score for invalid input"""
    return {
        'total_score': 0,
        'depth_score': 0,
        'coverage_score': 0,
        'consistency_score': 0,
        'evidence_score': 0,
        'breakdown': {
            'depth': f"0/{DEPTH_MAX}",
            'coverage': f"0/{COVERAGE_MAX}",
            'consistency': f"0/{CONSISTENCY_MAX}",
            'evidence': f"0/{EVIDENCE_MAX}"
        },
        'quality_level': 'very_low',
        'error': reason
    }


def _score_depth(reasoning: str, reasoning_lower: str) -> int:
    """
    Score analytical depth (0-30).

    Checks for:
    - Presence of depth indicators
    - Length of reasoning
    - Sentence complexity
    """
    score = 0

    # Length bonus (up to 10 points)
    word_count = len(reasoning.split())
    if word_count >= 50:
        score += 10
    elif word_count >= 30:
        score += 7
    elif word_count >= 15:
        score += 4

    # Depth indicators (up to 15 points)
    depth_count = sum(1 for indicator in DEPTH_INDICATORS if indicator in reasoning_lower)
    score += min(15, depth_count * 3)

    # Sentence count (up to 5 points)
    sentences = reasoning.count('.') + reasoning.count('!') + reasoning.count('?')
    if sentences >= 3:
        score += 5
    elif sentences >= 2:
        score += 3

    return min(DEPTH_MAX, score)


def _score_coverage(reasoning: str, reasoning_lower: str) -> int:
    """
    Score coverage of key factors (0-30).

    Checks for mentions of important market factors.
    """
    score = 0

    # Count unique coverage factors mentioned
    factors_mentioned = sum(1 for factor in COVERAGE_FACTORS if factor in reasoning_lower)

    # Award points based on coverage
    score = min(COVERAGE_MAX, factors_mentioned * 5)

    return score


def _score_consistency(reasoning: str, reasoning_lower: str) -> int:
    """
    Score internal consistency (0-20).

    Checks for contradictions and logical conflicts.
    """
    score = CONSISTENCY_MAX  # Start at max, deduct for issues

    # Check for contradiction patterns
    for pattern, description in INCONSISTENCY_PATTERNS:
        if re.search(pattern, reasoning_lower):
            score -= 5

    # Ensure non-negative
    return max(0, score)


def _score_evidence(reasoning: str, reasoning_lower: str) -> int:
    """
    Score evidence quality (0-20).

    Checks for evidence-based claims and specific references.
    """
    score = 0

    # Evidence indicators (up to 15 points)
    evidence_count = sum(1 for indicator in EVIDENCE_INDICATORS if indicator in reasoning_lower)
    score += min(15, evidence_count * 4)

    # Specific numbers or data (up to 5 points)
    has_numbers = bool(re.search(r'\d+%|\d+\.\d+|\$\d+', reasoning))
    if has_numbers:
        score += 5

    return min(EVIDENCE_MAX, score)


def _quality_level(score: int) -> str:
    """Categorize quality level based on score"""
    if score >= 80:
        return 'excellent'
    elif score >= 65:
        return 'good'
    elif score >= 50:
        return 'acceptable'
    elif score >= 30:
        return 'low'
    else:
        return 'very_low'
