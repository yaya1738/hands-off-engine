#!/usr/bin/env python3
"""
Enhanced Polymarket Data Pipeline

Integrates:
- Data fetcher with retry logic and caching
- Historical odds tracking
- Market filtering
- State management

This is the new main entry point for the alpha pipeline.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha.data_fetcher import get_data_fetcher, DataFetchError
from alpha.historical_odds import get_odds_tracker
from alpha.market_filter import get_market_filter, FilterCriteria
from alpha.sync_polymarket_model import transform_market, calculate_edge
from audit import get_audit_logger


class EnhancedPipeline:
    """
    Enhanced data pipeline for Polymarket alpha generation.
    
    Pipeline stages:
    1. Fetch data (with caching and retry)
    2. Filter markets (by liquidity, price, etc.)
    3. Track historical odds
    4. Calculate alpha signals
    5. Output to polymarket-model.json
    """
    
    def __init__(
        self,
        repo_root: Optional[Path] = None,
        cache_ttl_seconds: int = 300,
        filter_criteria: Optional[FilterCriteria] = None
    ):
        """
        Initialize enhanced pipeline.
        
        Args:
            repo_root: Repository root path
            cache_ttl_seconds: Cache TTL for data fetcher
            filter_criteria: Market filter criteria
        """
        self.repo_root = repo_root or Path(__file__).parent.parent
        
        # Initialize components
        self.fetcher = get_data_fetcher(cache_ttl_seconds=cache_ttl_seconds)
        self.odds_tracker = get_odds_tracker()
        self.market_filter = get_market_filter(criteria=filter_criteria)
        self.audit = get_audit_logger(component="alpha.enhanced_pipeline")
        
        # Paths
        self.input_path = self.repo_root / 'termux-hands-off' / 'out' / 'polymarket-compact.json'
        self.output_path = self.repo_root / 'state' / 'polymarket-model.json'
        self.fetch_log_path = self.repo_root / 'state' / 'fetch_log.jsonl'
        self.metrics_path = self.repo_root / 'state' / 'pipeline_metrics.json'
    
    def _log_fetch(
        self,
        success: bool,
        markets_fetched: int = 0,
        markets_filtered: int = 0,
        error: Optional[str] = None
    ) -> None:
        """Log fetch attempt to JSONL file"""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'success': success,
            'markets_fetched': markets_fetched,
            'markets_filtered': markets_filtered
        }
        
        if error:
            log_entry['error'] = error
        
        try:
            # Append to JSONL file
            with open(self.fetch_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            # Fallback to audit logger
            self.audit.log_error(
                error_type="fetch_log_write_error",
                error_message=str(e)
            )
    
    def _update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update pipeline metrics"""
        try:
            # Load existing metrics
            existing = {}
            if self.metrics_path.exists():
                with open(self.metrics_path, 'r') as f:
                    existing = json.load(f)
            
            # Update with new metrics
            existing.update(metrics)
            existing['last_updated'] = datetime.now(timezone.utc).isoformat()
            
            # Save atomically
            tmp_path = self.metrics_path.with_suffix('.tmp')
            with open(tmp_path, 'w') as f:
                json.dump(existing, f, indent=2)
            tmp_path.replace(self.metrics_path)
            
        except Exception as e:
            self.audit.log_error(
                error_type="metrics_update_error",
                error_message=str(e)
            )
    
    def run(
        self,
        use_cache: bool = True,
        max_markets: int = 20,
        update_history: bool = True
    ) -> Dict[str, Any]:
        """
        Run the enhanced pipeline.
        
        Args:
            use_cache: Whether to use data cache
            max_markets: Maximum markets to include in output
            update_history: Whether to update historical odds
            
        Returns:
            Generated model dict
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Stage 1: Fetch data
            self.audit.log(
                event_type="pipeline_start",
                event_data={"stage": "fetch"}
            )
            
            try:
                raw_data = self.fetcher.fetch_with_retry(
                    self.input_path,
                    use_cache=use_cache
                )
            except DataFetchError as e:
                self._log_fetch(success=False, error=str(e))
                raise
            
            # Count raw markets
            raw_market_count = sum(
                len(markets) for markets in raw_data.get('markets', {}).values()
            )
            
            # Stage 2: Filter markets
            self.audit.log(
                event_type="pipeline_stage",
                event_data={"stage": "filter"}
            )
            
            filtered_data = self.market_filter.filter_from_data(raw_data)
            filter_stats = self.market_filter.get_stats()
            
            # Stage 3: Update historical odds
            if update_history:
                self.audit.log(
                    event_type="pipeline_stage",
                    event_data={"stage": "history"}
                )
                
                self.odds_tracker.batch_update_from_data(raw_data)
            
            # Stage 4: Transform to alpha signals
            self.audit.log(
                event_type="pipeline_stage",
                event_data={"stage": "alpha"}
            )
            
            all_markets = []
            markets_by_query = filtered_data.get('markets', {})
            
            for query, markets in markets_by_query.items():
                for market in markets:
                    transformed = transform_market(market, query)
                    if transformed:
                        # Add velocity data if available
                        market_id = transformed['market_id']
                        velocity = self.odds_tracker.calculate_velocity(market_id)
                        
                        if velocity:
                            transformed['velocity_1h'] = velocity.velocity_1h
                            transformed['velocity_24h'] = velocity.velocity_24h
                            transformed['is_sharp_move'] = velocity.is_sharp_move
                        
                        all_markets.append(transformed)
            
            # Sort by edge and take top N
            all_markets.sort(key=lambda m: m['model_edge'], reverse=True)
            top_markets = all_markets[:max_markets]
            
            # Stage 5: Build output model
            model = {
                'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'source_timestamp': raw_data.get('timestamp', ''),
                'pipeline_version': '2.0',
                'total_markets_fetched': raw_market_count,
                'total_markets_filtered': len(all_markets),
                'markets_selected': len(top_markets),
                'filter_stats': filter_stats,
                'markets': top_markets
            }
            
            # Stage 6: Write output
            self.audit.log(
                event_type="pipeline_stage",
                event_data={"stage": "output"}
            )
            
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Atomic write
            tmp_path = self.output_path.with_suffix('.tmp')
            with open(tmp_path, 'w') as f:
                json.dump(model, f, indent=2)
            tmp_path.replace(self.output_path)
            
            # Log success
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            self._log_fetch(
                success=True,
                markets_fetched=raw_market_count,
                markets_filtered=len(all_markets)
            )
            
            self._update_metrics({
                'last_success': start_time.isoformat(),
                'last_duration_seconds': duration,
                'last_markets_fetched': raw_market_count,
                'last_markets_filtered': len(all_markets),
                'last_markets_selected': len(top_markets)
            })
            
            self.audit.log(
                event_type="pipeline_complete",
                event_data={
                    'duration_seconds': duration,
                    'markets_fetched': raw_market_count,
                    'markets_filtered': len(all_markets),
                    'markets_selected': len(top_markets)
                }
            )
            
            return model
            
        except Exception as e:
            # Log failure
            self._log_fetch(success=False, error=str(e))
            
            self._update_metrics({
                'last_failure': start_time.isoformat(),
                'last_error': str(e)
            })
            
            self.audit.log_error(
                error_type="pipeline_error",
                error_message=str(e)
            )
            
            raise


def main():
    """Main entry point"""
    print("🚀 Enhanced Polymarket Data Pipeline V2")
    print("=" * 70)
    
    # Create pipeline with default settings
    # Use conservative filter to allow placeholder liquidity data
    filter_criteria = FilterCriteria(
        min_liquidity=0.0,  # Disable liquidity filter for now (placeholder data)
        min_price=0.05,
        max_price=0.95
    )
    
    pipeline = EnhancedPipeline(filter_criteria=filter_criteria)
    
    try:
        print("\n📊 Running pipeline...")
        model = pipeline.run(use_cache=True, max_markets=20)
        
        print("\n✓ Pipeline completed successfully!")
        print(f"  Generated at: {model['generated_at']}")
        print(f"  Markets fetched: {model['total_markets_fetched']}")
        print(f"  Markets after filtering: {model['total_markets_filtered']}")
        print(f"  Markets selected: {model['markets_selected']}")
        
        # Show filter stats
        filter_stats = model.get('filter_stats', {})
        if filter_stats:
            print(f"\n  Filter Statistics:")
            print(f"    - Rejected by price: {filter_stats.get('rejected_price', 0)}")
            print(f"    - Rejected by liquidity: {filter_stats.get('rejected_liquidity', 0)}")
            print(f"    - Rejected by time: {filter_stats.get('rejected_time', 0)}")
            print(f"    - Rejected by exclusion: {filter_stats.get('rejected_excluded', 0)}")
        
        # Show top markets
        if model['markets']:
            print(f"\n  Top opportunities:")
            for i, m in enumerate(model['markets'][:5], 1):
                question = m['question'][:60] + ('...' if len(m['question']) > 60 else '')
                print(f"    {i}. {question}")
                print(f"       Edge: {m['model_edge']:.1%}, Confidence: {m['model_confidence']:.1%}, Side: {m['side']}")
                
                # Show velocity if available
                if 'velocity_1h' in m and m['velocity_1h'] is not None:
                    vel_indicator = "🔥" if m.get('is_sharp_move', False) else ""
                    print(f"       Velocity: {m['velocity_1h']:.4f}/h {vel_indicator}")
        
        print(f"\n  Output: {pipeline.output_path}")
        print(f"  Fetch log: {pipeline.fetch_log_path}")
        print(f"  Metrics: {pipeline.metrics_path}")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
