#!/usr/bin/env python3
"""
Integration tests for Polymarket fetcher (Batch 12).

Tests the ho_fetch_polymarket module with mocked network calls.
NO real network requests are made in these tests.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fetchers import ho_fetch_polymarket


# Sample mock data matching Polymarket Gamma API structure
MOCK_API_RESPONSE = [
    {
        "id": "event-1",
        "title": "Bitcoin to reach $100k in 2025?",
        "slug": "bitcoin-100k-2025",
        "tags": [{"label": "Crypto"}],
        "markets": [
            {
                "id": "market-btc-1",
                "slug": "btc-100k",
                "question": "Will Bitcoin reach $100,000 by end of 2025?",
                "outcomes": ["Yes", "No"],
                "outcomePrices": ["0.65", "0.35"],
                "end_date_iso": "2025-12-31T23:59:59Z"
            }
        ]
    },
    {
        "id": "event-2",
        "title": "Lakers vs Celtics - NBA Finals",
        "slug": "lakers-celtics-finals",
        "tags": [{"label": "Sports"}, {"label": "NBA"}],
        "markets": [
            {
                "id": "market-nba-1",
                "slug": "lakers-win",
                "question": "Will Lakers win the series?",
                "outcomes": ["Yes", "No"],
                "outcomePrices": ["0.48", "0.52"],
                "end_date_iso": "2025-06-20T23:59:59Z"
            },
            {
                "id": "market-nba-2",
                "slug": "series-length",
                "question": "Will series go to 7 games?",
                "outcomes": ["Yes", "No"],
                "outcomePrices": ["0.42", "0.58"],
                "end_date_iso": "2025-06-20T23:59:59Z"
            }
        ]
    },
    {
        "id": "event-3",
        "title": "2025 Presidential Election",
        "slug": "2025-election",
        "tags": [{"label": "Politics"}],
        "markets": [
            {
                "id": "market-pol-1",
                "slug": "election-outcome",
                "question": "Who will win the election?",
                "outcomes": ["Candidate A", "Candidate B"],
                "outcomePrices": ["0.55", "0.45"],
                "end_date_iso": "2025-11-05T23:59:59Z"
            }
        ]
    }
]


class TestBuildCompactFromRaw(unittest.TestCase):
    """Test the build_compact_from_raw transformation."""

    def test_basic_structure(self):
        """Test that compact format has correct basic structure."""
        compact = ho_fetch_polymarket.build_compact_from_raw(MOCK_API_RESPONSE)

        # Check top-level fields
        self.assertIn("timestamp", compact)
        self.assertIn("markets", compact)
        self.assertIsInstance(compact["markets"], dict)

        # Timestamp should be ISO8601
        self.assertTrue(compact["timestamp"].endswith("Z"))

    def test_market_categorization(self):
        """Test that markets are correctly categorized."""
        compact = ho_fetch_polymarket.build_compact_from_raw(MOCK_API_RESPONSE)

        markets = compact["markets"]

        # Should have crypto, sports, and politics categories
        self.assertIn("crypto", markets)
        self.assertIn("sports", markets)
        self.assertIn("politics", markets)

    def test_market_fields(self):
        """Test that individual markets have required fields."""
        compact = ho_fetch_polymarket.build_compact_from_raw(MOCK_API_RESPONSE)

        # Check crypto market
        crypto_markets = compact["markets"]["crypto"]
        self.assertGreater(len(crypto_markets), 0)

        market = crypto_markets[0]

        # Required fields
        self.assertIn("id", market)
        self.assertIn("slug", market)
        self.assertIn("question", market)
        self.assertIn("bestBid", market)
        self.assertIn("last", market)
        self.assertIn("endDate", market)
        self.assertIn("title", market)
        self.assertIn("outcomes", market)
        self.assertIn("outcomePrices", market)

    def test_price_normalization(self):
        """Test that prices are correctly normalized."""
        compact = ho_fetch_polymarket.build_compact_from_raw(MOCK_API_RESPONSE)

        crypto_market = compact["markets"]["crypto"][0]

        # Check prices are floats and in valid range
        self.assertIsInstance(crypto_market["bestBid"], float)
        self.assertGreaterEqual(crypto_market["bestBid"], 0.0)
        self.assertLessEqual(crypto_market["bestBid"], 1.0)

        # bestBid should be max of outcomePrices
        self.assertAlmostEqual(crypto_market["bestBid"], 0.65, places=2)

    def test_multiple_markets_per_event(self):
        """Test that events with multiple markets are handled correctly."""
        compact = ho_fetch_polymarket.build_compact_from_raw(MOCK_API_RESPONSE)

        sports_markets = compact["markets"]["sports"]

        # Event 2 has 2 markets
        self.assertGreaterEqual(len(sports_markets), 2)

    def test_empty_input(self):
        """Test handling of empty input."""
        compact = ho_fetch_polymarket.build_compact_from_raw([])

        self.assertIn("timestamp", compact)
        self.assertIn("markets", compact)
        self.assertEqual(len(compact["markets"]), 0)

    def test_invalid_markets_filtered(self):
        """Test that markets without prices are filtered out."""
        invalid_data = [
            {
                "id": "event-bad",
                "title": "Bad Event",
                "tags": [],
                "markets": [
                    {
                        "id": "market-bad",
                        "question": "Invalid market",
                        "outcomes": ["Yes", "No"],
                        "outcomePrices": None  # No prices
                    }
                ]
            }
        ]

        compact = ho_fetch_polymarket.build_compact_from_raw(invalid_data)

        # Should have no markets
        total_markets = sum(len(m) for m in compact["markets"].values())
        self.assertEqual(total_markets, 0)


class TestWriteCompact(unittest.TestCase):
    """Test the write_compact function."""

    def test_write_creates_file(self):
        """Test that write_compact creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            compact = {"timestamp": "2025-01-01T00:00:00Z", "markets": {}}

            output_path = ho_fetch_polymarket.write_compact(tmpdir, compact)

            # Check file exists
            self.assertTrue(os.path.exists(output_path))
            self.assertEqual(output_path, os.path.join(tmpdir, "polymarket-compact.json"))

    def test_write_creates_directory(self):
        """Test that write_compact creates state directory if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = os.path.join(tmpdir, "state")
            compact = {"timestamp": "2025-01-01T00:00:00Z", "markets": {}}

            output_path = ho_fetch_polymarket.write_compact(state_dir, compact)

            # Check directory and file exist
            self.assertTrue(os.path.exists(state_dir))
            self.assertTrue(os.path.exists(output_path))

    def test_write_valid_json(self):
        """Test that written file is valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            compact = ho_fetch_polymarket.build_compact_from_raw(MOCK_API_RESPONSE)

            output_path = ho_fetch_polymarket.write_compact(tmpdir, compact)

            # Read and validate JSON
            with open(output_path, 'r') as f:
                loaded = json.load(f)

            self.assertEqual(loaded["timestamp"], compact["timestamp"])
            self.assertEqual(len(loaded["markets"]), len(compact["markets"]))

    def test_write_atomic(self):
        """Test that write is atomic (uses temp file)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            compact = {"timestamp": "2025-01-01T00:00:00Z", "markets": {}}

            output_path = ho_fetch_polymarket.write_compact(tmpdir, compact)

            # Temp file should not exist after write
            temp_path = output_path + ".tmp"
            self.assertFalse(os.path.exists(temp_path))

            # Output file should exist
            self.assertTrue(os.path.exists(output_path))


class TestFetchAndWrite(unittest.TestCase):
    """Test the fetch_and_write function with mocked network."""

    @patch('fetchers.ho_fetch_polymarket.fetch_markets_raw')
    def test_fetch_and_write_success(self, mock_fetch):
        """Test successful fetch and write with mocked network."""
        mock_fetch.return_value = MOCK_API_RESPONSE

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = ho_fetch_polymarket.fetch_and_write(tmpdir)

            # Check that fetch was called
            mock_fetch.assert_called_once()

            # Check that file exists
            self.assertTrue(os.path.exists(output_path))

            # Validate content
            with open(output_path, 'r') as f:
                compact = json.load(f)

            self.assertIn("timestamp", compact)
            self.assertIn("markets", compact)

            # Should have markets in crypto, sports, politics
            total_markets = sum(len(m) for m in compact["markets"].values())
            self.assertGreater(total_markets, 0)

    @patch('fetchers.ho_fetch_polymarket.fetch_markets_raw')
    def test_fetch_and_write_network_error(self, mock_fetch):
        """Test handling of network errors."""
        mock_fetch.side_effect = RuntimeError("Network error")

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(RuntimeError):
                ho_fetch_polymarket.fetch_and_write(tmpdir)

    @patch('fetchers.ho_fetch_polymarket.fetch_markets_raw')
    def test_fetch_and_write_default_dir(self, mock_fetch):
        """Test that default state_dir is 'state'."""
        mock_fetch.return_value = []

        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                output_path = ho_fetch_polymarket.fetch_and_write()

                # Should create 'state' directory
                self.assertTrue(os.path.exists("state"))
                self.assertEqual(output_path, os.path.join("state", "polymarket-compact.json"))

            finally:
                os.chdir(old_cwd)


class TestCategoryInference(unittest.TestCase):
    """Test the _infer_category helper."""

    def test_crypto_category(self):
        """Test crypto category inference."""
        category = ho_fetch_polymarket._infer_category(
            "Bitcoin Price Prediction",
            "Will BTC reach $100k?",
            [{"label": "Crypto"}]
        )
        self.assertEqual(category, "crypto")

    def test_sports_category(self):
        """Test sports category inference."""
        category = ho_fetch_polymarket._infer_category(
            "NBA Finals 2025",
            "Lakers vs Celtics",
            [{"label": "Sports"}]
        )
        self.assertEqual(category, "sports")

    def test_politics_category(self):
        """Test politics category inference."""
        category = ho_fetch_polymarket._infer_category(
            "Presidential Election",
            "Who will win?",
            [{"label": "Politics"}]
        )
        self.assertEqual(category, "politics")

    def test_fallback_category(self):
        """Test fallback to 'other' category."""
        category = ho_fetch_polymarket._infer_category(
            "Random Event",
            "Some random question",
            []
        )
        self.assertEqual(category, "other")


class TestPriceNormalization(unittest.TestCase):
    """Test the _normalize_market_prices helper."""

    def test_valid_prices(self):
        """Test normalization of valid prices."""
        market = {
            "outcomePrices": ["0.65", "0.35"]
        }

        best_bid, last = ho_fetch_polymarket._normalize_market_prices(market)

        self.assertAlmostEqual(best_bid, 0.65, places=2)
        self.assertAlmostEqual(last, 0.65, places=2)

    def test_missing_prices(self):
        """Test handling of missing prices."""
        market = {
            "outcomePrices": None
        }

        best_bid, last = ho_fetch_polymarket._normalize_market_prices(market)

        self.assertIsNone(best_bid)
        self.assertIsNone(last)

    def test_invalid_prices(self):
        """Test handling of invalid price strings."""
        market = {
            "outcomePrices": ["invalid", "0.5"]
        }

        best_bid, last = ho_fetch_polymarket._normalize_market_prices(market)

        self.assertIsNone(best_bid)
        self.assertIsNone(last)


if __name__ == "__main__":
    unittest.main()
