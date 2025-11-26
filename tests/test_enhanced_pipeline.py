#!/usr/bin/env python3
"""
Tests for Enhanced Polymarket Data Pipeline Components
"""

import json
import sys
import tempfile
import time
import traceback
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha.data_fetcher import DataFetcher, DataFetchError
from alpha.historical_odds import HistoricalOddsTracker, OddsSnapshot
from alpha.market_filter import MarketFilter, FilterCriteria
from alpha.enhanced_pipeline import EnhancedPipeline


def test_data_fetcher():
    """Test data fetcher with retry and caching"""
    print("Testing DataFetcher...")
    
    repo_root = Path(__file__).parent.parent
    source = repo_root / 'termux-hands-off' / 'out' / 'polymarket-compact.json'
    
    if not source.exists():
        print("  ⊘ Skipping: Source file not found")
        return True
    
    # Test basic fetch
    fetcher = DataFetcher(cache_ttl_seconds=60)
    data = fetcher.fetch_with_retry(source)
    
    assert 'markets' in data, "Data should have 'markets' key"
    assert fetcher._count_records(data) > 0, "Should have markets"
    
    # Test caching
    data2 = fetcher.fetch_with_retry(source)
    assert data == data2, "Cached data should match"
    
    # Test cache invalidation
    cache_key = str(source)
    assert fetcher.invalidate_cache(cache_key), "Should invalidate cache"
    
    # Test fallback
    sources = [Path("/nonexistent/file.json"), source]
    data3 = fetcher.fetch_with_fallback(sources)
    assert 'markets' in data3, "Fallback should work"
    
    print("  ✓ DataFetcher: PASS")
    return True


def test_historical_odds_tracker():
    """Test historical odds tracking"""
    print("Testing HistoricalOddsTracker...")
    
    # Create tracker with temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = HistoricalOddsTracker(history_dir=Path(tmpdir))
        
        # Test adding snapshots
        tracker.add_snapshot(
            market_id="test-market-1",
            question="Test Question 1",
            best_bid=0.45,
            last_price=0.50
        )
        
        # Test loading history
        history = tracker.load_history("test-market-1")
        assert history is not None, "Should load history"
        assert history.market_id == "test-market-1", "Market ID should match"
        assert len(history.snapshots) == 1, "Should have 1 snapshot"
        
        # Test adding more snapshots
        for i in range(5):
            tracker.add_snapshot(
                market_id="test-market-1",
                question="Test Question 1",
                best_bid=0.45 + i * 0.01,
                last_price=0.50 + i * 0.01
            )
        
        history = tracker.load_history("test-market-1")
        assert len(history.snapshots) == 6, "Should have 6 snapshots"
        
        # Test velocity calculation (will be None without time gaps)
        velocity = tracker.calculate_velocity("test-market-1")
        # Velocity might be None if not enough time history
        
        print("  ✓ HistoricalOddsTracker: PASS")
        return True


def test_market_filter():
    """Test market filtering"""
    print("Testing MarketFilter...")
    
    # Test with default criteria
    filter1 = MarketFilter()
    
    # Create test market
    test_market = {
        'slug': 'test-market',
        'question': 'Test Question?',
        'last': 0.50,
        'bestBid': 0.48,
        'liquidity': 15000.0
    }
    
    # Should pass (price in range, liquidity ok)
    result = filter1.filter_market(test_market)
    assert result.passed, f"Market should pass: {result.reason}"
    
    # Test price filtering
    low_price_market = test_market.copy()
    low_price_market['last'] = 0.02
    result = filter1.filter_market(low_price_market)
    assert not result.passed, "Low price market should be rejected"
    
    high_price_market = test_market.copy()
    high_price_market['last'] = 0.98
    result = filter1.filter_market(high_price_market)
    assert not result.passed, "High price market should be rejected"
    
    # Test exclusion list
    with tempfile.TemporaryDirectory() as tmpdir:
        exclusion_path = Path(tmpdir) / "exclusion.json"
        filter2 = MarketFilter(exclusion_list_path=exclusion_path)
        
        filter2.add_to_exclusion_list("test-market", "Test")
        result = filter2.filter_market(test_market)
        assert not result.passed, "Excluded market should be rejected"
        
        filter2.remove_from_exclusion_list("test-market")
        result = filter2.filter_market(test_market)
        assert result.passed, "Unexcluded market should pass"
    
    # Test keyword filtering
    criteria_keywords = FilterCriteria(exclude_keywords=["exclude"])
    filter3 = MarketFilter(criteria=criteria_keywords)
    
    keyword_market = test_market.copy()
    keyword_market['question'] = "This has exclude word"
    result = filter3.filter_market(keyword_market)
    assert not result.passed, "Market with excluded keyword should be rejected"
    
    print("  ✓ MarketFilter: PASS")
    return True


