#!/usr/bin/env python3
"""
ESPN Live Game Alpha: Destroy Polymarket During Live Games
==========================================================

This module provides real-time sports alpha by comparing:
1. Live game state from ESPN (scores, time remaining, momentum)
2. Current Polymarket odds on the game

When the live situation diverges from market prices, we have edge.
The key is SPEED - acting before the market catches up.

Example scenarios:
- Team down 10 at halftime but market hasn't adjusted enough
- Star player injured mid-game
- Momentum shift (scoring run) not yet reflected in odds
- Late game scenarios where math favors one side

Philosophy: "ESPN algo destroys Polymarket during live games"
"""

import json
import sys
import os
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Tuple
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


class Sport(Enum):
    """Supported sports"""
    NBA = "nba"
    NFL = "nfl"
    MLB = "mlb"
    NHL = "nhl"
    NCAAB = "ncaab"     # College basketball
    NCAAF = "ncaaf"     # College football
    SOCCER = "soccer"


class GamePhase(Enum):
    """Game phase for context"""
    PREGAME = "pregame"
    EARLY = "early"             # First quarter/period
    MIDDLE = "middle"           # Mid-game
    LATE = "late"               # 4th quarter, 9th inning, etc.
    OVERTIME = "overtime"
    FINAL = "final"


@dataclass
class LiveGameState:
    """Current state of a live game from ESPN"""
    game_id: str
    sport: Sport
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    phase: GamePhase
    time_remaining: str         # "5:32 4th Q" format
    seconds_remaining: int      # Computed seconds
    possession: Optional[str]   # Which team has possession
    momentum_score: float       # -1 to 1 (away to home)
    injuries: List[str]         # Recent injury updates
    last_updated: str           # ISO timestamp


@dataclass
class PolymarketGameOdds:
    """Polymarket odds for a game"""
    market_id: str
    game_description: str
    home_win_price: float
    away_win_price: float
    last_updated: str


class ESPNClient:
    """
    ESPN API client for fetching live game data.

    Note: This uses ESPN's public endpoints. For production,
    consider ESPN's official API or alternative data providers.
    """

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"

    SPORT_ENDPOINTS = {
        Sport.NBA: "basketball/nba",
        Sport.NFL: "football/nfl",
        Sport.MLB: "baseball/mlb",
        Sport.NHL: "hockey/nhl",
        Sport.NCAAB: "basketball/mens-college-basketball",
        Sport.NCAAF: "football/college-football",
        Sport.SOCCER: "soccer/eng.1"  # Premier League default
    }

    def __init__(self):
        self.cache = {}
        self.cache_ttl = 30  # Refresh every 30 seconds for live games

    def get_live_games(self, sport: Sport) -> List[LiveGameState]:
        """
        Fetch all live games for a sport.

        Returns:
            List of LiveGameState objects for games currently in progress
        """
        # For now, return simulated data
        # In production: requests.get(f"{self.BASE_URL}/{self.SPORT_ENDPOINTS[sport]}/scoreboard")
        return self._fetch_live_games(sport)

    def _fetch_live_games(self, sport: Sport) -> List[LiveGameState]:
        """
        Actual ESPN API call (simulated for now).
        Replace with real HTTP requests in production.
        """
        # Placeholder - in production this hits ESPN API
        # Example endpoint: https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard

        # For demonstration, return empty list
        # The real implementation would parse ESPN JSON response
        return []

    def parse_espn_game(self, raw_data: Dict, sport: Sport) -> LiveGameState:
        """Parse ESPN API response into LiveGameState"""
        # This would parse the actual ESPN JSON structure
        # Example fields from ESPN API:
        # - competitions[0].competitors (home/away teams)
        # - competitions[0].status.displayClock
        # - competitions[0].status.period
        # - competitions[0].situation (for NFL)

        # Placeholder implementation
        return LiveGameState(
            game_id=raw_data.get('id', ''),
            sport=sport,
            home_team=raw_data.get('home_team', 'Home'),
            away_team=raw_data.get('away_team', 'Away'),
            home_score=raw_data.get('home_score', 0),
            away_score=raw_data.get('away_score', 0),
            phase=GamePhase.MIDDLE,
            time_remaining="0:00",
            seconds_remaining=0,
            possession=None,
            momentum_score=0.0,
            injuries=[],
            last_updated=datetime.now(timezone.utc).isoformat()
        )


