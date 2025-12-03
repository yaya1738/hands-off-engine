#!/usr/bin/env python3
"""
Yair Insights Pipeline: Golden Sprinkles for Maximum Edge
==========================================================

This module handles human expert insights - the "golden sprinkles"
that add alpha on top of algorithmic signals.

Yair (and other domain experts) can provide:
- Qualitative insights about specific markets
- News/event interpretation
- Sentiment calibration
- Edge multipliers on existing signals
- Veto power on risky trades

Input Methods:
1. Telegram messages (via bot)
2. JSON file drops
3. CLI interface
4. Voice notes (transcribed)
5. Direct API calls

The key is making it EASY for Yair to input insights quickly,
then we normalize and pipe them into the trading system.

Philosophy: "Yair's insights as needed for further golden sprinkles"
"""

import json
import sys
import os
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Any
import time

# Add parent directory for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from alpha.integrations_hub import (
    AlphaSourceAdapter,
    SignalSource,
    SignalUrgency,
    UnifiedAlphaSignal,
    create_signal
)


class InsightType(Enum):
    """Types of human insights"""
    ALPHA_SIGNAL = "alpha_signal"       # Direct trade recommendation
    EDGE_MODIFIER = "edge_modifier"      # Modify existing signal's edge
    VETO = "veto"                         # Block a specific trade
    GENERAL_CONTEXT = "general_context"  # Background info
    NEWS_INTERPRETATION = "news_interpretation"
    CONFIDENCE_OVERRIDE = "confidence_override"


class InsightPriority(Enum):
    """Priority levels for insights"""
    CRITICAL = "critical"   # Act immediately
    HIGH = "high"           # Process soon
    NORMAL = "normal"       # Regular priority
    LOW = "low"             # Background context


@dataclass
class YairInsight:
    """
    A single insight from Yair or other expert.

    Flexible format to accept various input styles:
    - Quick text message: "BTC market looks mispriced, buy YES"
    - Detailed analysis: Full JSON with reasoning
    - Edge modifier: "Increase confidence on trump market by 20%"
    - Veto: "Don't touch the crypto markets today"
    """
    # Core fields
    insight_id: str
    insight_type: InsightType
    timestamp: str
    source_name: str  # "yair", "expert_2", etc.

    # For ALPHA_SIGNAL type
    market_id: Optional[str] = None
    side: Optional[str] = None
    fair_price: Optional[float] = None
    confidence: Optional[float] = None

    # For EDGE_MODIFIER type
    target_market_id: Optional[str] = None
    edge_multiplier: Optional[float] = None  # 1.2 = increase edge by 20%
    confidence_adjustment: Optional[float] = None  # +0.1 = add 10% confidence

    # For VETO type
    veto_market_pattern: Optional[str] = None  # Regex or keyword
    veto_reason: Optional[str] = None
    veto_until: Optional[str] = None  # ISO timestamp

    # For all types
    reasoning: str = ""
    priority: InsightPriority = InsightPriority.NORMAL
    raw_input: Optional[str] = None

    # Metadata
    processed: bool = False
    applied_to_signals: List[str] = field(default_factory=list)


