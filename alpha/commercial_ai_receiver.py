#!/usr/bin/env python3
"""
Commercial AI Webhook Receiver: Ingest Mispricing Signals from AI Products
==========================================================================

This module receives alpha signals from commercial AI products:
- ChatGPT (via API or manual input)
- Claude (via API or manual input)
- Perplexity
- Custom AI analysis pipelines

These AI products can identify mispriced markets on Polymarket amazingly well.
This module provides the ingestion point to pipe those insights into
the automated trading system.

Input Methods:
1. Direct API push (webhook endpoint)
2. File drop (JSON/JSONL files in inbox directory)
3. Manual entry (CLI interface)
4. Programmatic Python API

Philosophy: "AI commercial products can tell which markets are mispriced on Polymarket amazingly"
"""

import json
import sys
import os
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass
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


class AIProvider(Enum):
    """Commercial AI providers"""
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    PERPLEXITY = "perplexity"
    GEMINI = "gemini"
    CUSTOM = "custom"


@dataclass
class AISignalInput:
    """
    Flexible input format for AI-generated signals.

    The AI might provide varying levels of detail, so
    we accept a flexible schema and normalize it.
    """
    # Required fields
    market_id: str                    # Polymarket market slug or URL
    recommendation: str               # "BUY YES", "BUY NO", "SELL YES", "SELL NO"

    # Optional but valuable
    fair_price: Optional[float]       # AI's estimated fair probability
    market_price: Optional[float]     # Current market price (AI might include)
    confidence: Optional[str]         # "high", "medium", "low" or 0.0-1.0
    reasoning: Optional[str]          # AI's explanation

    # Metadata
    ai_provider: AIProvider
    timestamp: Optional[str]
    raw_response: Optional[str]       # Full AI response for audit


class AISignalNormalizer:
    """
    Normalizes varying AI input formats to unified signals.

    AI outputs are messy - this handles:
    - "BUY YES" vs "YES" vs "buy the yes side"
    - Confidence as string vs number
    - Missing fields with reasonable defaults
    """

    def __init__(self):
        # Keywords to detect recommendation
        self.yes_keywords = ['buy yes', 'yes', 'bullish', 'will happen', 'likely']
        self.no_keywords = ['buy no', 'no', 'bearish', 'won\'t happen', 'unlikely']

    def normalize(self, raw_input: Dict, provider: AIProvider) -> Optional[AISignalInput]:
        """
        Normalize raw AI output to AISignalInput.

        Accepts various formats:
        - {"market": "...", "action": "BUY YES", "confidence": "high"}
        - {"market_id": "...", "side": "YES", "fair_price": 0.65}
        - Natural language strings
        """
        # Extract market ID (various field names)
        market_id = (
            raw_input.get('market_id') or
            raw_input.get('market') or
            raw_input.get('slug') or
            raw_input.get('url', '').split('/')[-1] or
            ''
        )

        if not market_id:
            return None

        # Extract recommendation
        recommendation = self._extract_recommendation(raw_input)
        if not recommendation:
            return None

        # Extract fair price
        fair_price = self._extract_price(raw_input, ['fair_price', 'fair', 'probability', 'prob'])

        # Extract market price
        market_price = self._extract_price(raw_input, ['market_price', 'current_price', 'price'])

        # Extract confidence
        confidence = self._extract_confidence(raw_input)

        # Extract reasoning
        reasoning = (
            raw_input.get('reasoning') or
            raw_input.get('explanation') or
            raw_input.get('rationale') or
            raw_input.get('analysis') or
            ''
        )

        return AISignalInput(
            market_id=market_id,
            recommendation=recommendation,
            fair_price=fair_price,
            market_price=market_price,
            confidence=confidence,
            reasoning=reasoning,
            ai_provider=provider,
            timestamp=raw_input.get('timestamp', datetime.now(timezone.utc).isoformat()),
            raw_response=raw_input.get('raw_response')
        )

    def _extract_recommendation(self, raw_input: Dict) -> Optional[str]:
        """Extract and normalize recommendation"""
        # Check various field names
        rec = (
            raw_input.get('recommendation') or
            raw_input.get('action') or
            raw_input.get('side') or
            raw_input.get('signal') or
            ''
        ).lower()

        # Map to standard format
        if any(kw in rec for kw in self.yes_keywords):
            return "BUY YES"
        elif any(kw in rec for kw in self.no_keywords):
            return "BUY NO"
        elif rec in ['yes', 'y']:
            return "BUY YES"
        elif rec in ['no', 'n']:
            return "BUY NO"

        return None

    def _extract_price(self, raw_input: Dict, field_names: List[str]) -> Optional[float]:
        """Extract price from various field names"""
        for field in field_names:
            val = raw_input.get(field)
            if val is not None:
                try:
                    price = float(val)
                    # Handle percentage vs decimal
                    if price > 1:
                        price = price / 100
                    return max(0.01, min(0.99, price))
                except (ValueError, TypeError):
                    continue
        return None

    def _extract_confidence(self, raw_input: Dict) -> Optional[str]:
        """Extract and normalize confidence"""
        conf = raw_input.get('confidence')
        if conf is None:
            return None

        if isinstance(conf, (int, float)):
            return str(conf)

        conf = str(conf).lower()
        if conf in ['high', 'very high', 'strong']:
            return '0.85'
        elif conf in ['medium', 'moderate', 'med']:
            return '0.65'
        elif conf in ['low', 'weak']:
            return '0.45'

        return conf


