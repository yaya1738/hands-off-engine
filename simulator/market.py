"""
Market Simulator for Hands-Off Engine

Simulates market price movements for backtesting:
- Replay historical odds data
- Generate synthetic market scenarios
- Support multiple markets simultaneously
"""

import json
import random
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger


@dataclass
class MarketSnapshot:
    """Single point-in-time snapshot of a market"""
    timestamp: datetime
    market_id: str
    market_name: str
    yes_price: float  # Price for YES outcome (0.0 to 1.0)
    no_price: float  # Price for NO outcome (0.0 to 1.0)
    volume: float = 0.0
    liquidity: float = 0.0


@dataclass
class Market:
    """Market definition for simulation"""
    market_id: str
    market_name: str
    initial_yes_price: float
    volatility: float = 0.02  # Daily volatility
    drift: float = 0.0  # Directional bias


class MarketSimulator:
    """
    Simulates market price movements for backtesting.
    
    Can replay historical data or generate synthetic scenarios.
    """
    
    def __init__(self, historical_data_dir: Optional[Path] = None):
        """
        Initialize market simulator.
        
        Args:
            historical_data_dir: Directory containing historical market data files
        """
        self.historical_data_dir = historical_data_dir or Path("data/historical")
        self.audit = get_audit_logger(component="simulator.market")
        self._markets: Dict[str, List[MarketSnapshot]] = {}
        self._current_time: Optional[datetime] = None
        
    def load_historical_data(self, market_id: str) -> bool:
        """
        Load historical market data from file.
        
        Args:
            market_id: ID of market to load
            
        Returns:
            True if data was loaded successfully
        """
        data_file = self.historical_data_dir / f"{market_id}.json"
        
        if not data_file.exists():
            self.audit.log_error(
                error_type="data_load_failed",
                error_message=f"Historical data file not found: {data_file}"
            )
            return False
            
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
                
            snapshots = []
            for entry in data.get('snapshots', []):
                snapshot = MarketSnapshot(
                    timestamp=datetime.fromisoformat(entry['timestamp']),
                    market_id=entry['market_id'],
                    market_name=entry['market_name'],
                    yes_price=entry['yes_price'],
                    no_price=entry['no_price'],
                    volume=entry.get('volume', 0.0),
                    liquidity=entry.get('liquidity', 0.0)
                )
                snapshots.append(snapshot)
                
            self._markets[market_id] = sorted(snapshots, key=lambda s: s.timestamp)
            
            self.audit.log_data_fetch(
                source="historical_file",
                params={"market_id": market_id, "file": str(data_file)},
                success=True,
                record_count=len(snapshots)
            )
            
            return True
            
        except Exception as e:
            self.audit.log_error(
                error_type="data_load_error",
                error_message=str(e),
                context={"market_id": market_id, "file": str(data_file)}
            )
            return False
    
    def generate_synthetic_data(
        self,
        market: Market,
        start_date: datetime,
        end_date: datetime,
        interval_hours: int = 1
    ) -> List[MarketSnapshot]:
        """
        Generate synthetic market price data using random walk.
        
        Args:
            market: Market definition
            start_date: Start date for simulation
            end_date: End date for simulation
            interval_hours: Hours between snapshots
            
        Returns:
            List of market snapshots
        """
        snapshots = []
        current_time = start_date
        current_price = market.initial_yes_price
        
        while current_time <= end_date:
            # Random walk with drift and volatility
            # Price moves are scaled by sqrt(interval_hours) for proper time scaling
            time_factor = (interval_hours / 24.0) ** 0.5
            price_change = (
                market.drift * (interval_hours / 24.0) +  # Drift component
                market.volatility * time_factor * random.gauss(0, 1)  # Random component
            )
            
            current_price = max(0.01, min(0.99, current_price + price_change))
            
            snapshot = MarketSnapshot(
                timestamp=current_time,
                market_id=market.market_id,
                market_name=market.market_name,
                yes_price=current_price,
                no_price=1.0 - current_price,
                volume=random.uniform(1000, 10000),
                liquidity=random.uniform(10000, 100000)
            )
            snapshots.append(snapshot)
            
            current_time += timedelta(hours=interval_hours)
        
        self._markets[market.market_id] = snapshots
        
        self.audit.log_action(
            action_type="generate_synthetic_data",
            action_data={
                "market_id": market.market_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "snapshots": len(snapshots)
            },
            result="completed"
        )
        
        return snapshots
    
    def get_market_at_time(
        self,
        market_id: str,
        timestamp: datetime
    ) -> Optional[MarketSnapshot]:
        """
        Get market snapshot at or just before a specific time.
        
        Args:
            market_id: ID of market
            timestamp: Time to query
            
        Returns:
            MarketSnapshot if available, None otherwise
        """
        if market_id not in self._markets:
            return None
            
        snapshots = self._markets[market_id]
        
        # Binary search for the snapshot at or before timestamp
        left, right = 0, len(snapshots) - 1
        result = None
        
        while left <= right:
            mid = (left + right) // 2
            if snapshots[mid].timestamp <= timestamp:
                result = snapshots[mid]
                left = mid + 1
            else:
                right = mid - 1
                
        return result
    
    def get_all_markets_at_time(
        self,
        timestamp: datetime
    ) -> Dict[str, MarketSnapshot]:
        """
        Get snapshots of all loaded markets at a specific time.
        
        Args:
            timestamp: Time to query
            
        Returns:
            Dict mapping market_id to MarketSnapshot
        """
        result = {}
        for market_id in self._markets:
            snapshot = self.get_market_at_time(market_id, timestamp)
            if snapshot:
                result[market_id] = snapshot
        return result
    
    def get_time_range(self, market_id: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Get the time range of available data for a market.
        
        Args:
            market_id: ID of market
            
        Returns:
            Tuple of (start_time, end_time) or None if market not found
        """
        if market_id not in self._markets or not self._markets[market_id]:
            return None
            
        snapshots = self._markets[market_id]
        return (snapshots[0].timestamp, snapshots[-1].timestamp)
    
    def get_common_time_range(self) -> Optional[Tuple[datetime, datetime]]:
        """
        Get the time range common to all loaded markets.
        
        Returns:
            Tuple of (start_time, end_time) or None if no markets loaded
        """
        if not self._markets:
            return None
            
        start_times = []
        end_times = []
        
        for market_id in self._markets:
            time_range = self.get_time_range(market_id)
            if time_range:
                start_times.append(time_range[0])
                end_times.append(time_range[1])
        
        if not start_times:
            return None
            
        return (max(start_times), min(end_times))
    
    def save_synthetic_data(
        self,
        market_id: str,
        output_file: Optional[Path] = None
    ) -> bool:
        """
        Save generated synthetic data to file.
        
        Args:
            market_id: ID of market to save
            output_file: Output file path (defaults to historical_data_dir)
            
        Returns:
            True if saved successfully
        """
        if market_id not in self._markets:
            return False
            
        if output_file is None:
            output_file = self.historical_data_dir / f"{market_id}.json"
            
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            snapshots = self._markets[market_id]
            data = {
                "market_id": market_id,
                "market_name": snapshots[0].market_name if snapshots else "",
                "snapshots": [
                    {
                        "timestamp": s.timestamp.isoformat(),
                        "market_id": s.market_id,
                        "market_name": s.market_name,
                        "yes_price": s.yes_price,
                        "no_price": s.no_price,
                        "volume": s.volume,
                        "liquidity": s.liquidity
                    }
                    for s in snapshots
                ]
            }
            
            # Atomic write
            temp_file = output_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            temp_file.replace(output_file)
            
            self.audit.log_action(
                action_type="save_synthetic_data",
                action_data={
                    "market_id": market_id,
                    "output_file": str(output_file),
                    "snapshots": len(snapshots)
                },
                result="completed"
            )
            
            return True
            
        except Exception as e:
            self.audit.log_error(
                error_type="save_data_error",
                error_message=str(e),
                context={"market_id": market_id, "output_file": str(output_file)}
            )
            return False


if __name__ == "__main__":
    # Example usage
    print("Market Simulator Example\n" + "=" * 50)
    
    simulator = MarketSimulator()
    
    # Create a synthetic market
    market = Market(
        market_id="btc_100k_eoy",
        market_name="Will BTC reach $100k by EOY?",
        initial_yes_price=0.40,
        volatility=0.05,
        drift=0.01
    )
    
    # Generate 30 days of hourly data
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 1, 30, tzinfo=timezone.utc)
    
    snapshots = simulator.generate_synthetic_data(market, start, end, interval_hours=1)
    print(f"Generated {len(snapshots)} snapshots for {market.market_name}")
    
    # Query specific time
    query_time = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
    snapshot = simulator.get_market_at_time(market.market_id, query_time)
    
    if snapshot:
        print(f"\nMarket at {query_time}:")
        print(f"  YES price: {snapshot.yes_price:.3f}")
        print(f"  NO price: {snapshot.no_price:.3f}")
    
    # Save the synthetic data
    simulator.save_synthetic_data(market.market_id)
    print(f"\nSaved synthetic data to: {simulator.historical_data_dir / market.market_id}.json")
