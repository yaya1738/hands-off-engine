#!/usr/bin/env python3
"""
DENSE AI - Maximum Intelligence Density
========================================

A densely-packed agentic AI system that maximizes capability
per operation. Uses ALL available intelligence sources.

Philosophy: DENSE = Maximum capability packed into every operation
- Multiple AI providers for redundancy and quality
- Web intelligence integration
- Local heuristics for speed
- Deep analysis combining all sources
- Rich context from every angle

Intelligence Stack (all used together):
1. External AI (Groq, Google AI, OpenAI) - Deep reasoning
2. Web Agent - Real-time market data
3. Local NLP - Fast pattern matching
4. Historical Analysis - Pattern recognition
5. Multi-source synthesis - Combined intelligence

Serving: Yair Siegel
"""

import os
import sys
import json
import time
import hashlib
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Setup paths
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

STATE_DIR = BASE_DIR / 'state'
CACHE_DIR = STATE_DIR / 'dense_cache'
STATE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Load environment
from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')

# Master identity
MASTER = "Yair Siegel"


# =============================================================================
# AI PROVIDERS - All available providers for maximum redundancy
# =============================================================================

class GroqProvider:
    """Groq - Ultra-fast inference (FREE tier)."""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-70b-versatile"
        self.available = bool(self.api_key)
        self.name = "groq"
        self.speed = "fast"

    def complete(self, prompt: str, system: str = None, max_tokens: int = 2000) -> Optional[str]:
        if not self.available:
            return None

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            r = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.3
                },
                timeout=60
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return None


class GoogleAIProvider:
    """Google AI - Gemini (FREE tier)."""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_AI_KEY") or os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model = "gemini-1.5-flash"
        self.available = bool(self.api_key)
        self.name = "google"
        self.speed = "medium"

    def complete(self, prompt: str, system: str = None, max_tokens: int = 2000) -> Optional[str]:
        if not self.available:
            return None

        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        try:
            r = requests.post(
                f"{self.base_url}/{self.model}:generateContent?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": 0.3
                    }
                },
                timeout=60
            )
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return None