class LiveGameAlphaModel:
    """
    Alpha model that compares live game state to market odds.

    This is where the "destruction" happens - finding when
    Polymarket odds lag behind reality.
    """

    def __init__(self):
        # Win probability lookup tables by sport
        # These are simplified - real models use much more data
        self.base_win_curves = {
            Sport.NBA: self._nba_win_probability,
            Sport.NFL: self._nfl_win_probability,
            Sport.MLB: self._mlb_win_probability,
        }

    def calculate_fair_price(
        self,
        game: LiveGameState,
        side: str  # "home" or "away"
    ) -> Tuple[float, float]:
        """
        Calculate fair win probability based on live game state.

        Returns:
            Tuple of (fair_price, confidence)
        """
        sport = game.sport
        calculator = self.base_win_curves.get(sport, self._default_win_probability)

        score_diff = game.home_score - game.away_score
        if side == "away":
            score_diff = -score_diff

        fair_price, confidence = calculator(
            score_diff=score_diff,
            seconds_remaining=game.seconds_remaining,
            phase=game.phase,
            momentum=game.momentum_score if side == "home" else -game.momentum_score
        )

        return fair_price, confidence

    def _nba_win_probability(
        self,
        score_diff: int,
        seconds_remaining: int,
        phase: GamePhase,
        momentum: float
    ) -> Tuple[float, float]:
        """
        NBA win probability model.

        Based on historical data:
        - NBA teams average ~1 point per 24 seconds of possession
        - Comeback probability decreases exponentially in final minutes
        """
        # Total game time = 48 minutes = 2880 seconds
        total_time = 2880
        time_fraction = max(0, seconds_remaining / total_time)

        # Points needed to tie
        points_needed = abs(score_diff)

        # Expected points remaining (both teams combined avg 2 pts/24 sec)
        expected_points = (seconds_remaining / 24) * 2

        # Base probability from lead
        if score_diff == 0:
            base_prob = 0.5
        elif points_needed > expected_points * 1.5:
            # Very unlikely comeback
            base_prob = 0.95 if score_diff > 0 else 0.05
        else:
            # Logistic curve based on lead relative to time
            lead_factor = score_diff / max(1, expected_points / 2)
            base_prob = 1 / (1 + pow(10, -lead_factor / 4))

        # Adjust for game phase
        if phase == GamePhase.LATE and seconds_remaining < 120:
            # Final 2 minutes - leads are more valuable
            confidence = 0.9
            if score_diff > 6:
                base_prob = min(0.98, base_prob * 1.1)
        elif phase == GamePhase.OVERTIME:
            confidence = 0.85
        else:
            confidence = 0.75

        # Momentum adjustment (small factor)
        base_prob = base_prob + (momentum * 0.05)
        base_prob = max(0.02, min(0.98, base_prob))

        return base_prob, confidence

    def _nfl_win_probability(
        self,
        score_diff: int,
        seconds_remaining: int,
        phase: GamePhase,
        momentum: float
    ) -> Tuple[float, float]:
        """
        NFL win probability model.

        NFL is more volatile - big plays can shift games quickly.
        """
        total_time = 3600  # 60 minutes
        time_fraction = max(0, seconds_remaining / total_time)

        # NFL scoring is chunkier (7 points TD, 3 points FG)
        if score_diff == 0:
            base_prob = 0.5
        else:
            possessions_remaining = seconds_remaining / 120  # ~2 min per possession
            scores_possible = possessions_remaining * 0.3  # ~30% scoring rate

            if abs(score_diff) > scores_possible * 7:
                base_prob = 0.95 if score_diff > 0 else 0.05
            else:
                lead_factor = score_diff / 7  # Normalize by TD value
                base_prob = 1 / (1 + pow(10, -lead_factor / (1 + time_fraction * 3)))

        # Late game adjustments
        if phase == GamePhase.LATE and seconds_remaining < 120:
            confidence = 0.85
        else:
            confidence = 0.70

        base_prob = max(0.02, min(0.98, base_prob))
        return base_prob, confidence

    def _mlb_win_probability(
        self,
        score_diff: int,
        seconds_remaining: int,
        phase: GamePhase,
        momentum: float
    ) -> Tuple[float, float]:
        """
        MLB win probability model.

        Baseball uses outs remaining instead of time.
        seconds_remaining approximates outs * 30 seconds per out.
        """
        outs_remaining = seconds_remaining / 30  # Rough approximation

        if score_diff == 0:
            base_prob = 0.5
        elif phase == GamePhase.LATE and outs_remaining < 3:
            # 9th inning, fewer than 3 outs
            base_prob = 0.90 if score_diff > 0 else 0.10
        else:
            # Runs per out remaining (MLB avg ~0.15 runs per out)
            expected_runs = outs_remaining * 0.15
            if abs(score_diff) > expected_runs * 3:
                base_prob = 0.92 if score_diff > 0 else 0.08
            else:
                lead_factor = score_diff / max(1, expected_runs)
                base_prob = 1 / (1 + pow(10, -lead_factor / 3))

        confidence = 0.72
        base_prob = max(0.02, min(0.98, base_prob))
        return base_prob, confidence

    def _default_win_probability(
        self,
        score_diff: int,
        seconds_remaining: int,
        phase: GamePhase,
        momentum: float
    ) -> Tuple[float, float]:
        """Fallback probability model"""
        if score_diff == 0:
            return 0.5, 0.5

        # Simple logistic
        base_prob = 1 / (1 + pow(10, -score_diff / 10))
        return max(0.05, min(0.95, base_prob)), 0.5