class InsightParser:
    """
    Parse natural language insights into structured YairInsight objects.

    Handles quick telegram messages, detailed JSON, and everything in between.
    """

    def __init__(self):
        # Keywords for insight type detection
        self.alpha_keywords = ['buy', 'sell', 'long', 'short', 'mispriced', 'edge on']
        self.veto_keywords = ['don\'t', 'avoid', 'stay away', 'veto', 'skip', 'pass on']
        self.modifier_keywords = ['increase', 'decrease', 'adjust', 'boost', 'reduce']

    def parse(self, raw_input: str, source_name: str = "yair") -> YairInsight:
        """
        Parse raw text input into a YairInsight.

        Examples:
        - "buy YES on trump market, looks good"
        - "don't touch crypto today"
        - "increase confidence on btc-100k by 20%"
        """
        raw_lower = raw_input.lower()
        timestamp = datetime.now(timezone.utc).isoformat()
        insight_id = hashlib.md5(f"{raw_input}_{timestamp}".encode()).hexdigest()[:12]

        # Detect insight type
        insight_type = self._detect_type(raw_lower)

        insight = YairInsight(
            insight_id=insight_id,
            insight_type=insight_type,
            timestamp=timestamp,
            source_name=source_name,
            raw_input=raw_input,
            reasoning=raw_input
        )

        # Parse based on type
        if insight_type == InsightType.ALPHA_SIGNAL:
            self._parse_alpha_signal(insight, raw_lower, raw_input)
        elif insight_type == InsightType.VETO:
            self._parse_veto(insight, raw_lower, raw_input)
        elif insight_type == InsightType.EDGE_MODIFIER:
            self._parse_modifier(insight, raw_lower, raw_input)
        else:
            # General context - just store the raw input
            pass

        return insight

    def _detect_type(self, text: str) -> InsightType:
        """Detect the type of insight from text"""
        if any(kw in text for kw in self.veto_keywords):
            return InsightType.VETO
        elif any(kw in text for kw in self.modifier_keywords):
            return InsightType.EDGE_MODIFIER
        elif any(kw in text for kw in self.alpha_keywords):
            return InsightType.ALPHA_SIGNAL
        else:
            return InsightType.GENERAL_CONTEXT

    def _parse_alpha_signal(self, insight: YairInsight, text_lower: str, raw_text: str):
        """Parse an alpha signal insight"""
        # Detect side
        if 'yes' in text_lower or 'buy' in text_lower or 'long' in text_lower:
            insight.side = 'YES'
        elif 'no' in text_lower or 'sell' in text_lower or 'short' in text_lower:
            insight.side = 'NO'

        # Extract market ID (look for common patterns)
        import re

        # Look for "on X market" or "X market" patterns
        market_patterns = [
            r'on\s+([a-z0-9_-]+)\s*market',
            r'([a-z0-9_-]+)\s*market',
            r'market[:\s]+([a-z0-9_-]+)',
            r'slug[:\s]+([a-z0-9_-]+)',
        ]

        for pattern in market_patterns:
            match = re.search(pattern, text_lower)
            if match:
                insight.market_id = match.group(1)
                break

        # Extract confidence keywords
        if 'very confident' in text_lower or 'high confidence' in text_lower or 'sure' in text_lower:
            insight.confidence = 0.85
        elif 'confident' in text_lower or 'looks good' in text_lower:
            insight.confidence = 0.75
        elif 'think' in text_lower or 'maybe' in text_lower:
            insight.confidence = 0.60

        # Extract numbers for fair price
        numbers = re.findall(r'(\d+\.?\d*)%?', raw_text)
        if numbers:
            for num_str in numbers:
                num = float(num_str)
                if 0 < num < 1:
                    insight.fair_price = num
                elif 1 < num <= 100:
                    insight.fair_price = num / 100

        # Set priority based on urgency words
        if 'now' in text_lower or 'quick' in text_lower or 'asap' in text_lower:
            insight.priority = InsightPriority.CRITICAL
        elif 'soon' in text_lower or 'today' in text_lower:
            insight.priority = InsightPriority.HIGH

    def _parse_veto(self, insight: YairInsight, text_lower: str, raw_text: str):
        """Parse a veto insight"""
        # Extract what to veto
        import re

        # Look for market patterns to veto
        patterns = [
            r'avoid\s+([a-z0-9_-]+)',
            r'don\'t\s+(?:touch|trade)\s+([a-z0-9_-]+)',
            r'skip\s+([a-z0-9_-]+)',
            r'pass on\s+([a-z0-9_-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                insight.veto_market_pattern = match.group(1)
                break

        # Check for category vetoes
        if 'crypto' in text_lower:
            insight.veto_market_pattern = 'crypto|bitcoin|btc|eth|ethereum'
        elif 'sports' in text_lower:
            insight.veto_market_pattern = 'nba|nfl|mlb|game|win|beat'
        elif 'politics' in text_lower:
            insight.veto_market_pattern = 'trump|biden|election|vote'

        insight.veto_reason = raw_text
        insight.priority = InsightPriority.HIGH

    def _parse_modifier(self, insight: YairInsight, text_lower: str, raw_text: str):
        """Parse an edge modifier insight"""
        import re

        # Extract percentage changes
        percent_match = re.search(r'(\d+)%', raw_text)
        if percent_match:
            pct = float(percent_match.group(1)) / 100

            if 'increase' in text_lower or 'boost' in text_lower:
                insight.edge_multiplier = 1 + pct
                insight.confidence_adjustment = pct
            elif 'decrease' in text_lower or 'reduce' in text_lower:
                insight.edge_multiplier = 1 - pct
                insight.confidence_adjustment = -pct

        # Extract target market
        market_patterns = [
            r'on\s+([a-z0-9_-]+)',
            r'for\s+([a-z0-9_-]+)',
        ]

        for pattern in market_patterns:
            match = re.search(pattern, text_lower)
            if match:
                insight.target_market_id = match.group(1)
                break


class YairInsightsAdapter(AlphaSourceAdapter):
    """
    Adapter that processes Yair's insights for the Integrations Hub.

    Handles:
    1. Converting direct alpha signals to unified format
    2. Storing edge modifiers for application to other signals
    3. Maintaining veto list
    """

    def __init__(
        self,
        insights_dir: Path = None,
        archive_dir: Path = None
    ):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.insights_dir = insights_dir or self.state_dir / 'yair-insights'
        self.archive_dir = archive_dir or self.state_dir / 'yair-insights-archive'

        # Create directories
        self.insights_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        self.parser = InsightParser()

        # In-memory storage
        self._pending_insights: List[YairInsight] = []
        self._active_vetoes: List[YairInsight] = []
        self._active_modifiers: List[YairInsight] = []

        # File paths
        self.vetoes_path = self.state_dir / 'active-vetoes.json'
        self.modifiers_path = self.state_dir / 'active-modifiers.json'

        # Load persisted vetoes and modifiers
        self._load_persisted_state()

    @property
    def source_type(self) -> SignalSource:
        return SignalSource.YAIR_INSIGHTS

    def is_available(self) -> bool:
        return True

    def fetch_signals(self) -> List[UnifiedAlphaSignal]:
        """
        Process pending insights and return alpha signals.

        Also updates the veto and modifier lists.
        """
        signals = []

        # Process file inbox
        self._process_insight_files()

        # Process pending insights
        for insight in self._pending_insights:
            if insight.insight_type == InsightType.ALPHA_SIGNAL:
                unified = self._convert_to_signal(insight)
                if unified:
                    signals.append(unified)
                    insight.processed = True

            elif insight.insight_type == InsightType.VETO:
                self._active_vetoes.append(insight)
                insight.processed = True
                print(f"[Yair] Added veto: {insight.veto_market_pattern}")

            elif insight.insight_type == InsightType.EDGE_MODIFIER:
                self._active_modifiers.append(insight)
                insight.processed = True
                print(f"[Yair] Added modifier: {insight.edge_multiplier}x on {insight.target_market_id}")

        # Clear processed insights
        self._pending_insights = [i for i in self._pending_insights if not i.processed]

        # Persist state
        self._save_persisted_state()

        return signals

    def submit_insight(self, text: str, source_name: str = "yair") -> str:
        """
        Submit an insight via text input.

        Returns:
            Insight ID for tracking
        """
        insight = self.parser.parse(text, source_name)
        self._pending_insights.append(insight)

        print(f"[Yair] Received {insight.insight_type.value}: {text[:50]}...")
        return insight.insight_id

    def submit_structured(self, insight: YairInsight) -> str:
        """Submit a pre-structured insight"""
        self._pending_insights.append(insight)
        return insight.insight_id

    def should_veto(self, market_id: str) -> Optional[str]:
        """
        Check if a market should be vetoed.

        Returns:
            Veto reason if vetoed, None otherwise
        """
        import re

        for veto in self._active_vetoes:
            if veto.veto_market_pattern:
                if re.search(veto.veto_market_pattern, market_id, re.IGNORECASE):
                    return veto.veto_reason

        return None

    def get_modifier(self, market_id: str) -> Optional[YairInsight]:
        """Get edge modifier for a market if one exists"""
        for mod in self._active_modifiers:
            if mod.target_market_id and mod.target_market_id in market_id:
                return mod
        return None

    def apply_modifiers(self, signal: UnifiedAlphaSignal) -> UnifiedAlphaSignal:
        """
        Apply any active modifiers to a signal.

        Returns modified signal (or original if no modifiers apply).
        """
        modifier = self.get_modifier(signal.market_id)
        if not modifier:
            return signal

        # Apply edge multiplier
        if modifier.edge_multiplier:
            signal.edge = signal.edge * modifier.edge_multiplier

        # Apply confidence adjustment
        if modifier.confidence_adjustment:
            signal.confidence = min(0.99, max(0.01,
                signal.confidence + modifier.confidence_adjustment
            ))

        # Update reasoning
        signal.reasoning += f" [Yair modifier applied: {modifier.edge_multiplier}x edge]"

        return signal

    def clear_veto(self, pattern: str):
        """Remove a veto by pattern"""
        self._active_vetoes = [
            v for v in self._active_vetoes
            if v.veto_market_pattern != pattern
        ]
        self._save_persisted_state()

    def clear_modifier(self, market_id: str):
        """Remove a modifier by market ID"""
        self._active_modifiers = [
            m for m in self._active_modifiers
            if m.target_market_id != market_id
        ]
        self._save_persisted_state()

    def clear_all(self):
        """Clear all pending insights, vetoes, and modifiers"""
        self._pending_insights = []
        self._active_vetoes = []
        self._active_modifiers = []
        self._save_persisted_state()

    def _process_insight_files(self):
        """Process JSON files in the insights directory"""
        for file_path in self.insights_dir.glob('*.json'):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Handle various formats
                if isinstance(data, str):
                    # Plain text insight
                    self.submit_insight(data)
                elif isinstance(data, list):
                    # Array of insights
                    for item in data:
                        if isinstance(item, str):
                            self.submit_insight(item)
                        else:
                            self._process_json_insight(item)
                else:
                    # Single JSON insight
                    self._process_json_insight(data)

                # Archive
                archive_path = self.archive_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_path.name}"
                file_path.rename(archive_path)

            except Exception as e:
                print(f"[Yair] Error processing {file_path}: {e}")

    def _process_json_insight(self, data: Dict):
        """Process a structured JSON insight"""
        # Check if it's natural language or structured
        if 'text' in data or 'message' in data:
            text = data.get('text') or data.get('message')
            self.submit_insight(text, data.get('source', 'yair'))
        else:
            # Try to build structured insight
            insight_type = InsightType(data.get('type', 'alpha_signal'))
            insight = YairInsight(
                insight_id=data.get('id', hashlib.md5(json.dumps(data).encode()).hexdigest()[:12]),
                insight_type=insight_type,
                timestamp=data.get('timestamp', datetime.now(timezone.utc).isoformat()),
                source_name=data.get('source', 'yair'),
                market_id=data.get('market_id'),
                side=data.get('side'),
                fair_price=data.get('fair_price'),
                confidence=data.get('confidence'),
                reasoning=data.get('reasoning', ''),
                priority=InsightPriority(data.get('priority', 'normal'))
            )
            self._pending_insights.append(insight)

    def _convert_to_signal(self, insight: YairInsight) -> Optional[UnifiedAlphaSignal]:
        """Convert an alpha signal insight to UnifiedAlphaSignal"""
        if not insight.market_id or not insight.side:
            print(f"[Yair] Insight missing market_id or side: {insight.raw_input}")
            return None

        fair_price = insight.fair_price or 0.65
        market_price = 0.5  # Default - would be fetched from market data

        edge = abs(fair_price - market_price)
        confidence = insight.confidence or 0.70

        # Map priority to urgency
        urgency_map = {
            InsightPriority.CRITICAL: SignalUrgency.IMMEDIATE,
            InsightPriority.HIGH: SignalUrgency.HIGH,
            InsightPriority.NORMAL: SignalUrgency.NORMAL,
            InsightPriority.LOW: SignalUrgency.LOW
        }

        return create_signal(
            market_id=insight.market_id,
            market_name=f"Yair Signal: {insight.market_id}",
            source=SignalSource.YAIR_INSIGHTS,
            side=insight.side,
            fair_price=fair_price,
            market_price=market_price,
            confidence=confidence,
            urgency=urgency_map.get(insight.priority, SignalUrgency.HIGH),
            category="human_insight",
            reasoning=f"Golden sprinkle from {insight.source_name}: {insight.reasoning}",
            raw_data={
                'insight_id': insight.insight_id,
                'source_name': insight.source_name,
                'raw_input': insight.raw_input
            }
        )

    def _load_persisted_state(self):
        """Load vetoes and modifiers from disk"""
        if self.vetoes_path.exists():
            with open(self.vetoes_path, 'r') as f:
                vetoes_data = json.load(f)
                for v in vetoes_data:
                    insight = YairInsight(
                        insight_id=v['insight_id'],
                        insight_type=InsightType.VETO,
                        timestamp=v['timestamp'],
                        source_name=v['source_name'],
                        veto_market_pattern=v['pattern'],
                        veto_reason=v['reason']
                    )
                    self._active_vetoes.append(insight)

        if self.modifiers_path.exists():
            with open(self.modifiers_path, 'r') as f:
                mods_data = json.load(f)
                for m in mods_data:
                    insight = YairInsight(
                        insight_id=m['insight_id'],
                        insight_type=InsightType.EDGE_MODIFIER,
                        timestamp=m['timestamp'],
                        source_name=m['source_name'],
                        target_market_id=m['target'],
                        edge_multiplier=m.get('edge_mult'),
                        confidence_adjustment=m.get('conf_adj')
                    )
                    self._active_modifiers.append(insight)

    def _save_persisted_state(self):
        """Save vetoes and modifiers to disk"""
        vetoes_data = []
        for v in self._active_vetoes:
            vetoes_data.append({
                'insight_id': v.insight_id,
                'timestamp': v.timestamp,
                'source_name': v.source_name,
                'pattern': v.veto_market_pattern,
                'reason': v.veto_reason
            })

        with open(self.vetoes_path, 'w') as f:
            json.dump(vetoes_data, f, indent=2)

        mods_data = []
        for m in self._active_modifiers:
            mods_data.append({
                'insight_id': m.insight_id,
                'timestamp': m.timestamp,
                'source_name': m.source_name,
                'target': m.target_market_id,
                'edge_mult': m.edge_multiplier,
                'conf_adj': m.confidence_adjustment
            })

        with open(self.modifiers_path, 'w') as f:
            json.dump(mods_data, f, indent=2)


