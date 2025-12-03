#!/usr/bin/env python3
"""
AGENTIC WEB AGENT - Self-Hosted Internet Intelligence
======================================================

A lightweight, self-hosted web agent that gathers internet data
WITHOUT requiring AI APIs. Pure Python, zero AI cost.

Features:
- Multi-source data aggregation
- Scheduled fetching
- Smart caching
- Alert generation
- Integration with trading system

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
CACHE_DIR = STATE_DIR / 'web_cache'
STATE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Try to import notification system
try:
    from ai.unified_ai import send_master_notification, log_action
    HAS_NOTIFICATIONS = True
except ImportError:
    HAS_NOTIFICATIONS = False
    def send_master_notification(msg, priority="normal"): print(f"[{priority}] {msg}")
    def log_action(agent, action, result): pass


# =============================================================================
# DATA SOURCES - All FREE, no API keys needed
# =============================================================================

DATA_SOURCES = {
    # Crypto prices
    "coingecko_prices": {
        "url": "https://api.coingecko.com/api/v3/simple/price",
        "params": {"ids": "bitcoin,ethereum,solana,polygon", "vs_currencies": "usd,usd_24h_change"},
        "interval": 300,  # 5 min
        "parser": "json"
    },

    # Polymarket markets
    "polymarket_active": {
        "url": "https://gamma-api.polymarket.com/markets",
        "params": {"limit": 20, "active": "true"},
        "interval": 600,  # 10 min
        "parser": "json"
    },

    # Crypto news
    "crypto_news": {
        "url": "https://min-api.cryptocompare.com/data/v2/news/",
        "params": {"lang": "EN", "categories": "Trading,Market"},
        "interval": 900,  # 15 min
        "parser": "json_data"
    },

    # Fear & Greed Index
    "fear_greed": {
        "url": "https://api.alternative.me/fng/",
        "params": {"limit": 1},
        "interval": 3600,  # 1 hour
        "parser": "json_data"
    },

    # Bitcoin dominance
    "btc_dominance": {
        "url": "https://api.coingecko.com/api/v3/global",
        "params": {},
        "interval": 1800,  # 30 min
        "parser": "json_data"
    }
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FetchResult:
    """Result of a web fetch operation."""
    source: str
    success: bool
    data: Any = None
    error: str = None
    timestamp: str = ""
    cached: bool = False
    latency_ms: int = 0


@dataclass
class Alert:
    """An alert generated from data analysis."""
    source: str
    alert_type: str  # price_spike, news_important, market_move
    message: str
    severity: str  # low, medium, high, critical
    data: Dict = field(default_factory=dict)
    timestamp: str = ""


@dataclass
class WebAgentState:
    """State of the web agent."""
    last_run: str = ""
    total_fetches: int = 0
    successful_fetches: int = 0
    failed_fetches: int = 0
    alerts_generated: int = 0
    cache_hits: int = 0
    sources_status: Dict[str, Dict] = field(default_factory=dict)


# =============================================================================
# WEB AGENT
# =============================================================================

class WebAgent:
    """
    Self-hosted agentic web agent.

    Autonomously gathers data from the internet without AI costs.
    Runs on schedules, caches intelligently, generates alerts.
    """

    def __init__(self, sources: Dict = None):
        self.sources = sources or DATA_SOURCES
        self.state = self._load_state()
        self.cache = {}
        self.alerts: List[Alert] = []
        self._lock = threading.Lock()

        # Alert thresholds
        self.thresholds = {
            "btc_price_change_pct": 5.0,
            "eth_price_change_pct": 7.0,
            "fear_greed_extreme": 20,  # Below 20 = extreme fear
            "fear_greed_greed": 80,    # Above 80 = extreme greed
        }

        log_action("web_agent", "init", f"sources={len(self.sources)}")

    def _load_state(self) -> WebAgentState:
        """Load agent state from disk."""
        state_file = STATE_DIR / "web_agent_state.json"
        if state_file.exists():
            try:
                data = json.load(open(state_file))
                return WebAgentState(**data)
            except:
                pass
        return WebAgentState()

    def _save_state(self):
        """Save agent state to disk."""
        state_file = STATE_DIR / "web_agent_state.json"
        with open(state_file, 'w') as f:
            json.dump(asdict(self.state), f, indent=2)

    def _get_cache_key(self, source: str, params: Dict) -> str:
        """Generate cache key for a request."""
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(f"{source}:{param_str}".encode()).hexdigest()

    def _is_cache_valid(self, source: str, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        cache_file = CACHE_DIR / f"{cache_key}.json"
        if not cache_file.exists():
            return False

        try:
            data = json.load(open(cache_file))
            cached_time = datetime.fromisoformat(data.get("timestamp", ""))
            interval = self.sources.get(source, {}).get("interval", 300)
            return (datetime.now(timezone.utc) - cached_time).total_seconds() < interval
        except:
            return False

    def _load_cache(self, cache_key: str) -> Optional[Dict]:
        """Load data from cache."""
        cache_file = CACHE_DIR / f"{cache_key}.json"
        if cache_file.exists():
            try:
                return json.load(open(cache_file))
            except:
                pass
        return None

    def _save_cache(self, cache_key: str, data: Any):
        """Save data to cache."""
        cache_file = CACHE_DIR / f"{cache_key}.json"
        cache_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)

    def fetch_source(self, source: str, force: bool = False) -> FetchResult:
        """Fetch data from a single source."""
        config = self.sources.get(source)
        if not config:
            return FetchResult(source=source, success=False, error="Unknown source")

        url = config["url"]
        params = config.get("params", {})
        parser = config.get("parser", "json")

        cache_key = self._get_cache_key(source, params)

        # Check cache
        if not force and self._is_cache_valid(source, cache_key):
            cached = self._load_cache(cache_key)
            if cached:
                with self._lock:
                    self.state.cache_hits += 1
                return FetchResult(
                    source=source,
                    success=True,
                    data=cached.get("data"),
                    timestamp=cached.get("timestamp"),
                    cached=True
                )

        # Fetch from web
        start = time.time()
        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            latency = int((time.time() - start) * 1000)

            # Parse response
            if parser == "json":
                data = r.json()
            elif parser == "json_data":
                data = r.json().get("Data", r.json().get("data", r.json()))
            else:
                data = r.text

            # Cache result
            self._save_cache(cache_key, data)

            with self._lock:
                self.state.total_fetches += 1
                self.state.successful_fetches += 1
                self.state.sources_status[source] = {
                    "last_success": datetime.now(timezone.utc).isoformat(),
                    "status": "ok"
                }

            return FetchResult(
                source=source,
                success=True,
                data=data,
                timestamp=datetime.now(timezone.utc).isoformat(),
                latency_ms=latency
            )

        except Exception as e:
            with self._lock:
                self.state.total_fetches += 1
                self.state.failed_fetches += 1
                self.state.sources_status[source] = {
                    "last_error": datetime.now(timezone.utc).isoformat(),
                    "status": "error",
                    "error": str(e)
                }

            return FetchResult(
                source=source,
                success=False,
                error=str(e),
                timestamp=datetime.now(timezone.utc).isoformat()
            )

    def fetch_all(self, parallel: bool = True, force: bool = False) -> Dict[str, FetchResult]:
        """Fetch data from all sources."""
        results = {}

        if parallel:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(self.fetch_source, source, force): source
                    for source in self.sources
                }
                for future in as_completed(futures):
                    source = futures[future]
                    results[source] = future.result()
        else:
            for source in self.sources:
                results[source] = self.fetch_source(source, force)

        self.state.last_run = datetime.now(timezone.utc).isoformat()
        self._save_state()

        # Analyze for alerts
        self._analyze_for_alerts(results)

        return results

    def _analyze_for_alerts(self, results: Dict[str, FetchResult]):
        """Analyze fetched data for alert conditions."""
        alerts = []

        # Check crypto prices
        if "coingecko_prices" in results and results["coingecko_prices"].success:
            prices = results["coingecko_prices"].data
            if prices:
                btc = prices.get("bitcoin", {})
                if btc.get("usd_24h_change", 0) > self.thresholds["btc_price_change_pct"]:
                    alerts.append(Alert(
                        source="coingecko_prices",
                        alert_type="price_spike",
                        message=f"BTC up {btc['usd_24h_change']:.1f}% in 24h",
                        severity="medium",
                        data={"price": btc.get("usd"), "change": btc.get("usd_24h_change")},
                        timestamp=datetime.now(timezone.utc).isoformat()
                    ))
                elif btc.get("usd_24h_change", 0) < -self.thresholds["btc_price_change_pct"]:
                    alerts.append(Alert(
                        source="coingecko_prices",
                        alert_type="price_drop",
                        message=f"BTC down {abs(btc['usd_24h_change']):.1f}% in 24h",
                        severity="high",
                        data={"price": btc.get("usd"), "change": btc.get("usd_24h_change")},
                        timestamp=datetime.now(timezone.utc).isoformat()
                    ))

        # Check fear & greed
        if "fear_greed" in results and results["fear_greed"].success:
            fg_data = results["fear_greed"].data
            if isinstance(fg_data, list) and fg_data:
                value = int(fg_data[0].get("value", 50))
                classification = fg_data[0].get("value_classification", "")

                if value <= self.thresholds["fear_greed_extreme"]:
                    alerts.append(Alert(
                        source="fear_greed",
                        alert_type="extreme_fear",
                        message=f"Extreme Fear ({value}) - potential buy opportunity",
                        severity="high",
                        data={"value": value, "classification": classification},
                        timestamp=datetime.now(timezone.utc).isoformat()
                    ))
                elif value >= self.thresholds["fear_greed_greed"]:
                    alerts.append(Alert(
                        source="fear_greed",
                        alert_type="extreme_greed",
                        message=f"Extreme Greed ({value}) - caution advised",
                        severity="medium",
                        data={"value": value, "classification": classification},
                        timestamp=datetime.now(timezone.utc).isoformat()
                    ))

        # Store alerts
        with self._lock:
            self.alerts.extend(alerts)
            self.state.alerts_generated += len(alerts)

        # Send notifications for high severity
        for alert in alerts:
            if alert.severity in ["high", "critical"]:
                send_master_notification(
                    f"[{alert.alert_type.upper()}] {alert.message}",
                    priority="high" if alert.severity == "critical" else "normal"
                )

        return alerts

    def get_summary(self) -> Dict:
        """Get a summary of all current data."""
        results = self.fetch_all()

        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "crypto": {},
            "markets": [],
            "news": [],
            "sentiment": {},
            "alerts": [asdict(a) for a in self.alerts[-10:]]
        }

        # Crypto prices
        if results.get("coingecko_prices", {}).success:
            summary["crypto"] = results["coingecko_prices"].data

        # Polymarket
        if results.get("polymarket_active", {}).success:
            markets = results["polymarket_active"].data
            if isinstance(markets, list):
                summary["markets"] = [
                    {"question": m.get("question", "")[:80], "volume": m.get("volume")}
                    for m in markets[:5]
                ]

        # News
        if results.get("crypto_news", {}).success:
            news = results["crypto_news"].data
            if isinstance(news, list):
                summary["news"] = [
                    {"title": n.get("title", "")[:60], "source": n.get("source")}
                    for n in news[:5]
                ]

        # Fear & Greed
        if results.get("fear_greed", {}).success:
            fg = results["fear_greed"].data
            if isinstance(fg, list) and fg:
                summary["sentiment"]["fear_greed"] = {
                    "value": fg[0].get("value"),
                    "classification": fg[0].get("value_classification")
                }

        return summary

    def get_state(self) -> Dict:
        """Get agent state."""
        return asdict(self.state)

    def add_source(self, name: str, config: Dict):
        """Add a new data source."""
        self.sources[name] = config
        log_action("web_agent", "add_source", name)

    def run_daemon(self, interval: int = 300):
        """Run agent as daemon, fetching periodically."""
        log_action("web_agent", "daemon_start", f"interval={interval}")
        print(f"[WebAgent] Starting daemon (interval={interval}s)")

        while True:
            try:
                results = self.fetch_all()
                success = sum(1 for r in results.values() if r.success)
                print(f"[WebAgent] Fetched {success}/{len(results)} sources")

            except Exception as e:
                print(f"[WebAgent] Error: {e}")

            time.sleep(interval)


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_web_agent: Optional[WebAgent] = None


def get_web_agent() -> WebAgent:
    """Get or create the global web agent."""
    global _web_agent
    if _web_agent is None:
        _web_agent = WebAgent()
    return _web_agent


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Agentic Web Agent - Self-Hosted")
    parser.add_argument("command", choices=[
        "fetch", "summary", "status", "daemon", "alerts"
    ])
    parser.add_argument("--source", help="Specific source to fetch")
    parser.add_argument("--force", action="store_true", help="Force fetch (ignore cache)")
    parser.add_argument("--interval", type=int, default=300, help="Daemon interval")

    args = parser.parse_args()
    agent = get_web_agent()

    if args.command == "fetch":
        if args.source:
            result = agent.fetch_source(args.source, args.force)
            print(json.dumps(asdict(result), indent=2, default=str))
        else:
            results = agent.fetch_all(force=args.force)
            for source, result in results.items():
                status = "OK" if result.success else f"FAIL: {result.error}"
                cached = " (cached)" if result.cached else ""
                print(f"{source}: {status}{cached}")

    elif args.command == "summary":
        summary = agent.get_summary()
        print(json.dumps(summary, indent=2, default=str))

    elif args.command == "status":
        state = agent.get_state()
        print(f"\n=== Web Agent Status ===")
        print(f"Last run: {state['last_run']}")
        print(f"Total fetches: {state['total_fetches']}")
        print(f"Success rate: {state['successful_fetches']}/{state['total_fetches']}")
        print(f"Cache hits: {state['cache_hits']}")
        print(f"Alerts generated: {state['alerts_generated']}")
        print(f"\nSources:")
        for source, status in state['sources_status'].items():
            print(f"  {source}: {status.get('status', 'unknown')}")

    elif args.command == "alerts":
        for alert in agent.alerts:
            print(f"[{alert.severity.upper()}] {alert.message}")

    elif args.command == "daemon":
        agent.run_daemon(args.interval)


if __name__ == "__main__":
    main()
