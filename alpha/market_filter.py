#!/usr/bin/env python3
"""
Market Filter for Polymarket

Filters markets based on:
- Liquidity requirements
- Time to resolution
- Market type (binary only for V1)
- Exclusion list for problematic markets
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audit import get_audit_logger


@dataclass
class FilterCriteria:
    """Criteria for filtering markets"""
    min_liquidity: float = 10000.0  # Min $10k volume
    max_days_to_resolution: Optional[int] = None  # None = no limit
    min_days_to_resolution: int = 1  # At least 1 day
    only_binary: bool = True  # Only binary markets
    min_price: float = 0.05  # Avoid near-certain markets
    max_price: float = 0.95  # Avoid near-certain markets
    exclude_keywords: List[str] = None  # Keywords to exclude from questions
    
    def __post_init__(self):
        if self.exclude_keywords is None:
            self.exclude_keywords = []


@dataclass
class FilterResult:
    """Result of filtering a market"""
    passed: bool
    reason: Optional[str] = None  # Reason for rejection


class MarketFilter:
    """
    Filter markets based on various criteria.
    
    Features:
    - Liquidity filtering
    - Time-based filtering
    - Market type filtering
    - Keyword exclusion
    - Persistent exclusion list
    """
    
    def __init__(
        self,
        criteria: Optional[FilterCriteria] = None,
        exclusion_list_path: Optional[Path] = None,
        component: str = "alpha.market_filter"
    ):
        """
        Initialize market filter.
        
        Args:
            criteria: Filter criteria (uses defaults if None)
            exclusion_list_path: Path to exclusion list file
            component: Component name for audit logging
        """
        self.criteria = criteria or FilterCriteria()
        
        if exclusion_list_path is None:
            repo_root = Path(__file__).parent.parent
            exclusion_list_path = repo_root / "state" / "market_exclusion_list.json"
        
        self.exclusion_list_path = exclusion_list_path
        self.exclusion_list: Set[str] = self._load_exclusion_list()
        
        self.audit = get_audit_logger(component=component)
        
        # Statistics
        self.stats = {
            'total_checked': 0,
            'passed': 0,
            'rejected_liquidity': 0,
            'rejected_price': 0,
            'rejected_time': 0,
            'rejected_type': 0,
            'rejected_excluded': 0,
            'rejected_keyword': 0
        }
    
    def _load_exclusion_list(self) -> Set[str]:
        """Load market exclusion list from file"""
        if not self.exclusion_list_path.exists():
            return set()
        
        try:
            with open(self.exclusion_list_path, 'r') as f:
                data = json.load(f)
            return set(data.get('excluded_markets', []))
        except Exception as e:
            # Log error but continue with empty list
            return set()
    
    def _save_exclusion_list(self) -> None:
        """Save market exclusion list to file"""
        try:
            # Create parent directory if needed
            self.exclusion_list_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Atomic write
            tmp_path = self.exclusion_list_path.with_suffix('.tmp')
            with open(tmp_path, 'w') as f:
                json.dump({
                    'excluded_markets': sorted(list(self.exclusion_list)),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }, f, indent=2)
            tmp_path.replace(self.exclusion_list_path)
            
        except Exception as e:
            self.audit.log_error(
                error_type="exclusion_list_save_error",
                error_message=str(e)
            )
    
    def add_to_exclusion_list(self, market_id: str, reason: str = "") -> None:
        """
        Add a market to the exclusion list.
        
        Args:
            market_id: Market identifier to exclude
            reason: Reason for exclusion
        """
        self.exclusion_list.add(market_id)
        self._save_exclusion_list()
        
        self.audit.log(
            event_type="market_excluded",
            event_data={
                "market_id": market_id,
                "reason": reason
            }
        )
    
    def remove_from_exclusion_list(self, market_id: str) -> bool:
        """
        Remove a market from the exclusion list.
        
        Args:
            market_id: Market identifier to remove
            
        Returns:
            True if removed, False if not in list
        """
        if market_id in self.exclusion_list:
            self.exclusion_list.remove(market_id)
            self._save_exclusion_list()
            
            self.audit.log(
                event_type="market_unexcluded",
                event_data={"market_id": market_id}
            )
            
            return True
        
        return False
    
    def _check_liquidity(self, market: Dict[str, Any]) -> FilterResult:
        """Check if market meets liquidity requirements"""
        # For now, use a placeholder since real liquidity data isn't available
        # In production, would fetch from Polymarket API
        liquidity = market.get('liquidity', 1000.0)
        
        if liquidity < self.criteria.min_liquidity:
            return FilterResult(
                passed=False,
                reason=f"Liquidity ${liquidity:.0f} below minimum ${self.criteria.min_liquidity:.0f}"
            )
        
        return FilterResult(passed=True)
    
    def _check_price_range(self, market: Dict[str, Any]) -> FilterResult:
        """Check if market price is in acceptable range"""
        price = market.get('last', market.get('bestBid', 0.5))
        
        if price < self.criteria.min_price:
            return FilterResult(
                passed=False,
                reason=f"Price {price:.2f} below minimum {self.criteria.min_price:.2f}"
            )
        
        if price > self.criteria.max_price:
            return FilterResult(
                passed=False,
                reason=f"Price {price:.2f} above maximum {self.criteria.max_price:.2f}"
            )
        
        return FilterResult(passed=True)
    
    def _check_time_to_resolution(self, market: Dict[str, Any]) -> FilterResult:
        """Check if market meets time-to-resolution requirements"""
        end_date_str = market.get('endDate')
        
        # If no end date, we can't filter by time
        if not end_date_str:
            return FilterResult(passed=True)
        
        try:
            # Parse end date
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            days_to_resolution = (end_date - now).days
            
            # Check minimum time
            if days_to_resolution < self.criteria.min_days_to_resolution:
                return FilterResult(
                    passed=False,
                    reason=f"Resolves in {days_to_resolution} days, minimum is {self.criteria.min_days_to_resolution}"
                )
            
            # Check maximum time
            if self.criteria.max_days_to_resolution is not None:
                if days_to_resolution > self.criteria.max_days_to_resolution:
                    return FilterResult(
                        passed=False,
                        reason=f"Resolves in {days_to_resolution} days, maximum is {self.criteria.max_days_to_resolution}"
                    )
            
            return FilterResult(passed=True)
            
        except Exception as e:
            # If we can't parse date, skip this check
            return FilterResult(passed=True)
    
    def _check_market_type(self, market: Dict[str, Any]) -> FilterResult:
        """Check if market type is acceptable"""
        # For V1, we only support binary markets
        # In the Polymarket data, all markets appear to be binary
        # This is a placeholder for future multi-outcome support
        
        if self.criteria.only_binary:
            # All current markets are binary, so pass
            return FilterResult(passed=True)
        
        return FilterResult(passed=True)
    
    def _check_keywords(self, market: Dict[str, Any]) -> FilterResult:
        """Check if market question contains excluded keywords"""
        question = market.get('question', '').lower()
        
        for keyword in self.criteria.exclude_keywords:
            if keyword.lower() in question:
                return FilterResult(
                    passed=False,
                    reason=f"Question contains excluded keyword: {keyword}"
                )
        
        return FilterResult(passed=True)
    
    def _check_exclusion_list(self, market: Dict[str, Any]) -> FilterResult:
        """Check if market is in exclusion list"""
        market_id = market.get('slug', market.get('market_id', ''))
        
        if market_id in self.exclusion_list:
            return FilterResult(
                passed=False,
                reason="Market is in exclusion list"
            )
        
        return FilterResult(passed=True)
    
    def filter_market(self, market: Dict[str, Any]) -> FilterResult:
        """
        Filter a single market against all criteria.
        
        Args:
            market: Market dict to filter
            
        Returns:
            FilterResult indicating if market passed and reason if not
        """
        self.stats['total_checked'] += 1
        
        # Check exclusion list first
        result = self._check_exclusion_list(market)
        if not result.passed:
            self.stats['rejected_excluded'] += 1
            return result
        
        # Check price range
        result = self._check_price_range(market)
        if not result.passed:
            self.stats['rejected_price'] += 1
            return result
        
        # Check liquidity
        result = self._check_liquidity(market)
        if not result.passed:
            self.stats['rejected_liquidity'] += 1
            return result
        
        # Check time to resolution
        result = self._check_time_to_resolution(market)
        if not result.passed:
            self.stats['rejected_time'] += 1
            return result
        
        # Check market type
        result = self._check_market_type(market)
        if not result.passed:
            self.stats['rejected_type'] += 1
            return result
        
        # Check keywords
        result = self._check_keywords(market)
        if not result.passed:
            self.stats['rejected_keyword'] += 1
            return result
        
        # Passed all filters
        self.stats['passed'] += 1
        return FilterResult(passed=True)
    
    def filter_markets(
        self,
        markets: List[Dict[str, Any]],
        log_rejections: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Filter a list of markets.
        
        Args:
            markets: List of market dicts
            log_rejections: Whether to log rejected markets
            
        Returns:
            List of markets that passed filters
        """
        filtered = []
        
        for market in markets:
            result = self.filter_market(market)
            
            if result.passed:
                filtered.append(market)
            elif log_rejections:
                market_id = market.get('slug', market.get('market_id', 'unknown'))
                self.audit.log(
                    event_type="market_filtered",
                    event_data={
                        "market_id": market_id,
                        "reason": result.reason
                    },
                    severity="debug"
                )
        
        return filtered
    
    def filter_from_data(
        self,
        data: Dict[str, Any],
        log_rejections: bool = False
    ) -> Dict[str, Any]:
        """
        Filter markets from polymarket data structure.
        
        Args:
            data: Polymarket data dict (from polymarket-compact.json)
            log_rejections: Whether to log rejected markets
            
        Returns:
            Filtered data with same structure
        """
        filtered_data = {
            'timestamp': data.get('timestamp'),
            'markets': {},
            'counts': {}
        }
        
        markets_by_query = data.get('markets', {})
        
        for query, markets in markets_by_query.items():
            filtered_markets = self.filter_markets(markets, log_rejections)
            
            if filtered_markets:
                filtered_data['markets'][query] = filtered_markets
                filtered_data['counts'][query] = len(filtered_markets)
        
        filtered_data['queries'] = list(filtered_data['markets'].keys())
        
        # Log summary
        self.audit.log(
            event_type="batch_filter",
            event_data={
                "input_markets": self.stats['total_checked'],
                "output_markets": self.stats['passed'],
                "rejection_rate": (self.stats['total_checked'] - self.stats['passed']) / max(1, self.stats['total_checked'])
            }
        )
        
        return filtered_data
    
    def get_stats(self) -> Dict[str, Any]:
        """Get filtering statistics"""
        return self.stats.copy()