class OpenAIProvider:
    """OpenAI - GPT-4 (paid, highest quality)."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4-turbo-preview"
        self.available = bool(self.api_key)
        self.name = "openai"
        self.speed = "slow"

    def complete(self, prompt: str, system: str = None, max_tokens: int = 2000) -> Optional[str]:
        if not self.available:
            return None

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            r = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.3
                },
                timeout=120
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return None


# =============================================================================
# LOCAL INTELLIGENCE - Fast heuristics
# =============================================================================

class LocalIntelligence:
    """Fast local analysis without API calls."""

    # Sentiment keywords
    BULLISH = {
        "bull", "bullish", "surge", "gain", "profit", "up", "high", "growth",
        "rally", "moon", "pump", "breakout", "support", "buy", "long",
        "accumulate", "strong", "win", "success", "increase", "rise"
    }
    BEARISH = {
        "bear", "bearish", "crash", "loss", "down", "low", "drop", "fall",
        "dump", "breakdown", "resistance", "sell", "short", "weak", "fail",
        "decrease", "decline", "fear", "panic", "collapse", "plunge"
    }

    # Crypto tickers
    KNOWN_TICKERS = {
        "BTC", "ETH", "SOL", "DOGE", "XRP", "ADA", "MATIC", "LINK",
        "UNI", "AVAX", "DOT", "ATOM", "NEAR", "APT", "ARB", "OP"
    }

    @classmethod
    def sentiment(cls, text: str) -> Dict[str, Any]:
        """Fast keyword-based sentiment analysis."""
        words = set(text.lower().split())
        pos = len(words & cls.BULLISH)
        neg = len(words & cls.BEARISH)

        if pos > neg * 1.5:
            label, score = "strongly_bullish", min(1.0, pos / 5)
        elif pos > neg:
            label, score = "bullish", min(0.7, pos / 7)
        elif neg > pos * 1.5:
            label, score = "strongly_bearish", min(1.0, neg / 5)
        elif neg > pos:
            label, score = "bearish", min(0.7, neg / 7)
        else:
            label, score = "neutral", 0.0

        return {
            "label": label,
            "score": score,
            "bullish_words": pos,
            "bearish_words": neg,
            "method": "local_keywords"
        }

    @classmethod
    def extract_entities(cls, text: str) -> Dict[str, List]:
        """Extract tickers, numbers, and key phrases."""
        import re

        # Extract numbers
        numbers = []
        for match in re.finditer(r'[\$]?([\d,]+\.?\d*)[%]?', text):
            try:
                n = float(match.group(1).replace(',', ''))
                numbers.append(n)
            except:
                pass

        # Extract tickers
        tickers = []
        for word in text.split():
            clean = word.strip('$.,!?()[]').upper()
            if clean in cls.KNOWN_TICKERS or (word.startswith('$') and 2 <= len(clean) <= 5):
                tickers.append(clean)

        # Extract percentages
        percentages = re.findall(r'([-+]?\d+\.?\d*)\s*%', text)

        return {
            "tickers": list(set(tickers)),
            "numbers": numbers[:10],
            "percentages": [float(p) for p in percentages[:5]]
        }

    @classmethod
    def quick_analysis(cls, data: Dict) -> Dict[str, Any]:
        """Quick rule-based market analysis."""
        signals = []
        score = 0.0

        # Price change signals (ensure numeric)
        try:
            price_change = float(data.get("price_change_24h", 0) or 0)
        except (TypeError, ValueError):
            price_change = 0.0
        if price_change > 10:
            signals.append(f"Strong pump +{price_change:.1f}%")
            score += 0.4
        elif price_change > 5:
            signals.append(f"Price spike +{price_change:.1f}%")
            score += 0.2
        elif price_change < -10:
            signals.append(f"Major dump {price_change:.1f}%")
            score -= 0.4
        elif price_change < -5:
            signals.append(f"Price drop {price_change:.1f}%")
            score -= 0.2

        # Fear & Greed (ensure numeric)
        try:
            fg = int(data.get("fear_greed", 50) or 50)
        except (TypeError, ValueError):
            fg = 50
        if fg < 20:
            signals.append(f"Extreme fear ({fg}) - contrarian BUY")
            score += 0.3
        elif fg < 35:
            signals.append(f"Fear zone ({fg})")
            score += 0.1
        elif fg > 80:
            signals.append(f"Extreme greed ({fg}) - contrarian SELL")
            score -= 0.3
        elif fg > 65:
            signals.append(f"Greed zone ({fg})")
            score -= 0.1

        # Determine action
        if score > 0.5:
            action = "STRONG_BUY"
        elif score > 0.2:
            action = "BUY"
        elif score < -0.5:
            action = "STRONG_SELL"
        elif score < -0.2:
            action = "SELL"
        else:
            action = "HOLD"

        return {
            "signals": signals,
            "score": score,
            "action": action,
            "confidence": min(abs(score), 1.0)
        }


# =============================================================================
# DENSE AI - Maximum Intelligence Density
# =============================================================================

@dataclass
class DenseResult:
    """Result from dense analysis."""
    success: bool
    content: str = ""
    provider: str = ""
    sources_used: List[str] = field(default_factory=list)
    latency_ms: int = 0
    local_analysis: Dict = field(default_factory=dict)
    web_data: Dict = field(default_factory=dict)
    ai_analysis: str = ""
    synthesis: str = ""
    error: str = ""


@dataclass
class DenseState:
    """State tracking for Dense AI."""
    total_calls: int = 0
    ai_calls: int = 0
    web_calls: int = 0
    local_calls: int = 0
    cache_hits: int = 0
    provider_usage: Dict[str, int] = field(default_factory=dict)
    last_call: str = ""
    errors: int = 0


class DenseAI:
    """
    Dense Agentic AI - Maximum intelligence packed into every operation.

    Combines:
    - Multiple AI providers (parallel queries for speed)
    - Web agent integration (real-time data)
    - Local intelligence (instant heuristics)
    - Historical patterns
    - Multi-source synthesis
    """

    def __init__(self):
        self.master = MASTER
        self.state = self._load_state()
        self._lock = threading.Lock()

        # Initialize AI providers (priority order)
        self.groq = GroqProvider()
        self.google = GoogleAIProvider()
        self.openai = OpenAIProvider()

        # Build provider list
        self.providers = []
        if self.groq.available:
            self.providers.append(self.groq)
        if self.google.available:
            self.providers.append(self.google)
        if self.openai.available:
            self.providers.append(self.openai)

        # Web agent (lazy load)
        self._web_agent = None

        # Cache
        self._cache: Dict[str, tuple] = {}
        self.cache_ttl = 300  # 5 min

        print(f"[DenseAI] Initialized for {self.master}")
        print(f"[DenseAI] AI Providers: {[p.name for p in self.providers]}")

    @property
    def web_agent(self):
        """Lazy load web agent."""
        if self._web_agent is None:
            try:
                from autonomous.web_agent import get_web_agent
                self._web_agent = get_web_agent()
            except Exception as e:
                print(f"[DenseAI] Web agent unavailable: {e}")
        return self._web_agent

    def _load_state(self) -> DenseState:
        state_file = STATE_DIR / "dense_ai_state.json"
        if state_file.exists():
            try:
                return DenseState(**json.load(open(state_file)))
            except:
                pass
        return DenseState()

    def _save_state(self):
        state_file = STATE_DIR / "dense_ai_state.json"
        with open(state_file, 'w') as f:
            json.dump(asdict(self.state), f, indent=2)

    def _cache_key(self, key: str) -> str:
        return hashlib.md5(key.encode()).hexdigest()[:16]

    def _get_cache(self, key: str) -> Optional[Any]:
        hkey = self._cache_key(key)
        if hkey in self._cache:
            value, ts = self._cache[hkey]
            if time.time() - ts < self.cache_ttl:
                return value
        return None

    def _set_cache(self, key: str, value: Any):
        self._cache[self._cache_key(key)] = (value, time.time())

    # =========================================================================
    # CORE: Dense Analysis
    # =========================================================================

    def dense_analyze(
        self,
        query: str,
        context: Dict = None,
        use_web: bool = True,
        use_ai: bool = True,
        parallel: bool = True
    ) -> DenseResult:
        """
        Perform DENSE analysis - maximum intelligence from all sources.

        Gathers:
        1. Local heuristics (instant)
        2. Web data (if available)
        3. AI analysis (if providers available)
        4. Synthesizes all sources
        """
        start = time.time()
        sources = []
        context = context or {}

        with self._lock:
            self.state.total_calls += 1

        # === 1. LOCAL INTELLIGENCE (Always, instant) ===
        local_result = {
            "sentiment": LocalIntelligence.sentiment(query),
            "entities": LocalIntelligence.extract_entities(query)
        }
        sources.append("local")
        with self._lock:
            self.state.local_calls += 1

        # === 2. WEB DATA (If enabled and available) ===
        web_data = {}
        if use_web and self.web_agent:
            try:
                self.web_agent.fetch_all()
                web_data = self.web_agent.get_summary()
                sources.append("web")
                with self._lock:
                    self.state.web_calls += 1
            except Exception as e:
                web_data = {"error": str(e)}

        # Add context to local analysis
        if web_data.get("crypto"):
            btc = web_data["crypto"].get("btc", {})
            context["btc_price"] = btc.get("price", 0)
            context["price_change_24h"] = btc.get("price_change_24h", 0)
        if web_data.get("sentiment", {}).get("fear_greed"):
            context["fear_greed"] = web_data["sentiment"]["fear_greed"].get("value", 50)

        # Quick local analysis with context
        quick_analysis = LocalIntelligence.quick_analysis(context)
        local_result["quick_analysis"] = quick_analysis

        # === 3. AI ANALYSIS (If enabled and providers available) ===
        ai_response = ""
        provider_used = ""

        if use_ai and self.providers:
            system_prompt = f"""You are a dense market intelligence AI serving {self.master}.
