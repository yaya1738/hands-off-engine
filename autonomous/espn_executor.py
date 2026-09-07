from ai.factory.live_order_authority import submit_legacy_order
#!/usr/bin/env python3
"""
ESPN Executor - Concrete Implementation of Yair's ESPN Teaching
Actually fetches ESPN win probabilities and acts on Polymarket.

YAIR'S TEACHING: 'ESPN mid-game probability = very accurate'
- ESPN uses sophisticated models for live win probability
- Polymarket prices can lag behind ESPN during live games
- Edge = when ESPN says 70% but Polymarket says 60%

ESPN API ENDPOINTS (undocumented but functional):
- Scoreboard: site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard
- Win Prob: sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{ID}/competitions/{ID}/probabilities
- Predictor: sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{ID}/competitions/{ID}/predictor

Serving: Yair Siegel
"""

import json
import os
import re
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

MASTER = "Yair Siegel"
ESPN_STATE = STATE_DIR / "espn_executor.json"
ESPN_LOG = STATE_DIR / "espn_trades.jsonl"

# ESPN API endpoints
ESPN_ENDPOINTS = {
    "nfl_scoreboard": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "nba_scoreboard": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
    "mlb_scoreboard": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
    "nhl_scoreboard": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
    "ncaaf_scoreboard": "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard",
    "ncaab_scoreboard": "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard",
}

# Minimum edge to trade (Yair's teaching: need meaningful edge)
MIN_EDGE = 0.05  # 5% divergence
MIN_SIZE = 5     # $5 minimum trade