def test_enhanced_pipeline():
    """Test enhanced pipeline integration"""
    print("Testing EnhancedPipeline...")
    
    repo_root = Path(__file__).parent.parent
    input_path = repo_root / 'termux-hands-off' / 'out' / 'polymarket-compact.json'
    
    if not input_path.exists():
        print("  ⊘ Skipping: Input file not found")
        return True
    
    # Create pipeline with test settings
    filter_criteria = FilterCriteria(
        min_liquidity=0.0,  # Disable for testing
        min_price=0.05,
        max_price=0.95
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = EnhancedPipeline(filter_criteria=filter_criteria)
        
        # Override output paths to temp directory
        pipeline.output_path = Path(tmpdir) / "output.json"
        pipeline.fetch_log_path = Path(tmpdir) / "fetch.jsonl"
        pipeline.metrics_path = Path(tmpdir) / "metrics.json"
        
        # Run pipeline
        model = pipeline.run(use_cache=False, max_markets=10)
        
        # Validate output
        assert 'generated_at' in model, "Model should have timestamp"
        assert 'markets' in model, "Model should have markets"
        assert 'pipeline_version' in model, "Model should have version"
        assert model['pipeline_version'] == '2.0', "Should be version 2.0"
        
        # Check that output file was created
        assert pipeline.output_path.exists(), "Output file should exist"
        
        # Check fetch log
        assert pipeline.fetch_log_path.exists(), "Fetch log should exist"
        
        # Check metrics
        assert pipeline.metrics_path.exists(), "Metrics file should exist"
        with open(pipeline.metrics_path, 'r') as f:
            metrics = json.load(f)
        assert 'last_success' in metrics, "Metrics should have last_success"
        
        print("  ✓ EnhancedPipeline: PASS")
        return True


def test_filter_stats():
    """Test filter statistics tracking"""
    print("Testing filter statistics...")
    
    filter1 = MarketFilter()
    
    # Create test markets
    test_markets = [
        {'slug': 'm1', 'question': 'Q1', 'last': 0.50, 'liquidity': 15000},
        {'slug': 'm2', 'question': 'Q2', 'last': 0.02, 'liquidity': 15000},  # Too low
        {'slug': 'm3', 'question': 'Q3', 'last': 0.98, 'liquidity': 15000},  # Too high
        {'slug': 'm4', 'question': 'Q4', 'last': 0.60, 'liquidity': 15000},
        {'slug': 'm5', 'question': 'Q5', 'last': 0.01, 'liquidity': 15000},  # Too low
    ]
    
    filtered = filter1.filter_markets(test_markets)
    stats = filter1.get_stats()
    
    assert stats['total_checked'] == 5, "Should check 5 markets"
    assert stats['passed'] == 2, "Should pass 2 markets"
    assert stats['rejected_price'] == 3, "Should reject 3 by price"
    
    print("  ✓ Filter statistics: PASS")
    return True


def test_cache_invalidation():
    """Test cache invalidation logic"""
    print("Testing cache invalidation...")
    
    repo_root = Path(__file__).parent.parent
    source = repo_root / 'termux-hands-off' / 'out' / 'polymarket-compact.json'
    
    if not source.exists():
        print("  ⊘ Skipping: Source file not found")
        return True
    
    fetcher = DataFetcher(cache_ttl_seconds=1)  # 1 second TTL
    
    # First fetch
    data1 = fetcher.fetch_with_retry(source)
    
    # Immediate second fetch should use cache
    data2 = fetcher.fetch_with_retry(source)
    
    # Wait for cache to expire
    time.sleep(2)
    
    # Third fetch should re-fetch (cache expired)
    data3 = fetcher.fetch_with_retry(source)
    
    assert 'markets' in data3, "Should still fetch data"
    
    print("  ✓ Cache invalidation: PASS")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  ENHANCED PIPELINE TESTS")
    print("=" * 70 + "\n")
    
    tests = [
        test_data_fetcher,
        test_historical_odds_tracker,
        test_market_filter,
        test_filter_stats,
        test_cache_invalidation,
        test_enhanced_pipeline,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ {test.__name__}: FAIL - {e}")
            traceback.print_exc()
            results.append(False)
        print()
    
    # Summary
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