class ESPNLiveAlphaAdapter(AlphaSourceAdapter):
    """
    Adapter that connects ESPN live data to the Integrations Hub.

    This is the "ESPN algo that destroys Polymarket during live games"
    """

    def __init__(
        self,
        polymarket_matcher: 'PolymarketMatcher' = None,
        sports: List[Sport] = None
    ):
        self.espn_client = ESPNClient()
        self.alpha_model = LiveGameAlphaModel()
        self.polymarket_matcher = polymarket_matcher or PolymarketMatcher()
        self.active_sports = sports or [Sport.NBA, Sport.NFL, Sport.MLB]

        # Minimum edge to generate signal
        self.min_edge = 0.05  # 5%

    @property
    def source_type(self) -> SignalSource:
        return SignalSource.ESPN_LIVE

    def is_available(self) -> bool:
        """Check if ESPN data is accessible"""
        # In production: actually ping ESPN API
        return True

    def fetch_signals(self) -> List[UnifiedAlphaSignal]:
        """
        Fetch live games, compare to Polymarket, generate signals.
        """
        signals = []

        for sport in self.active_sports:
            live_games = self.espn_client.get_live_games(sport)

            for game in live_games:
                game_signals = self._analyze_game(game)
                signals.extend(game_signals)

        return signals

    def _analyze_game(self, game: LiveGameState) -> List[UnifiedAlphaSignal]:
        """
        Analyze a single live game for alpha opportunities.
        """
        signals = []

        # Find matching Polymarket market
        market = self.polymarket_matcher.find_game_market(game)
        if not market:
            return []

        # Calculate fair prices
        home_fair, home_conf = self.alpha_model.calculate_fair_price(game, "home")
        away_fair, away_conf = self.alpha_model.calculate_fair_price(game, "away")

        # Check home team edge
        home_edge = home_fair - market.home_win_price
        if abs(home_edge) >= self.min_edge:
            side = "YES" if home_edge > 0 else "NO"
            signal = create_signal(
                market_id=market.market_id,
                market_name=f"{game.away_team} @ {game.home_team} - {game.home_team} Win",
                source=SignalSource.ESPN_LIVE,
                side=side,
                fair_price=home_fair,
                market_price=market.home_win_price,
                confidence=home_conf,
                urgency=SignalUrgency.IMMEDIATE,
                category="sports",
                reasoning=self._build_reasoning(game, "home", home_fair, market.home_win_price),
                raw_data={
                    'game': {
                        'home_team': game.home_team,
                        'away_team': game.away_team,
                        'score': f"{game.away_score}-{game.home_score}",
                        'time': game.time_remaining,
                        'phase': game.phase.value
                    },
                    'model_price': home_fair,
                    'market_price': market.home_win_price
                }
            )
            signals.append(signal)

        # Check away team edge (similar logic)
        away_edge = away_fair - market.away_win_price
        if abs(away_edge) >= self.min_edge:
            side = "YES" if away_edge > 0 else "NO"
            signal = create_signal(
                market_id=market.market_id + "_away",
                market_name=f"{game.away_team} @ {game.home_team} - {game.away_team} Win",
                source=SignalSource.ESPN_LIVE,
                side=side,
                fair_price=away_fair,
                market_price=market.away_win_price,
                confidence=away_conf,
                urgency=SignalUrgency.IMMEDIATE,
                category="sports",
                reasoning=self._build_reasoning(game, "away", away_fair, market.away_win_price),
                raw_data={
                    'game': {
                        'home_team': game.home_team,
                        'away_team': game.away_team,
                        'score': f"{game.away_score}-{game.home_score}",
                        'time': game.time_remaining,
                        'phase': game.phase.value
                    },
                    'model_price': away_fair,
                    'market_price': market.away_win_price
                }
            )
            signals.append(signal)

        return signals

    def _build_reasoning(
        self,
        game: LiveGameState,
        side: str,
        fair_price: float,
        market_price: float
    ) -> str:
        """Build human-readable reasoning for the signal"""
        team = game.home_team if side == "home" else game.away_team
        score = f"{game.away_score}-{game.home_score}"
        edge = abs(fair_price - market_price)

        return (
            f"ESPN LIVE: {team} currently {score} with {game.time_remaining} remaining. "
            f"Model estimates {fair_price:.1%} win prob vs market {market_price:.1%} "
            f"({edge:.1%} edge). Phase: {game.phase.value}"
        )