# Convenience function
def get_market_filter(criteria: Optional[FilterCriteria] = None) -> MarketFilter:
    """Get a configured market filter instance"""
    return MarketFilter(criteria=criteria)


if __name__ == "__main__":
    # Test the market filter
    from alpha.data_fetcher import get_data_fetcher
    
    print("Testing market filter...")
    
    # Get data
    repo_root = Path(__file__).parent.parent
    source = repo_root / 'termux-hands-off' / 'out' / 'polymarket-compact.json'
    
    if not source.exists():
        print(f"Error: Source file not found: {source}", file=sys.stderr)
        sys.exit(1)
    
    fetcher = get_data_fetcher()
    data = fetcher.fetch_with_retry(source, use_cache=False)
    
    # Test with default criteria
    print("\n1. Testing with default criteria...")
    filter1 = MarketFilter()
    filtered_data1 = filter1.filter_from_data(data)
    stats1 = filter1.get_stats()
    
    print(f"   Input: {stats1['total_checked']} markets")
    print(f"   Output: {stats1['passed']} markets")
    print(f"   Rejected by price: {stats1['rejected_price']}")
    print(f"   Rejected by liquidity: {stats1['rejected_liquidity']}")
    
    # Test with stricter criteria
    print("\n2. Testing with stricter criteria...")
    criteria2 = FilterCriteria(
        min_liquidity=50000.0,  # $50k minimum
        min_price=0.10,
        max_price=0.90
    )
    filter2 = MarketFilter(criteria=criteria2)
    filtered_data2 = filter2.filter_from_data(data)
    stats2 = filter2.get_stats()
    
    print(f"   Input: {stats2['total_checked']} markets")
    print(f"   Output: {stats2['passed']} markets")
    print(f"   Rejected by price: {stats2['rejected_price']}")
    print(f"   Rejected by liquidity: {stats2['rejected_liquidity']}")
    
    # Test exclusion list
    print("\n3. Testing exclusion list...")
    filter3 = MarketFilter()
    
    # Add first market to exclusion list
    markets = data.get('markets', {})
    if markets:
        first_query = list(markets.keys())[0]
        first_market = markets[first_query][0]
        market_id = first_market.get('slug', '')
        
        if market_id:
            filter3.add_to_exclusion_list(market_id, "Test exclusion")
            print(f"   Added to exclusion list: {market_id}")
            
            # Filter again
            filtered_data3 = filter3.filter_from_data(data)
            stats3 = filter3.get_stats()
            
            print(f"   Rejected by exclusion: {stats3['rejected_excluded']}")
            
            # Remove from exclusion list
            filter3.remove_from_exclusion_list(market_id)
            print(f"   Removed from exclusion list: {market_id}")
    
    print("\n✓ Market filter tests complete!")