Analyze the query and context to provide maximum insight density.
Be specific, actionable, and data-driven. Include concrete numbers when available.
Focus on: opportunities, risks, recommended actions, confidence levels."""

            # Build rich context prompt
            context_str = json.dumps({
                "query": query,
                "local_sentiment": local_result["sentiment"],
                "entities": local_result["entities"],
                "quick_signals": quick_analysis,
                "market_context": context,
                "web_data_summary": {
                    "btc_price": context.get("btc_price"),
                    "price_change": context.get("price_change_24h"),
                    "fear_greed": context.get("fear_greed"),
                    "news_count": len(web_data.get("news", [])) if web_data else 0
                }
            }, indent=2)

            full_prompt = f"""QUERY: {query}

CONTEXT DATA:
{context_str}

Provide dense analysis with:
1. Key insight (1 sentence)
2. Signals detected (bulleted)
3. Recommended action
4. Risk assessment
5. Confidence level (0-100%)"""

            # Try providers (in order, or parallel)
            if parallel and len(self.providers) > 1:
                # Parallel query - first response wins
                with ThreadPoolExecutor(max_workers=3) as executor:
                    futures = {
                        executor.submit(p.complete, full_prompt, system_prompt): p
                        for p in self.providers
                    }
                    for future in as_completed(futures, timeout=30):
                        provider = futures[future]
                        try:
                            result = future.result()
                            if result:
                                ai_response = result
                                provider_used = provider.name
                                break
                        except:
                            pass
            else:
                # Sequential fallback
                for provider in self.providers:
                    result = provider.complete(full_prompt, system_prompt)
                    if result:
                        ai_response = result
                        provider_used = provider.name
                        break

            if provider_used:
                sources.append(f"ai:{provider_used}")
                with self._lock:
                    self.state.ai_calls += 1
                    self.state.provider_usage[provider_used] = \
                        self.state.provider_usage.get(provider_used, 0) + 1

        # === 4. SYNTHESIS ===
        synthesis = self._synthesize(query, local_result, web_data, ai_response, quick_analysis)

        # Calculate latency
        latency = int((time.time() - start) * 1000)

        # Update state
        with self._lock:
            self.state.last_call = datetime.now(timezone.utc).isoformat()
            self._save_state()

        return DenseResult(
            success=True,
            content=synthesis,
            provider=provider_used,
            sources_used=sources,
            latency_ms=latency,
            local_analysis=local_result,
            web_data=web_data,
            ai_analysis=ai_response,
            synthesis=synthesis
        )

    def _synthesize(
        self,
        query: str,
        local: Dict,
        web: Dict,
        ai: str,
        quick: Dict
    ) -> str:
        """Synthesize all intelligence sources into dense output."""
        parts = []

        # Header
        parts.append(f"=== DENSE ANALYSIS for {self.master} ===")
        parts.append(f"Query: {query[:100]}")
        parts.append("")

        # Quick signals
        if quick.get("signals"):
            parts.append("SIGNALS:")
            for sig in quick["signals"]:
                parts.append(f"  - {sig}")
            parts.append(f"  ACTION: {quick['action']} (confidence: {quick['confidence']:.0%})")
            parts.append("")

        # Local sentiment
        sent = local.get("sentiment", {})
        parts.append(f"SENTIMENT: {sent.get('label', 'unknown')} (score: {sent.get('score', 0):.2f})")

        # Entities
        entities = local.get("entities", {})
        if entities.get("tickers"):
            parts.append(f"TICKERS: {', '.join(entities['tickers'])}")
        if entities.get("percentages"):
            parts.append(f"PERCENTAGES: {entities['percentages']}")
        parts.append("")

        # Web data
        if web and not web.get("error"):
            crypto = web.get("crypto", {}).get("btc", {})
            if crypto.get("price"):
                parts.append(f"BTC: ${crypto['price']:,.0f} ({crypto.get('price_change_24h', 0):+.1f}%)")
            fg = web.get("sentiment", {}).get("fear_greed", {})
            if fg.get("value"):
                parts.append(f"FEAR & GREED: {fg['value']} ({fg.get('classification', '')})")
            parts.append("")

        # AI Analysis
        if ai:
            parts.append("AI ANALYSIS:")
            parts.append(ai[:1500])  # Truncate if needed
            parts.append("")

        parts.append(f"[Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")

        return "\n".join(parts)

    # =========================================================================
    # SPECIALIZED METHODS
    # =========================================================================

    def analyze_market(self, asset: str = "BTC") -> DenseResult:
        """Dense analysis of market conditions."""
        return self.dense_analyze(
            f"Analyze current {asset} market conditions, key levels, and trading opportunities",
            context={"asset": asset}
        )

    def analyze_trade(self, market: str, price: float) -> DenseResult:
        """Dense analysis for a specific trade."""
        return self.dense_analyze(
            f"Should I trade '{market}' at current price {price}? Analyze edge and risk.",
            context={"market": market, "current_price": price}
        )

    def analyze_news(self, headlines: List[str]) -> DenseResult:
        """Dense analysis of news headlines."""
        return self.dense_analyze(
            f"Analyze these market headlines for trading signals:\n" +
            "\n".join(f"- {h}" for h in headlines[:10]),
            context={"headlines": headlines}
        )

    def quick_sentiment(self, text: str) -> Dict:
        """Quick local sentiment (no AI calls)."""
        return LocalIntelligence.sentiment(text)

    def quick_signals(self, data: Dict) -> Dict:
        """Quick local signals (no AI calls)."""
        return LocalIntelligence.quick_analysis(data)

    # =========================================================================
    # STATUS
    # =========================================================================

    def get_status(self) -> Dict:
        """Get agent status."""
        return {
            "master": self.master,
            "providers": {
                "groq": self.groq.available,
                "google": self.google.available,
                "openai": self.openai.available,
                "total": len(self.providers)
            },
            "web_agent": self.web_agent is not None,
            "state": asdict(self.state),
            "cache_size": len(self._cache)
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_dense_ai: Optional[DenseAI] = None


def get_dense_ai() -> DenseAI:
    """Get or create global Dense AI instance."""
    global _dense_ai
    if _dense_ai is None:
        _dense_ai = DenseAI()
    return _dense_ai


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Dense AI - Maximum Intelligence Density")
    parser.add_argument("command", choices=["status", "analyze", "market", "test", "daemon"])
    parser.add_argument("--query", help="Query to analyze")
    parser.add_argument("--asset", default="BTC", help="Asset for market analysis")
    parser.add_argument("--interval", type=int, default=300, help="Daemon interval (seconds)")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI providers")
    parser.add_argument("--no-web", action="store_true", help="Skip web data")

    args = parser.parse_args()
    ai = get_dense_ai()

    if args.command == "status":
        status = ai.get_status()
        print(f"\n=== Dense AI Status ===")
        print(f"Master: {status['master']}")
        print(f"\nProviders:")
        print(f"  Groq: {'Available' if status['providers']['groq'] else 'Not configured'}")
        print(f"  Google: {'Available' if status['providers']['google'] else 'Not configured'}")
        print(f"  OpenAI: {'Available' if status['providers']['openai'] else 'Not configured'}")
        print(f"  Total: {status['providers']['total']}")
        print(f"\nWeb Agent: {'Connected' if status['web_agent'] else 'Not available'}")
        print(f"\nUsage:")
        print(f"  Total calls: {status['state']['total_calls']}")
        print(f"  AI calls: {status['state']['ai_calls']}")
        print(f"  Web calls: {status['state']['web_calls']}")
        print(f"  Local calls: {status['state']['local_calls']}")
        print(f"  Provider usage: {status['state']['provider_usage']}")

    elif args.command == "analyze":
        query = args.query or "What's the current market sentiment and any opportunities?"
        print(f"Analyzing: {query}\n")
        result = ai.dense_analyze(query, use_ai=not args.no_ai, use_web=not args.no_web)
        print(result.synthesis)
        print(f"\n[Sources: {', '.join(result.sources_used)}] [Latency: {result.latency_ms}ms]")

    elif args.command == "market":
        print(f"Dense Market Analysis: {args.asset}\n")
        result = ai.analyze_market(args.asset)
        print(result.synthesis)
        print(f"\n[Sources: {', '.join(result.sources_used)}] [Latency: {result.latency_ms}ms]")

    elif args.command == "test":
        print("=== Dense AI Test ===\n")

        # Test local intelligence
        print("1. Local Intelligence:")
        sent = ai.quick_sentiment("Bitcoin surges past $100k as bulls dominate")
        print(f"   Sentiment: {sent['label']} ({sent['score']:.2f})")

        signals = ai.quick_signals({"price_change_24h": 8.5, "fear_greed": 25})
        print(f"   Signals: {signals['signals']}")
        print(f"   Action: {signals['action']}")

        # Test dense analysis
        print("\n2. Dense Analysis (all sources):")
        result = ai.dense_analyze("Should I buy BTC right now?")
        print(f"   Sources: {result.sources_used}")
        print(f"   Latency: {result.latency_ms}ms")
        print(f"\n{result.synthesis[:500]}...")

        print("\n=== Test Complete ===")

    elif args.command == "daemon":
        print(f"=== Dense AI Daemon ===")
        print(f"Serving: {ai.master}")
        print(f"Interval: {args.interval}s")
        print(f"Providers: {[p.name for p in ai.providers]}\n")

        while True:
            try:
                result = ai.analyze_market("BTC")

                # Extract key info
                quick = result.local_analysis.get("quick_analysis", {})
                action = quick.get("action", "UNKNOWN")
                signals = len(quick.get("signals", []))

                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] Action: {action} | Signals: {signals} | Sources: {result.sources_used} | {result.latency_ms}ms")

            except Exception as e:
                print(f"[ERROR] {e}")

            time.sleep(args.interval)


if __name__ == "__main__":
    main()
