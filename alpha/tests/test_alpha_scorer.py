#!/usr/bin/env python3
"""
Unit tests for alpha_scorer.py
"""
import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha_scorer import (
    calculate_composite_score,
    score_candidate,
    calculate_summary_stats,
    rank_and_cap_candidates,
    ScoringConfig
)


class TestAlphaScorer(unittest.TestCase):

    def test_composite_score_basic(self):
        """Test basic composite score calculation"""
        score = calculate_composite_score(
            edge_raw=0.1,
            volume=1000000,
            spread=0.01,
            days_to_close=7,
            p_fair=0.7
        )
        self.assertGreater(score, 0)
        self.assertIsInstance(score, float)

    def test_composite_score_no_optionals(self):
        """Test composite score with minimal inputs"""
        score = calculate_composite_score(
            edge_raw=0.05,
            volume=None,
            spread=None,
            days_to_close=None,
            p_fair=0.5
        )
        # With p_fair=0.5, confidence=1.0, so score = 0.05 * (1+0) * 1 * 1 * (1+1.0) = 0.1
        self.assertAlmostEqual(score, 0.1, places=2)

    def test_score_candidate_buy_yes(self):
        """Test candidate scoring - BUY YES scenario"""
        candidate = {
            'key': 'btc_100k',
            'p_fair': 0.7,
            'p_mkt': 0.5,
            'volume': 500000,
            'category': 'crypto'
        }
        result = score_candidate(candidate)

        self.assertEqual(result['rec'], 'buy_yes')
        self.assertAlmostEqual(result['edge_raw'], 0.2, places=2)
        self.assertGreater(result['score'], 0)

    def test_score_candidate_buy_no(self):
        """Test candidate scoring - BUY NO scenario"""
        candidate = {
            'key': 'oil_crash',
            'p_fair': 0.2,
            'p_mkt': 0.6,
            'category': 'macro'
        }
        result = score_candidate(candidate)

        self.assertEqual(result['rec'], 'buy_no')
        self.assertAlmostEqual(result['edge_raw'], -0.4, places=2)

    def test_score_candidate_hold(self):
        """Test candidate scoring - HOLD scenario"""
        candidate = {
            'key': 'neutral',
            'p_fair': 0.52,
            'p_mkt': 0.50,
        }
        result = score_candidate(candidate)

        self.assertEqual(result['rec'], 'hold')

    def test_summary_stats(self):
        """Test summary statistics calculation"""
        candidates = [
            {'score': 0.1, 'edge_raw': 0.08, 'category': 'crypto'},
            {'score': 0.05, 'edge_raw': 0.04, 'category': 'crypto'},
            {'score': 0.03, 'edge_raw': 0.02, 'category': 'sports'},
        ]

        stats = calculate_summary_stats(candidates, threshold=0.02)

        self.assertEqual(stats['total_candidates'], 3)
        self.assertEqual(stats['filtered_candidates'], 3)
        self.assertAlmostEqual(stats['best_score'], 0.1, places=2)
        self.assertIn('crypto', stats['category_breakdown'])
        self.assertEqual(stats['category_breakdown']['crypto']['count'], 2)

    def test_rank_and_cap(self):
        """Test ranking and capping logic"""
        candidates = [
            {'score': 0.1, 'category': 'crypto'},
            {'score': 0.09, 'category': 'crypto'},
            {'score': 0.08, 'category': 'sports'},
            {'score': 0.01, 'category': 'other'},  # Below threshold
        ]

        config = ScoringConfig(
            min_score_threshold=0.02,
            max_candidates_global=10,
            max_candidates_per_category=2
        )

        result = rank_and_cap_candidates(candidates, config)

        # Should filter out score=0.01
        self.assertEqual(len(result), 3)
        # Should be sorted by score DESC
        self.assertEqual(result[0]['score'], 0.1)


if __name__ == '__main__':
    unittest.main()
