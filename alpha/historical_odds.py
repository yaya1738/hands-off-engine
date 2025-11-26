#!/usr/bin/env python3
"""
Historical Odds Tracking for Polymarket

Tracks odds movement over time to:
- Identify trends and momentum
- Calculate odds velocity (rate of change)
- Detect sharp money movements
- Provide historical context for decision-making
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audit import get_audit_logger


@dataclass
class OddsSnapshot:
    """Single odds observation"""
    timestamp: str  # ISO 8601 UTC
    market_id: str
    best_bid: float
    last_price: float
    spread: float  # best_ask - best_bid


@dataclass
class OddsHistory:
    """Historical odds for a market"""
    market_id: str
    question: str
    snapshots: List[OddsSnapshot]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'market_id': self.market_id,
            'question': self.question,
            'snapshots': [asdict(s) for s in self.snapshots]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OddsHistory':
        """Create from dictionary"""
        snapshots = [
            OddsSnapshot(**s) for s in data.get('snapshots', [])
        ]
        return cls(
            market_id=data['market_id'],
            question=data['question'],
            snapshots=snapshots
        )


@dataclass
class OddsVelocity:
    """Odds velocity metrics"""
    market_id: str
    velocity_1h: Optional[float]  # Change per hour over last hour
    velocity_6h: Optional[float]  # Change per hour over last 6 hours
    velocity_24h: Optional[float]  # Change per hour over last 24 hours
    total_change_24h: Optional[float]  # Total change in last 24 hours
    is_sharp_move: bool  # Large sudden movement detected
    

class HistoricalOddsTracker:
    """
    Track and analyze historical odds movements.
    
    Features:
    - Store odds snapshots over time
    - Calculate odds velocity
    - Detect sharp money movements
    - Provide trend analysis
    """
    
    def __init__(
        self,
        history_dir: Optional[Path] = None,
        max_snapshots_per_market: int = 288,  # 24 hours at 5-min intervals
        sharp_move_threshold: float = 0.10,  # 10% move in short period
        component: str = "alpha.historical_odds"
    ):
        """
        Initialize historical odds tracker.
        
        Args:
            history_dir: Directory for history files (defaults to state/historical_odds/)
            max_snapshots_per_market: Maximum snapshots to keep per market
            sharp_move_threshold: Threshold for detecting sharp moves
            component: Component name for audit logging
        """
        self.history_dir = history_dir or Path(__file__).parent.parent / "state" / "historical_odds"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_snapshots = max_snapshots_per_market
        self.sharp_move_threshold = sharp_move_threshold
        
        self.audit = get_audit_logger(component=component)
    
    def _get_history_path(self, market_id: str) -> Path:
        """Get path to history file for a market"""
        # Sanitize market_id for filename
        safe_id = market_id.replace("/", "_").replace(":", "_")
        return self.history_dir / f"{safe_id}.json"
    
    def load_history(self, market_id: str) -> Optional[OddsHistory]:
        """
        Load historical odds for a market.
        
        Args:
            market_id: Market identifier
            
        Returns:
            OddsHistory if found, None otherwise
        """
        path = self._get_history_path(market_id)
        
        if not path.exists():
            return None
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            return OddsHistory.from_dict(data)
        except Exception as e:
            self.audit.log_error(
                error_type="history_load_error",
                error_message=str(e),
                context={"market_id": market_id}
            )
            return None
    
    def save_history(self, history: OddsHistory) -> None:
        """
        Save historical odds for a market.
        
        Args:
            history: OddsHistory to save
        """
        path = self._get_history_path(history.market_id)
        
        try:
            # Atomic write
            tmp_path = path.with_suffix('.tmp')
            with open(tmp_path, 'w') as f:
                json.dump(history.to_dict(), f, indent=2)
            tmp_path.replace(path)
            
        except Exception as e:
            self.audit.log_error(
                error_type="history_save_error",
                error_message=str(e),
                context={"market_id": history.market_id}
            )
    
    def add_snapshot(
        self,
        market_id: str,
        question: str,
        best_bid: float,
        last_price: float,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Add a new odds snapshot for a market.
        
        Args:
            market_id: Market identifier
            question: Market question
            best_bid: Best bid price
            last_price: Last trade price
            timestamp: Snapshot timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # Load existing history or create new
        history = self.load_history(market_id)
        if history is None:
            history = OddsHistory(
                market_id=market_id,
                question=question,
                snapshots=[]
            )
        
        # Create snapshot
        snapshot = OddsSnapshot(
            timestamp=timestamp.isoformat(),
            market_id=market_id,
            best_bid=best_bid,
            last_price=last_price,
            spread=0.0  # Placeholder - would need best_ask to calculate
        )
        
        # Add to history
        history.snapshots.append(snapshot)
        
        # Trim old snapshots
        if len(history.snapshots) > self.max_snapshots:
            history.snapshots = history.snapshots[-self.max_snapshots:]
        
        # Save
        self.save_history(history)
        
        self.audit.log(
            event_type="odds_snapshot",
            event_data={
                "market_id": market_id,
                "last_price": last_price,
                "best_bid": best_bid,
                "snapshot_count": len(history.snapshots)
            }
        )
    
    def calculate_velocity(self, market_id: str) -> Optional[OddsVelocity]:
        """
        Calculate odds velocity for a market.
        
        Args:
            market_id: Market identifier
            
        Returns:
            OddsVelocity metrics if enough history, None otherwise
        """
        history = self.load_history(market_id)
        if not history or len(history.snapshots) < 2:
            return None
        
        now = datetime.now(timezone.utc)
        
        # Get prices at different time points
        current_price = history.snapshots[-1].last_price
        
        def get_price_at(hours_ago: float) -> Optional[float]:
            """Get price from approximately N hours ago"""
            target_time = now - timedelta(hours=hours_ago)
            
            # Find closest snapshot to target time
            closest_snapshot = None
            min_diff = float('inf')
            
            for snapshot in history.snapshots:
                snap_time = datetime.fromisoformat(snapshot.timestamp)
                diff = abs((snap_time - target_time).total_seconds())
                
                if diff < min_diff:
                    min_diff = diff
                    closest_snapshot = snapshot
            
            # Only use if within reasonable window (e.g., 30 minutes)
            if closest_snapshot and min_diff < 1800:  # 30 minutes
                return closest_snapshot.last_price
            
            return None
        
        # Calculate velocities
        price_1h = get_price_at(1.0)
        price_6h = get_price_at(6.0)
        price_24h = get_price_at(24.0)
        
        velocity_1h = None
        if price_1h is not None:
            velocity_1h = (current_price - price_1h) / 1.0  # Change per hour
        
        velocity_6h = None
        if price_6h is not None:
            velocity_6h = (current_price - price_6h) / 6.0  # Change per hour
        
        velocity_24h = None
        total_change_24h = None
        if price_24h is not None:
            velocity_24h = (current_price - price_24h) / 24.0  # Change per hour
            total_change_24h = current_price - price_24h
        
        # Detect sharp moves
        # A sharp move is when 1h velocity is much higher than 6h velocity
        is_sharp = False
        if velocity_1h is not None and velocity_6h is not None:
            if abs(velocity_1h) > self.sharp_move_threshold:
                # Strong recent movement
                if abs(velocity_1h) > abs(velocity_6h) * 2:
                    # Recent movement is at least 2x the longer-term trend
                    is_sharp = True
        
        velocity = OddsVelocity(
            market_id=market_id,
            velocity_1h=velocity_1h,
            velocity_6h=velocity_6h,
            velocity_24h=velocity_24h,
            total_change_24h=total_change_24h,
            is_sharp_move=is_sharp
        )
        
        if is_sharp:
            self.audit.log(
                event_type="sharp_move_detected",
                event_data={
                    "market_id": market_id,
                    "velocity_1h": velocity_1h,
                    "velocity_6h": velocity_6h,
                    "current_price": current_price
                },
                severity="warning"
            )
        
        return velocity
    
    def batch_update_from_data(self, data: Dict[str, Any]) -> int:
        """
        Batch update odds snapshots from polymarket data.
        
        Args:
            data: Polymarket data dict (from polymarket-compact.json)
            
        Returns:
            Number of markets updated
        """
        updated_count = 0
        
        # Parse timestamp
        timestamp_str = data.get('timestamp')
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now(timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)
        
        # Process each market
        markets_by_query = data.get('markets', {})
        for query, markets in markets_by_query.items():
            for market in markets:
                market_id = market.get('slug', '')
                question = market.get('question', '')
                best_bid = market.get('bestBid', 0.5)
                last_price = market.get('last', 0.5)
                
                if market_id:
                    self.add_snapshot(
                        market_id=market_id,
                        question=question,
                        best_bid=best_bid,
                        last_price=last_price,
                        timestamp=timestamp
                    )
                    updated_count += 1
        
        self.audit.log(
            event_type="batch_update",
            event_data={
                "markets_updated": updated_count,
                "timestamp": timestamp.isoformat()
            }
        )
        
        return updated_count
    
    def get_trending_markets(
        self,
        min_velocity: float = 0.05,
        max_results: int = 10
    ) -> List[Tuple[str, OddsVelocity]]:
        """
        Get markets with significant odds movement.
        
        Args:
            min_velocity: Minimum 1h velocity to include
            max_results: Maximum number of results
            
        Returns:
            List of (market_id, velocity) tuples sorted by velocity
        """
        trending = []
        
        # Check all markets with history
        for history_file in self.history_dir.glob("*.json"):
            if history_file.stem.startswith("cache_"):
                continue  # Skip cache files
            
            market_id = history_file.stem.replace("_", "/")
            velocity = self.calculate_velocity(market_id)
            
            if velocity and velocity.velocity_1h is not None:
                if abs(velocity.velocity_1h) >= min_velocity:
                    trending.append((market_id, velocity))
        
        # Sort by absolute velocity (highest movement first)
        trending.sort(
            key=lambda x: abs(x[1].velocity_1h) if x[1].velocity_1h else 0,
            reverse=True
        )
        
        return trending[:max_results]


# Convenience function
def get_odds_tracker() -> HistoricalOddsTracker:
    """Get a configured historical odds tracker instance"""
    return HistoricalOddsTracker()


if __name__ == "__main__":
    # Test the historical odds tracker
    from alpha.data_fetcher import get_data_fetcher
    
    print("Testing historical odds tracker...")
    
    # Get data
    repo_root = Path(__file__).parent.parent
    source = repo_root / 'termux-hands-off' / 'out' / 'polymarket-compact.json'
    
    if not source.exists():
        print(f"Error: Source file not found: {source}", file=sys.stderr)
        sys.exit(1)
    
    fetcher = get_data_fetcher()
    data = fetcher.fetch_with_retry(source, use_cache=False)
    
    # Create tracker
    tracker = HistoricalOddsTracker()
    
    # Test batch update
    print("\n1. Batch updating from current data...")
    count = tracker.batch_update_from_data(data)
    print(f"   ✓ Updated {count} markets")
    
    # Test velocity calculation
    print("\n2. Calculating velocity for first market...")
    markets = data.get('markets', {})
    if markets:
        first_query = list(markets.keys())[0]
        first_market = markets[first_query][0]
        market_id = first_market.get('slug', '')
        
        if market_id:
            velocity = tracker.calculate_velocity(market_id)
            if velocity:
                print(f"   Market: {market_id}")
                print(f"   1h velocity: {velocity.velocity_1h}")
                print(f"   Sharp move: {velocity.is_sharp_move}")
            else:
                print("   ⊘ Not enough history for velocity calculation")
    
    # Test trending markets
    print("\n3. Getting trending markets...")
    trending = tracker.get_trending_markets(min_velocity=0.0, max_results=5)
    if trending:
        print(f"   Found {len(trending)} markets with movement")
        for market_id, vel in trending[:3]:
            print(f"   - {market_id}: {vel.velocity_1h:.4f}/h")
    else:
        print("   ⊘ No trending markets (need more history)")
    
    print("\n✓ Historical odds tracker tests complete!")