# ============================================================================
# Interactive CLI for quick insight input
# ============================================================================

def interactive_cli():
    """
    Interactive CLI for Yair to input insights quickly.

    Commands:
    - Direct text: treated as insight
    - !veto <pattern>: Add a veto
    - !clear-veto <pattern>: Remove a veto
    - !list-vetoes: Show active vetoes
    - !status: Show current state
    - !quit: Exit
    """
    adapter = YairInsightsAdapter()

    print("=" * 60)
    print("Yair Insights Interactive CLI")
    print("=" * 60)
    print("\nEnter insights as natural language:")
    print("  'buy YES on trump-market, looks mispriced'")
    print("  'don't touch crypto today'")
    print("  'increase confidence on btc-100k by 20%'")
    print("\nCommands: !veto, !clear-veto, !list-vetoes, !status, !quit")
    print("=" * 60)

    while True:
        try:
            text = input("\n[yair] > ").strip()

            if not text:
                continue

            if text.lower() == '!quit':
                print("Exiting...")
                break

            elif text.lower() == '!status':
                print(f"\nPending insights: {len(adapter._pending_insights)}")
                print(f"Active vetoes: {len(adapter._active_vetoes)}")
                print(f"Active modifiers: {len(adapter._active_modifiers)}")

            elif text.lower() == '!list-vetoes':
                if adapter._active_vetoes:
                    print("\nActive vetoes:")
                    for v in adapter._active_vetoes:
                        print(f"  - {v.veto_market_pattern}: {v.veto_reason}")
                else:
                    print("\nNo active vetoes")

            elif text.lower().startswith('!veto '):
                pattern = text[6:].strip()
                adapter.submit_insight(f"avoid {pattern}")
                print(f"Added veto for: {pattern}")

            elif text.lower().startswith('!clear-veto '):
                pattern = text[12:].strip()
                adapter.clear_veto(pattern)
                print(f"Cleared veto: {pattern}")

            else:
                insight_id = adapter.submit_insight(text)
                print(f"Insight received: {insight_id}")

                # Process immediately
                signals = adapter.fetch_signals()
                if signals:
                    print(f"\nGenerated {len(signals)} signals:")
                    for sig in signals:
                        print(f"  - {sig.market_id}: {sig.side} @ {sig.edge:.1%} edge")

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