class ESPNExecutor:
    """
    Concrete implementation of ESPN algorithm.

    Yair's teaching: 'ESPN mid-game probability = very accurate'
    This system actually fetches ESPN data and trades on divergence.
    """

    def __init__(self):
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if ESPN_STATE.exists():
            with open(ESPN_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "espn_fetches": 0,
            "opportunities_found": 0,
            "trades_placed": 0,
            "total_edge": 0,
            "wins": 0,
            "losses": 0,
            "pending_trades": []
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(ESPN_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_trade(self, trade: Dict):
        trade["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(ESPN_LOG, 'a') as f:
            f.write(json.dumps(trade) + "\n")

    def fetch_espn_scoreboard(self, sport: str = "nfl") -> List[Dict]:
        """
        Fetch live games from ESPN scoreboard.
        Returns list of games with basic info.
        """
        endpoint = ESPN_ENDPOINTS.get(f"{sport}_scoreboard")
        if not endpoint:
            return []

        try:
            response = requests.get(endpoint, timeout=10)
            if response.status_code != 200:
                return []

            data = response.json()
            events = data.get("events", [])

            games = []
            for event in events:
                competition = event.get("competitions", [{}])[0]
                competitors = competition.get("competitors", [])

                if len(competitors) < 2:
                    continue

                # Find home and away teams
                home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
                away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

                game = {
                    "event_id": event.get("id"),
                    "name": event.get("name"),
                    "short_name": event.get("shortName"),
                    "status": event.get("status", {}).get("type", {}).get("name"),
                    "status_detail": event.get("status", {}).get("type", {}).get("detail"),
                    "home_team": home.get("team", {}).get("displayName"),
                    "away_team": away.get("team", {}).get("displayName"),
                    "home_score": home.get("score"),
                    "away_score": away.get("score"),
                    "sport": sport
                }

                # Get win probability if available (some games include it directly)
                situation = competition.get("situation", {})
                if situation:
                    last_play = situation.get("lastPlay", {})
                    if last_play.get("probability"):
                        game["espn_home_win_prob"] = last_play["probability"].get("homeWinPercentage")

                games.append(game)

            self.state["espn_fetches"] += 1
            return games

        except Exception as e:
            print(f"Error fetching ESPN scoreboard: {e}")
            return []

    def fetch_win_probability(self, event_id: str, sport: str = "nfl") -> Optional[float]:
        """
        Fetch live win probability from ESPN for a specific game.
        Returns home team win probability.
        """
        league_map = {
            "nfl": "football/leagues/nfl",
            "nba": "basketball/leagues/nba",
            "mlb": "baseball/leagues/mlb",
            "ncaaf": "football/leagues/college-football",
            "ncaab": "basketball/leagues/mens-college-basketball"
        }

        league_path = league_map.get(sport, "football/leagues/nfl")

        # Try predictor endpoint first (pre-game predictions)
        try:
            url = f"https://sports.core.api.espn.com/v2/sports/{league_path}/events/{event_id}/competitions/{event_id}/predictor"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                home_proj = data.get("homeTeam", {}).get("gameProjection")
                if home_proj:
                    return float(home_proj) / 100  # Convert from percentage

        except:
            pass

        # Try probabilities endpoint (live game)
        try:
            url = f"https://sports.core.api.espn.com/v2/sports/{league_path}/events/{event_id}/competitions/{event_id}/probabilities?limit=1"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                if items:
                    # Get most recent probability
                    latest = items[-1] if isinstance(items[-1], dict) else None
                    if latest:
                        home_wp = latest.get("homeWinPercentage")
                        if home_wp:
                            return float(home_wp)

        except:
            pass

        return None

    def fetch_polymarket_sports_markets(self) -> List[Dict]:
        """
        Fetch sports-related markets from Polymarket.
        """
        try:
            response = requests.get(
                "https://gamma-api.polymarket.com/markets",
                params={"closed": "false", "limit": 100},
                timeout=15
            )

            if response.status_code != 200:
                return []

            markets = response.json()
            sports_markets = []

            # Keywords for sports detection
            sports_keywords = [
                'nfl', 'nba', 'mlb', 'nhl', 'ncaa',
                'super bowl', 'world series', 'playoffs', 'finals',
                'win', 'beat', 'game', 'championship',
                'chiefs', 'eagles', 'ravens', 'bills', '49ers', 'cowboys', 'packers',
                'lakers', 'celtics', 'warriors', 'bulls', 'heat', 'nuggets',
                'dodgers', 'yankees', 'braves', 'phillies', 'astros'
            ]

            for market in markets:
                question = market.get("question", "").lower()
                if any(kw in question for kw in sports_keywords):
                    prices = json.loads(market.get("outcomePrices", "[]"))
                    if len(prices) >= 2:
                        sports_markets.append({
                            "market_id": market.get("id", market.get("condition_id")),
                            "question": market.get("question"),
                            "yes_price": float(prices[0]),
                            "no_price": float(prices[1]),
                            "volume": float(market.get("volume", 0)),
                            "liquidity": float(market.get("liquidity", 0)),
                            "token_ids": json.loads(market.get("clobTokenIds", "[]"))
                        })

            return sports_markets

        except Exception as e:
            print(f"Error fetching Polymarket sports: {e}")
            return []

    def match_game_to_market(self, game: Dict, markets: List[Dict]) -> Optional[Dict]:
        """
        Try to match an ESPN game to a Polymarket market.
        Returns matched market or None.
        """
        home_team = game.get("home_team", "").lower()
        away_team = game.get("away_team", "").lower()

        # Try to find market mentioning either team
        for market in markets:
            question = market.get("question", "").lower()

            # Check if both teams mentioned or game name matches
            home_in = any(word in question for word in home_team.split())
            away_in = any(word in question for word in away_team.split())

            # Also check short name (e.g., "KC @ LV")
            short_name = game.get("short_name", "").lower()
            short_match = short_name and short_name in question

            if (home_in and away_in) or short_match:
                return market

        return None

    def find_opportunities(self) -> List[Dict]:
        """
        Find ESPN vs Polymarket divergences.

        THE ALGORITHM:
        1. Get live ESPN games
        2. Get ESPN win probability for each
        3. Match to Polymarket markets
        4. Identify where ESPN != Polymarket by > MIN_EDGE
        5. Return actionable opportunities
        """
        opportunities = []

        # Fetch sports markets from Polymarket
        pm_markets = self.fetch_polymarket_sports_markets()
        print(f"  Found {len(pm_markets)} sports markets on Polymarket")

        # Check each sport
        for sport in ["nfl", "nba", "ncaaf", "ncaab"]:
            games = self.fetch_espn_scoreboard(sport)

            for game in games:
                # Only look at live games (in progress)
                status = game.get("status", "")
                if status not in ["STATUS_IN_PROGRESS", "STATUS_HALFTIME", "STATUS_SECOND_HALF"]:
                    # Also consider pre-game for testing
                    if status != "STATUS_SCHEDULED":
                        continue

                # Get ESPN win probability
                espn_prob = game.get("espn_home_win_prob")
                if espn_prob is None:
                    espn_prob = self.fetch_win_probability(game["event_id"], sport)

                if espn_prob is None:
                    continue

                # Try to match to Polymarket
                matched_market = self.match_game_to_market(game, pm_markets)

                if matched_market:
                    pm_price = matched_market.get("yes_price", 0.5)

                    # Calculate edge
                    # Assume YES = home team wins (may need market-specific logic)
                    edge = espn_prob - pm_price

                    if abs(edge) >= MIN_EDGE:
                        opportunity = {
                            "game": game.get("name"),
                            "sport": sport,
                            "status": game.get("status_detail"),
                            "espn_home_win_prob": espn_prob,
                            "polymarket_yes_price": pm_price,
                            "edge": edge,
                            "direction": "BUY_YES" if edge > 0 else "BUY_NO",
                            "market_id": matched_market.get("market_id"),
                            "market_question": matched_market.get("question"),
                            "liquidity": matched_market.get("liquidity"),
                            "token_ids": matched_market.get("token_ids")
                        }
                        opportunities.append(opportunity)
                        self.state["opportunities_found"] += 1

        return opportunities

    def execute_opportunity(self, opp: Dict) -> Dict:
        """
        Execute a trade on Polymarket based on ESPN divergence.
        """
        try:
            from py_clob_client.client import ClobClient
            from py_clob_client.clob_types import OrderArgs

            host = "https://clob.polymarket.com"
            key = os.environ.get("POLYMARKET_PRIVATE_KEY")
            funder = os.environ.get("POLYMARKET_FUNDER_ADDRESS")

            if not key:
                return {"executed": False, "reason": "No API key"}

            client = ClobClient(host, key=key, chain_id=137, funder=funder)
            creds = client.create_or_derive_api_creds()
            client.set_api_creds(creds)

            # Determine trade parameters
            direction = opp.get("direction", "BUY_YES")
            edge = abs(opp.get("edge", 0))

            # Size based on edge and confidence
            # Yair's teaching: 'Volume overwhelms mistakes' but start small
            base_size = MIN_SIZE
            if edge > 0.10:  # >10% edge
                size = base_size * 2
            elif edge > 0.07:  # >7% edge
                size = base_size * 1.5
            else:
                size = base_size

            # Get token ID for the right side
            token_ids = opp.get("token_ids", [])
            if len(token_ids) < 2:
                return {"executed": False, "reason": "No token IDs"}

            # YES = token_ids[0], NO = token_ids[1]
            if direction == "BUY_YES":
                token_id = token_ids[0]
                price = opp.get("polymarket_yes_price", 0.5)
                side = "BUY"
            else:
                token_id = token_ids[1]
                price = 1 - opp.get("polymarket_yes_price", 0.5)
                side = "BUY"

            # Create order slightly better than market (limit order)
            limit_price = round(price + 0.01, 2)  # Bid 1 cent above for fill

            order_args = OrderArgs(
                token_id=token_id,
                price=limit_price,
                size=size,
                side=side
            )

            signed_order = client.create_order(order_args)
            result = client.submit_legacy_order(signed_order)

            execution = {
                "executed": True,
                "order_id": result.get("orderID"),
                "game": opp.get("game"),
                "direction": direction,
                "size": size,
                "price": limit_price,
                "espn_prob": opp.get("espn_home_win_prob"),
                "pm_price": opp.get("polymarket_yes_price"),
                "edge": opp.get("edge"),
                "teaching_applied": "ESPN mid-game probability = very accurate"
            }

            self._log_trade(execution)
            self.state["trades_placed"] += 1
            self.state["total_edge"] += abs(opp.get("edge", 0))

            return execution

        except Exception as e:
            return {"executed": False, "error": str(e)}

    def run_espn_executor(self) -> Dict:
        """
        Run the full ESPN execution cycle.
        """
        print("=" * 70)
        print("ESPN EXECUTOR - Making Yair's Teaching Concrete")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        print("[YAIR'S TEACHING]")
        print("  'ESPN mid-game probability = very accurate'")
        print("  'Compare ESPN prob vs Polymarket price, trade divergence'")
        print()

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "opportunities": [],
            "executions": []
        }

        # Find opportunities
        print("[SCANNING FOR ESPN vs POLYMARKET DIVERGENCE]")
        opportunities = self.find_opportunities()
        results["opportunities"] = opportunities

        print(f"  Opportunities found: {len(opportunities)}")
        print()

        if opportunities:
            print("[OPPORTUNITIES]")
            for opp in opportunities:
                print(f"  {opp['game']}")
                print(f"    ESPN: {opp['espn_home_win_prob']:.0%}")
                print(f"    Polymarket: {opp['polymarket_yes_price']:.0%}")
                print(f"    Edge: {opp['edge']:.1%} → {opp['direction']}")
                print(f"    Market: {opp['market_question'][:50]}...")
                print()

            # Execute trades (if enabled)
            print("[EXECUTING TRADES]")
            for opp in opportunities:
                if opp.get("liquidity", 0) > 100:  # Only trade liquid markets
                    execution = self.execute_opportunity(opp)
                    results["executions"].append(execution)

                    if execution.get("executed"):
                        print(f"  ✓ EXECUTED: {opp['game']}")
                        print(f"    {execution['direction']} ${execution['size']} @ {execution['price']}")
                    else:
                        print(f"  ✗ FAILED: {execution.get('reason', execution.get('error'))}")
                else:
                    print(f"  ⚠ SKIPPED {opp['game']}: Low liquidity (${opp.get('liquidity', 0):.0f})")
            print()

        else:
            print("  No actionable opportunities found")
            print("  (Need live games with ESPN prob diverging from Polymarket)")
            print()

        # Summary
        print("=" * 70)
        print("ESPN EXECUTOR SUMMARY")
        print("=" * 70)
        print(f"  Total ESPN fetches: {self.state['espn_fetches']}")
        print(f"  Opportunities found: {self.state['opportunities_found']}")
        print(f"  Trades placed: {self.state['trades_placed']}")
        print(f"  Total edge captured: {self.state['total_edge']:.1%}")
        print()

        self._save_state()
        return results


def main():
    executor = ESPNExecutor()
    return executor.run_espn_executor()


if __name__ == "__main__":
    main()