class CommercialAIReceiver(AlphaSourceAdapter):
    """
    Adapter that receives and processes AI-generated alpha signals.

    Supports multiple input methods:
    1. File inbox (JSON/JSONL files)
    2. Direct Python API calls
    3. Webhook endpoint (when run as server)
    """

    def __init__(
        self,
        inbox_dir: Path = None,
        archive_dir: Path = None,
        min_confidence: float = 0.5
    ):
        self.state_dir = Path(__file__).parent.parent / 'state'
        self.inbox_dir = inbox_dir or self.state_dir / 'ai-signals-inbox'
        self.archive_dir = archive_dir or self.state_dir / 'ai-signals-archive'
        self.min_confidence = min_confidence

        # Create directories
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        self.normalizer = AISignalNormalizer()

        # In-memory signal queue (for direct API usage)
        self._pending_signals: List[AISignalInput] = []

    @property
    def source_type(self) -> SignalSource:
        return SignalSource.COMMERCIAL_AI

    def is_available(self) -> bool:
        """Always available - we can always receive signals"""
        return True

    def fetch_signals(self) -> List[UnifiedAlphaSignal]:
        """
        Fetch all pending AI signals from inbox and memory queue.
        """
        signals = []

        # 1. Process file inbox
        file_signals = self._process_inbox_files()
        signals.extend(file_signals)

        # 2. Process memory queue
        for ai_input in self._pending_signals:
            unified = self._convert_to_unified(ai_input)
            if unified:
                signals.append(unified)

        # Clear memory queue after processing
        self._pending_signals = []

        return signals

    def submit_signal(
        self,
        market_id: str,
        side: str,
        fair_price: float = None,
        confidence: float = None,
        reasoning: str = "",
        provider: AIProvider = AIProvider.CUSTOM
    ) -> str:
        """
        Programmatic API to submit a signal directly.

        Returns:
            Signal ID for tracking
        """
        signal_input = AISignalInput(
            market_id=market_id,
            recommendation=f"BUY {side.upper()}",
            fair_price=fair_price,
            market_price=None,
            confidence=str(confidence) if confidence else None,
            reasoning=reasoning,
            ai_provider=provider,
            timestamp=datetime.now(timezone.utc).isoformat(),
            raw_response=None
        )

        self._pending_signals.append(signal_input)

        signal_id = hashlib.md5(
            f"{market_id}_{side}_{time.time()}".encode()
        ).hexdigest()[:12]

        print(f"[AI Receiver] Queued signal {signal_id}: {side} on {market_id}")
        return signal_id

    def submit_from_json(self, json_data: Dict, provider: AIProvider = AIProvider.CUSTOM) -> Optional[str]:
        """
        Submit a signal from JSON data (e.g., AI API response).

        Accepts flexible format - normalizer handles variations.
        """
        normalized = self.normalizer.normalize(json_data, provider)
        if normalized:
            self._pending_signals.append(normalized)
            return f"queued_{len(self._pending_signals)}"
        return None

    def submit_chatgpt_response(self, response: str, market_id: str = None) -> Optional[str]:
        """
        Parse and submit a ChatGPT response about a market.

        Example response:
        "Based on my analysis, the market 'Will X happen?' is mispriced.
         The current price of 0.35 seems too low. Fair value is around 0.55.
         Recommendation: BUY YES with high confidence."
        """
        parsed = self._parse_natural_language(response)
        if market_id:
            parsed['market_id'] = market_id

        return self.submit_from_json(parsed, AIProvider.CHATGPT)

    def submit_claude_response(self, response: str, market_id: str = None) -> Optional[str]:
        """Parse and submit a Claude response"""
        parsed = self._parse_natural_language(response)
        if market_id:
            parsed['market_id'] = market_id

        return self.submit_from_json(parsed, AIProvider.CLAUDE)

    def _parse_natural_language(self, text: str) -> Dict:
        """
        Parse natural language AI response into structured data.

        This is a simple parser - for production, could use
        another AI call to extract structured data.
        """
        text_lower = text.lower()

        result = {
            'raw_response': text
        }

        # Extract recommendation
        if 'buy yes' in text_lower or 'bullish' in text_lower:
            result['recommendation'] = 'BUY YES'
        elif 'buy no' in text_lower or 'bearish' in text_lower:
            result['recommendation'] = 'BUY NO'

        # Extract confidence
        if 'high confidence' in text_lower or 'very confident' in text_lower:
            result['confidence'] = 'high'
        elif 'medium confidence' in text_lower or 'moderate' in text_lower:
            result['confidence'] = 'medium'
        elif 'low confidence' in text_lower:
            result['confidence'] = 'low'

        # Try to extract prices (simple regex-like parsing)
        import re

        # Look for "fair value is X" or "should be X"
        fair_match = re.search(r'fair (?:value|price|probability)[^\d]*(\d+\.?\d*)', text_lower)
        if fair_match:
            result['fair_price'] = float(fair_match.group(1))

        # Look for "current price is X"
        current_match = re.search(r'current (?:price|probability)[^\d]*(\d+\.?\d*)', text_lower)
        if current_match:
            result['market_price'] = float(current_match.group(1))

        # Use the whole text as reasoning
        result['reasoning'] = text[:500]  # Truncate for storage

        return result

    def _process_inbox_files(self) -> List[UnifiedAlphaSignal]:
        """Process JSON/JSONL files in the inbox directory"""
        signals = []

        for file_path in self.inbox_dir.glob('*.json'):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Handle single signal or array
                if isinstance(data, list):
                    for item in data:
                        unified = self._process_json_item(item, file_path)
                        if unified:
                            signals.append(unified)
                else:
                    unified = self._process_json_item(data, file_path)
                    if unified:
                        signals.append(unified)

                # Archive processed file
                archive_path = self.archive_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_path.name}"
                file_path.rename(archive_path)

            except Exception as e:
                print(f"[AI Receiver] Error processing {file_path}: {e}")

        # Also process JSONL files
        for file_path in self.inbox_dir.glob('*.jsonl'):
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            item = json.loads(line)
                            unified = self._process_json_item(item, file_path)
                            if unified:
                                signals.append(unified)

                # Archive
                archive_path = self.archive_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_path.name}"
                file_path.rename(archive_path)

            except Exception as e:
                print(f"[AI Receiver] Error processing {file_path}: {e}")

        return signals

    def _process_json_item(self, item: Dict, source_file: Path) -> Optional[UnifiedAlphaSignal]:
        """Process a single JSON item into a unified signal"""
        # Detect provider from file name or content
        provider = AIProvider.CUSTOM
        if 'chatgpt' in source_file.name.lower():
            provider = AIProvider.CHATGPT
        elif 'claude' in source_file.name.lower():
            provider = AIProvider.CLAUDE
        elif 'perplexity' in source_file.name.lower():
            provider = AIProvider.PERPLEXITY

        normalized = self.normalizer.normalize(item, provider)
        if normalized:
            return self._convert_to_unified(normalized)
        return None

    def _convert_to_unified(self, ai_input: AISignalInput) -> Optional[UnifiedAlphaSignal]:
        """Convert AISignalInput to UnifiedAlphaSignal"""
        # Parse side from recommendation
        side = "YES" if "YES" in ai_input.recommendation.upper() else "NO"

        # Get fair price (default to estimate based on side)
        fair_price = ai_input.fair_price
        market_price = ai_input.market_price or 0.5  # Default if not provided

        if fair_price is None:
            # Estimate based on side
            fair_price = market_price + 0.1 if side == "YES" else market_price - 0.1
            fair_price = max(0.05, min(0.95, fair_price))

        # Calculate edge
        edge = abs(fair_price - market_price)

        # Parse confidence
        confidence = 0.65  # Default
        if ai_input.confidence:
            try:
                confidence = float(ai_input.confidence)
            except ValueError:
                pass

        # Skip low confidence signals
        if confidence < self.min_confidence:
            return None

        return create_signal(
            market_id=ai_input.market_id,
            market_name=f"AI Signal: {ai_input.market_id}",
            source=SignalSource.COMMERCIAL_AI,
            side=side,
            fair_price=fair_price,
            market_price=market_price,
            confidence=confidence,
            urgency=SignalUrgency.HIGH,  # AI signals are usually time-sensitive
            category="ai_detected",
            reasoning=ai_input.reasoning or f"AI ({ai_input.ai_provider.value}) recommends {ai_input.recommendation}",
            raw_data={
                'provider': ai_input.ai_provider.value,
                'raw_recommendation': ai_input.recommendation,
                'raw_response': ai_input.raw_response
            }
        )