# ============================================================================
# Main entry point
# ============================================================================

def main():
    """Demo or run interactive CLI"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive_cli()
    else:
        print("Yair Insights Pipeline")
        print("=" * 50)
        print("\nThis module handles human expert insights:")
        print("- Direct alpha signals ('buy YES on trump market')")
        print("- Edge modifiers ('increase confidence by 20%')")
        print("- Vetoes ('don't touch crypto today')")
        print("\n'Yair's insights as needed for further golden sprinkles'")
        print("=" * 50)

        adapter = YairInsightsAdapter()

        print(f"\nInsights directory: {adapter.insights_dir}")
        print("\nTo use:")
        print("1. Drop JSON files in the insights directory")
        print("2. Use adapter.submit_insight('text') programmatically")
        print("3. Run with --interactive for CLI mode")

        # Demo
        print("\n--- Demo ---")
        adapter.submit_insight("buy YES on trump-2024 market, looks underpriced")
        adapter.submit_insight("don't touch crypto markets today")
        adapter.submit_insight("increase confidence on btc-100k by 15%")

        signals = adapter.fetch_signals()
        print(f"\nGenerated {len(signals)} signals")
        print(f"Active vetoes: {len(adapter._active_vetoes)}")
        print(f"Active modifiers: {len(adapter._active_modifiers)}")


if __name__ == '__main__':
    main()
