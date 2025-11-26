#!/usr/bin/env python3
"""
Data Fetcher for Polymarket Pipeline

Handles data fetching with:
- Retry logic with exponential backoff
- Caching to reduce API calls
- Rate limiting protection
- Multiple data source support with fallback
"""

import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audit import get_audit_logger


class DataFetchError(Exception):
    """Raised when data fetching fails after all retries"""
    pass


class DataFetcher:
    """
    Data fetcher with retry logic, caching, and rate limiting.
    
    Features:
    - Exponential backoff for retries
    - File-based caching with TTL
    - Rate limiting to protect against excessive API calls
    - Multiple data source support
    """
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        cache_ttl_seconds: int = 300,  # 5 minutes default
        max_retries: int = 3,
        base_delay_seconds: float = 1.0,
        rate_limit_calls: int = 60,
        rate_limit_period: int = 60,
        component: str = "alpha.data_fetcher"
    ):
        """
        Initialize data fetcher.
        
        Args:
            cache_dir: Directory for cache files (defaults to state/)
            cache_ttl_seconds: Cache time-to-live in seconds
            max_retries: Maximum number of retry attempts
            base_delay_seconds: Base delay for exponential backoff
            rate_limit_calls: Maximum calls per period
            rate_limit_period: Rate limit period in seconds
            component: Component name for audit logging
        """
        self.cache_dir = cache_dir or Path(__file__).parent.parent / "state"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_retries = max_retries
        self.base_delay_seconds = base_delay_seconds
        self.rate_limit_calls = rate_limit_calls
        self.rate_limit_period = rate_limit_period
        
        self.audit = get_audit_logger(component=component)
        
        # Rate limiting state
        self._call_times: List[float] = []
    
    def _check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits.
        
        Returns:
            True if we can make a call, False if rate limited
        """
        now = time.time()
        
        # Remove old timestamps outside the window
        cutoff = now - self.rate_limit_period
        self._call_times = [t for t in self._call_times if t > cutoff]
        
        # Check if we're under the limit
        if len(self._call_times) >= self.rate_limit_calls:
            return False
        
        # Record this call
        self._call_times.append(now)
        return True
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a given key"""
        # Sanitize key for filename
        safe_key = cache_key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"cache_{safe_key}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """
        Check if cache file is valid (exists and not expired).
        
        Args:
            cache_path: Path to cache file
            
        Returns:
            True if cache is valid, False otherwise
        """
        if not cache_path.exists():
            return False
        
        # Check age
        mtime = cache_path.stat().st_mtime
        age_seconds = time.time() - mtime
        
        return age_seconds < self.cache_ttl_seconds
    
    def _read_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Read data from cache if valid.
        
        Args:
            cache_key: Cache key to look up
            
        Returns:
            Cached data if valid, None otherwise
        """
        cache_path = self._get_cache_path(cache_key)
        
        if not self._is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            self.audit.log(
                event_type="cache_hit",
                event_data={
                    "cache_key": cache_key,
                    "cache_path": str(cache_path)
                }
            )
            
            return data
            
        except Exception as e:
            self.audit.log_error(
                error_type="cache_read_error",
                error_message=str(e),
                context={"cache_key": cache_key}
            )
            return None
    
    def _write_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """
        Write data to cache.
        
        Args:
            cache_key: Cache key
            data: Data to cache
        """
        cache_path = self._get_cache_path(cache_key)
        
        try:
            # Atomic write
            tmp_path = cache_path.with_suffix('.tmp')
            with open(tmp_path, 'w') as f:
                json.dump(data, f, indent=2)
            tmp_path.replace(cache_path)
            
            self.audit.log(
                event_type="cache_write",
                event_data={
                    "cache_key": cache_key,
                    "cache_path": str(cache_path)
                }
            )
            
        except Exception as e:
            self.audit.log_error(
                error_type="cache_write_error",
                error_message=str(e),
                context={"cache_key": cache_key}
            )
    
    def _fetch_from_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Fetch data from a local file.
        
        Args:
            file_path: Path to data file
            
        Returns:
            Parsed JSON data
            
        Raises:
            DataFetchError: If file cannot be read
        """
        if not file_path.exists():
            raise DataFetchError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise DataFetchError(f"Failed to read file {file_path}: {e}")
    
    def fetch_with_retry(
        self,
        source_path: Path,
        cache_key: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch data with retry logic and caching.
        
        Args:
            source_path: Path to data source file
            cache_key: Optional cache key (defaults to source path)
            use_cache: Whether to use caching
            
        Returns:
            Fetched data
            
        Raises:
            DataFetchError: If all fetch attempts fail
        """
        # Use source path as cache key if not provided
        if cache_key is None:
            cache_key = str(source_path)
        
        # Try cache first
        if use_cache:
            cached_data = self._read_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Check rate limit
        if not self._check_rate_limit():
            # Wait for rate limit window to reset
            wait_time = self.rate_limit_period - (time.time() - min(self._call_times))
            
            self.audit.log(
                event_type="rate_limit_wait",
                event_data={
                    "wait_seconds": wait_time,
                    "source": str(source_path)
                },
                severity="warning"
            )
            
            time.sleep(max(0, wait_time))
        
        # Fetch with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                data = self._fetch_from_file(source_path)
                
                # Log success
                self.audit.log_data_fetch(
                    source=str(source_path),
                    params={"attempt": attempt + 1},
                    success=True,
                    record_count=self._count_records(data)
                )
                
                # Cache the result
                if use_cache:
                    self._write_cache(cache_key, data)
                
                return data
                
            except Exception as e:
                last_error = e
                
                # Log failure
                self.audit.log_data_fetch(
                    source=str(source_path),
                    params={"attempt": attempt + 1},
                    success=False,
                    error=str(e)
                )
                
                # Wait before retry with exponential backoff
                if attempt < self.max_retries - 1:
                    delay = self.base_delay_seconds * (2 ** attempt)
                    time.sleep(delay)
        
        # All retries failed
        raise DataFetchError(f"Failed to fetch after {self.max_retries} attempts: {last_error}")
    
    def fetch_with_fallback(
        self,
        sources: List[Path],
        cache_key: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch data with fallback to multiple sources.
        
        Tries each source in order until one succeeds.
        
        Args:
            sources: List of source paths to try in order
            cache_key: Optional cache key
            use_cache: Whether to use caching
            
        Returns:
            Fetched data from first successful source
            
        Raises:
            DataFetchError: If all sources fail
        """
        if not sources:
            raise DataFetchError("No sources provided")
        
        last_errors = []
        
        for i, source in enumerate(sources):
            try:
                self.audit.log(
                    event_type="fallback_attempt",
                    event_data={
                        "source": str(source),
                        "attempt": i + 1,
                        "total_sources": len(sources)
                    }
                )
                
                return self.fetch_with_retry(source, cache_key, use_cache)
                
            except DataFetchError as e:
                last_errors.append((str(source), str(e)))
                continue
        
        # All sources failed
        error_summary = "; ".join([f"{src}: {err}" for src, err in last_errors])
        raise DataFetchError(f"All {len(sources)} sources failed: {error_summary}")
    
    def invalidate_cache(self, cache_key: str) -> bool:
        """
        Invalidate a cache entry.
        
        Args:
            cache_key: Cache key to invalidate
            
        Returns:
            True if cache was invalidated, False if it didn't exist
        """
        cache_path = self._get_cache_path(cache_key)
        
        if cache_path.exists():
            try:
                cache_path.unlink()
                
                self.audit.log(
                    event_type="cache_invalidate",
                    event_data={"cache_key": cache_key}
                )
                
                return True
            except Exception as e:
                self.audit.log_error(
                    error_type="cache_invalidate_error",
                    error_message=str(e),
                    context={"cache_key": cache_key}
                )
        
        return False
    
    def _count_records(self, data: Dict[str, Any]) -> int:
        """
        Count records in fetched data.
        
        Args:
            data: Fetched data dict
            
        Returns:
            Number of records (markets)
        """
        if 'markets' in data:
            return sum(len(markets) for markets in data['markets'].values())
        return 0


# Convenience function
def get_data_fetcher(cache_ttl_seconds: int = 300) -> DataFetcher:
    """
    Get a configured data fetcher instance.
    
    Args:
        cache_ttl_seconds: Cache TTL in seconds (default: 5 minutes)
        
    Returns:
        Configured DataFetcher instance
    """
    return DataFetcher(cache_ttl_seconds=cache_ttl_seconds)


if __name__ == "__main__":
    # Test the data fetcher
    import sys
    
    fetcher = DataFetcher(cache_ttl_seconds=60)
    
    # Test with polymarket-compact.json
    repo_root = Path(__file__).parent.parent
    source = repo_root / 'termux-hands-off' / 'out' / 'polymarket-compact.json'
    
    if source.exists():
        print("Testing data fetcher...")
        
        # First fetch (should hit source)
        print("\n1. Fetching from source...")
        data1 = fetcher.fetch_with_retry(source)
        print(f"   ✓ Fetched {fetcher._count_records(data1)} markets")
        
        # Second fetch (should hit cache)
        print("\n2. Fetching again (should use cache)...")
        data2 = fetcher.fetch_with_retry(source)
        print(f"   ✓ Fetched {fetcher._count_records(data2)} markets")
        
        # Test cache invalidation
        print("\n3. Invalidating cache...")
        cache_key = str(source)
        if fetcher.invalidate_cache(cache_key):
            print("   ✓ Cache invalidated")
        
        # Test fallback
        print("\n4. Testing fallback...")
        sources = [
            Path("/nonexistent/file.json"),
            source
        ]
        data3 = fetcher.fetch_with_fallback(sources)
        print(f"   ✓ Fetched with fallback: {fetcher._count_records(data3)} markets")
        
        print("\n✓ All tests passed!")
    else:
        print(f"Error: Source file not found: {source}", file=sys.stderr)
        sys.exit(1)