# ============================================================================
# Simple HTTP webhook server (optional - for receiving external signals)
# ============================================================================

def create_webhook_server(receiver: CommercialAIReceiver, port: int = 8080):
    """
    Create a simple HTTP server to receive webhook signals.

    POST /signal with JSON body to submit signals.
    """
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json

    class SignalHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path == '/signal':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)

                try:
                    data = json.loads(post_data)
                    signal_id = receiver.submit_from_json(data)

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'status': 'queued',
                        'signal_id': signal_id
                    }).encode())
                except Exception as e:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'status': 'error',
                        'message': str(e)
                    }).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            print(f"[Webhook] {args[0]}")

    server = HTTPServer(('0.0.0.0', port), SignalHandler)
    print(f"[Webhook] Server listening on port {port}")
    return server


# ============================================================================
# Main entry point
# ============================================================================

def main():
    """Demo the Commercial AI Receiver"""
    print("Commercial AI Webhook Receiver")
    print("=" * 50)
    print("\nThis module receives alpha signals from AI products:")
    print("- ChatGPT mispricing detection")
    print("- Claude market analysis")
    print("- Perplexity research signals")
    print("- Custom AI pipelines")
    print("\n'AI commercial products can tell which markets are mispriced amazingly'")
    print("=" * 50)

    receiver = CommercialAIReceiver()

    print(f"\nInbox directory: {receiver.inbox_dir}")
    print(f"Archive directory: {receiver.archive_dir}")
    print("\nTo submit signals:")
    print("1. Drop JSON files in the inbox directory")
    print("2. Use receiver.submit_signal() programmatically")
    print("3. Use receiver.submit_chatgpt_response() for natural language")

    # Demo: submit a test signal
    print("\n--- Demo: Submitting test signal ---")
    signal_id = receiver.submit_signal(
        market_id="will-trump-win-2024",
        side="YES",
        fair_price=0.65,
        confidence=0.8,
        reasoning="ChatGPT analysis indicates market is underpricing event probability",
        provider=AIProvider.CHATGPT
    )
    print(f"Submitted signal: {signal_id}")

    # Fetch and display
    signals = receiver.fetch_signals()
    print(f"\nFetched {len(signals)} signals:")
    for sig in signals:
        print(f"  - {sig.market_id}: {sig.side} @ {sig.edge:.1%} edge")


if __name__ == '__main__':
    main()
