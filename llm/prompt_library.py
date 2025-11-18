#!/usr/bin/env python3
"""
Prompt Library

Version-controlled prompt templates for different market categories.
Each prompt is designed to produce structured JSON output with:
- fair_probability: estimated probability (0-100%)
- confidence: low/medium/high
- edge_bps: edge in basis points
- reasoning: short explanation
- action: buy_yes/buy_no/avoid

Design principles:
- Short, focused prompts (minimize tokens)
- Explicit JSON schema in prompt
- Category-specific domain knowledge
- Minimize hallucination risk
- Request calibrated probabilities
"""

from __future__ import annotations

from typing import Dict, Any


# Prompt version for tracking
PROMPT_VERSION = "v1.0.0"


def get_base_prompt() -> str:
    """
    Base instructions common to all prompts.
    Sets up JSON output format and calibration guidance.
    """
    return """You are a probability estimator for prediction markets. Analyze the market and provide a JSON response.

Output format (valid JSON only, no markdown):
{
  "fair_probability": <float 0-100>,
  "confidence": "<low|medium|high>",
  "edge_bps": <int>,
  "reasoning": "<concise explanation>",
  "action": "<buy_yes|buy_no|avoid>"
}

Guidelines:
- fair_probability: Your best estimate of YES outcome (0-100%)
- confidence: low (uncertain), medium (reasonable), high (very confident)
- edge_bps: (fair_probability - market_price) * 100 in basis points
- reasoning: 1-2 sentences explaining your estimate
- action: buy_yes if edge>500bps, buy_no if edge<-500bps, else avoid

Be well-calibrated. Avoid overconfidence. Consider base rates."""


def get_politics_prompt(market_data: Dict[str, Any]) -> str:
    """Politics-specific prompt"""
    base = get_base_prompt()

    question = market_data.get("question", "Unknown question")
    current_price = market_data.get("yes_price", 0.5) * 100
    volume = market_data.get("volume", 0)
    closes_at = market_data.get("closes_at", "Unknown")

    return f"""{base}

Category: POLITICS

Market: {question}
Current YES price: {current_price:.1f}%
Volume: ${volume:,.0f}
Closes: {closes_at}

Political markets considerations:
- Polling data and trends
- Institutional factors (electoral college, parliament rules, etc.)
- Historical precedents
- Current events and momentum
- Time until resolution

Analyze this political market and provide your JSON estimate."""


def get_crypto_prompt(market_data: Dict[str, Any]) -> str:
    """Crypto-specific prompt"""
    base = get_base_prompt()

    question = market_data.get("question", "Unknown question")
    current_price = market_data.get("yes_price", 0.5) * 100
    volume = market_data.get("volume", 0)
    closes_at = market_data.get("closes_at", "Unknown")

    return f"""{base}

Category: CRYPTO

Market: {question}
Current YES price: {current_price:.1f}%
Volume: ${volume:,.0f}
Closes: {closes_at}

Crypto markets considerations:
- Price volatility and historical ranges
- Market cycles and sentiment
- Technical levels (support/resistance)
- Regulatory developments
- Network fundamentals (if applicable)
- Macro crypto market conditions

Analyze this crypto market and provide your JSON estimate."""


def get_sports_prompt(market_data: Dict[str, Any]) -> str:
    """Sports-specific prompt"""
    base = get_base_prompt()

    question = market_data.get("question", "Unknown question")
    current_price = market_data.get("yes_price", 0.5) * 100
    volume = market_data.get("volume", 0)
    closes_at = market_data.get("closes_at", "Unknown")

    return f"""{base}

Category: SPORTS

Market: {question}
Current YES price: {current_price:.1f}%
Volume: ${volume:,.0f}
Closes: {closes_at}

Sports markets considerations:
- Team/player historical performance
- Recent form and trends
- Injuries and roster changes
- Head-to-head records
- Home/away advantage
- Betting market consensus (if available)

Analyze this sports market and provide your JSON estimate."""


def get_macro_prompt(market_data: Dict[str, Any]) -> str:
    """Macro/economics-specific prompt"""
    base = get_base_prompt()

    question = market_data.get("question", "Unknown question")
    current_price = market_data.get("yes_price", 0.5) * 100
    volume = market_data.get("volume", 0)
    closes_at = market_data.get("closes_at", "Unknown")

    return f"""{base}

Category: MACRO/ECONOMICS

Market: {question}
Current YES price: {current_price:.1f}%
Volume: ${volume:,.0f}
Closes: {closes_at}

Macro markets considerations:
- Economic data trends
- Central bank policy and guidance
- Historical precedents for similar indicators
- Consensus economist forecasts
- Current economic cycle phase
- Global macro conditions

Analyze this macro market and provide your JSON estimate."""


def get_generic_prompt(market_data: Dict[str, Any]) -> str:
    """Generic fallback prompt for uncategorized markets"""
    base = get_base_prompt()

    question = market_data.get("question", "Unknown question")
    current_price = market_data.get("yes_price", 0.5) * 100
    volume = market_data.get("volume", 0)
    closes_at = market_data.get("closes_at", "Unknown")
    category = market_data.get("category", "other")

    return f"""{base}

Category: {category.upper()}

Market: {question}
Current YES price: {current_price:.1f}%
Volume: ${volume:,.0f}
Closes: {closes_at}

General considerations:
- Base rates for similar events
- Available information and news
- Market efficiency (high volume = more efficient)
- Time until resolution
- Clarity of resolution criteria

Analyze this market and provide your JSON estimate."""


# Prompt router - maps category to prompt function
PROMPT_ROUTER = {
    "politics": get_politics_prompt,
    "crypto": get_crypto_prompt,
    "sports": get_sports_prompt,
    "macro": get_macro_prompt,
    "other": get_generic_prompt,
}


def get_prompt_for_market(market_data: Dict[str, Any]) -> str:
    """
    Get the appropriate prompt for a market based on its category.

    Args:
        market_data: Market dict with at least 'category' field

    Returns:
        Formatted prompt string ready to send to LLM
    """
    category = market_data.get("category", "other")
    prompt_fn = PROMPT_ROUTER.get(category, get_generic_prompt)
    return prompt_fn(market_data)


def get_prompt_metadata() -> Dict[str, Any]:
    """
    Get metadata about the prompt library.

    Returns:
        Dict with version, available categories, etc.
    """
    return {
        "version": PROMPT_VERSION,
        "categories": list(PROMPT_ROUTER.keys()),
        "base_prompt_tokens_estimate": 150,  # Approximate
        "category_prompt_tokens_estimate": 250,  # Approximate per category
    }