class PolymarketMatcher:
    """
    Matches ESPN games to Polymarket markets.

    This is critical - we need to find the right Polymarket market
    for each live game.
    """

    def __init__(self, markets_path: Path = None):
        self.markets_path = markets_path
        self.cached_markets: Dict[str, PolymarketGameOdds] = {}

    def load_markets(self, markets_data: List[Dict]):
        """Load Polymarket sports markets"""
        for market in markets_data:
            if self._is_sports_market(market):
                odds = self._parse_market(market)
                if odds:
                    self.cached_markets[odds.game_description.lower()] = odds

    def _is_sports_market(self, market: Dict) -> bool:
        """Check if market is a sports outcome market"""
        keywords = ['win', 'beat', 'vs', 'game', 'match', 'championship']
        question = market.get('question', '').lower()
        return any(kw in question for kw in keywords)

    def _parse_market(self, market: Dict) -> Optional[PolymarketGameOdds]:
        """Parse market data into PolymarketGameOdds"""
        # This would parse the actual Polymarket market structure
        return None

    def find_game_market(self, game: LiveGameState) -> Optional[PolymarketGameOdds]:
        """
        Find the Polymarket market for a given ESPN game.

        Uses fuzzy matching on team names.
        """
        search_terms = [
            f"{game.home_team}".lower(),
            f"{game.away_team}".lower(),
            f"{game.away_team} vs {game.home_team}".lower(),
            f"{game.away_team} @ {game.home_team}".lower()
        ]

        for term in search_terms:
            for desc, market in self.cached_markets.items():
                if term in desc:
                    return market

        return None


# ============================================================================
# Real-time monitoring loop
# ============================================================================

class LiveGameMonitor:
    """
    Continuous monitoring loop for live games.

    This runs in a separate process/thread and pushes
    signals to the execution queue as they're detected.
    """

    def __init__(
        self,
        adapter: ESPNLiveAlphaAdapter,
        poll_interval: int = 30,  # seconds
        signal_callback=None
    ):
        self.adapter = adapter
        self.poll_interval = poll_interval
        self.signal_callback = signal_callback
        self.running = False

    def start(self):
        """Start the monitoring loop"""
        self.running = True
        print(f"[LiveGameMonitor] Starting with {self.poll_interval}s interval")

        while self.running:
            try:
                signals = self.adapter.fetch_signals()

                if signals:
                    print(f"[LiveGameMonitor] Found {len(signals)} live signals!")
                    for sig in signals:
                        print(f"  -> {sig.market_name[:40]}... | {sig.edge:.1%} edge | {sig.urgency.value}")

                    if self.signal_callback:
                        self.signal_callback(signals)

                time.sleep(self.poll_interval)

            except KeyboardInterrupt:
                print("\n[LiveGameMonitor] Stopping...")
                self.running = False
            except Exception as e:
                print(f"[LiveGameMonitor] Error: {e}")
                time.sleep(self.poll_interval)

    def stop(self):
        """Stop the monitoring loop"""
        self.running = False


# ============================================================================
# Main entry point
# ============================================================================

def main():
    """Demo the ESPN Live Alpha system"""
    print("ESPN Live Game Alpha Module")
    print("=" * 50)
    print("\nThis module provides real-time sports alpha by:")
    print("1. Fetching live game data from ESPN")
    print("2. Calculating fair win probabilities")
    print("3. Comparing to Polymarket odds")
    print("4. Generating IMMEDIATE urgency signals")
    print("\n'ESPN algo destroys Polymarket during live games'")
    print("=" * 50)

    # Demo the alpha model
    model = LiveGameAlphaModel()

    print("\nNBA Win Probability Examples:")
    scenarios = [
        ("Home +10, 5 min left", 10, 300, GamePhase.LATE),
        ("Tied, halftime", 0, 1440, GamePhase.MIDDLE),
        ("Home -5, 1 min left", -5, 60, GamePhase.LATE),
        ("Home +3, overtime", 3, 180, GamePhase.OVERTIME),
    ]

    for desc, diff, secs, phase in scenarios:
        prob, conf = model._nba_win_probability(diff, secs, phase, 0)
        print(f"  {desc}: {prob:.1%} (confidence: {conf:.0%})")


if __name__ == '__main__':
    main()
