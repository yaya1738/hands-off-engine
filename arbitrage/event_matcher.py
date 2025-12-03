"""
Cross-Platform Event Matcher
============================

Matches the same events across different prediction market platforms.

For arbitrage to work, we need to identify when Polymarket and Kalshi
(and potentially sportsbooks) are offering contracts on the exact same
underlying event.

Matching strategies:
1. Exact match: Identical or nearly identical question text
2. Semantic match: Same meaning with different wording
3. Entity match: Same entities (candidates, teams, dates)
4. Manual mapping: Pre-defined market ID pairs
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

from .types import Platform, PredictionMarket, MatchedEvent

logger = logging.getLogger(__name__)


class EventMatcher:
    """
    Matches prediction markets across platforms.

    Uses multiple matching strategies to identify the same event
    being traded on different platforms.
    """

    # Known entity mappings (different names for same thing)
    ENTITY_ALIASES = {
        # Politicians
        'trump': ['donald trump', 'donald j trump', 'djt', 'trump'],
        'biden': ['joe biden', 'joseph biden', 'biden'],
        'harris': ['kamala harris', 'harris'],
        'desantis': ['ron desantis', 'desantis'],

        # Crypto
        'bitcoin': ['btc', 'bitcoin', 'xbt'],
        'ethereum': ['eth', 'ethereum', 'ether'],

        # Sports leagues
        'nfl': ['nfl', 'national football league'],
        'nba': ['nba', 'national basketball association'],
        'mlb': ['mlb', 'major league baseball'],
        'super_bowl': ['super bowl', 'superbowl', 'sb'],
    }

    # Question patterns for normalization
    QUESTION_PATTERNS = [
        # "Will X happen?" -> "X happen"
        (r'^will\s+', ''),
        (r'\?$', ''),
        (r'^(who will|what will|when will)\s+', ''),
        # Dates - normalize format
        (r'(\d{1,2})/(\d{1,2})/(\d{2,4})', r'\1-\2-\3'),
        # Common words to remove
        (r'\b(the|a|an|in|on|at|by|for|to)\b', ' '),
        # Multiple spaces
        (r'\s+', ' '),
    ]

    def __init__(
        self,
        manual_mappings_path: Optional[Path] = None,
        match_threshold: float = 0.85,
    ):
        """
        Initialize the event matcher.

        Args:
            manual_mappings_path: Path to JSON file with pre-defined market mappings
            match_threshold: Minimum similarity score for automatic matching (0-1)
        """
        self.match_threshold = match_threshold
        self.manual_mappings: Dict[str, str] = {}

        if manual_mappings_path and manual_mappings_path.exists():
            self._load_manual_mappings(manual_mappings_path)

        # Build reverse alias lookup
        self._alias_lookup: Dict[str, str] = {}
        for canonical, aliases in self.ENTITY_ALIASES.items():
            for alias in aliases:
                self._alias_lookup[alias.lower()] = canonical

    def _load_manual_mappings(self, path: Path) -> None:
        """Load pre-defined market ID mappings"""
        try:
            with open(path, 'r') as f:
                self.manual_mappings = json.load(f)
            logger.info(f"Loaded {len(self.manual_mappings)} manual mappings")
        except Exception as e:
            logger.warning(f"Failed to load manual mappings: {e}")

    def match_markets(
        self,
        markets_by_platform: Dict[Platform, List[PredictionMarket]],
    ) -> List[MatchedEvent]:
        """
        Match markets across platforms.

        Args:
            markets_by_platform: Dict mapping Platform to list of markets

        Returns:
            List of MatchedEvent objects (same event across 2+ platforms)
        """
        matched_events: List[MatchedEvent] = []
        used_market_ids: Set[str] = set()

        platforms = list(markets_by_platform.keys())

        # For each pair of platforms, find matching markets
        for i, platform_a in enumerate(platforms):
            for platform_b in platforms[i + 1:]:
                markets_a = markets_by_platform[platform_a]
                markets_b = markets_by_platform[platform_b]

                for market_a in markets_a:
                    if market_a.market_id in used_market_ids:
                        continue

                    best_match = None
                    best_score = 0

                    for market_b in markets_b:
                        if market_b.market_id in used_market_ids:
                            continue

                        score, method = self._calculate_match_score(market_a, market_b)

                        if score > best_score and score >= self.match_threshold:
                            best_score = score
                            best_match = (market_b, method)

                    if best_match:
                        market_b, method = best_match

                        # Check if this extends an existing match
                        extended = False
                        for event in matched_events:
                            if market_a in event.markets:
                                event.markets.append(market_b)
                                extended = True
                                break
                            elif market_b in event.markets:
                                event.markets.append(market_a)
                                extended = True
                                break

                        if not extended:
                            # Create new matched event
                            event_id = self._generate_event_id(market_a.question)
                            matched_event = MatchedEvent(
                                event_id=event_id,
                                canonical_question=self._canonicalize_question(market_a.question),
                                markets=[market_a, market_b],
                                match_confidence=best_score,
                                match_method=method,
                                category=self._infer_category(market_a.question),
                                created_at=datetime.now(timezone.utc),
                            )
                            matched_events.append(matched_event)

                        used_market_ids.add(market_a.market_id)
                        used_market_ids.add(market_b.market_id)

        logger.info(f"Found {len(matched_events)} matched events across {len(platforms)} platforms")
        return matched_events

    def _calculate_match_score(
        self,
        market_a: PredictionMarket,
        market_b: PredictionMarket,
    ) -> Tuple[float, str]:
        """
        Calculate how well two markets match.

        Returns:
            Tuple of (score 0-1, matching_method)
        """
        # Check manual mapping first
        key_a = f"{market_a.platform.value}:{market_a.market_id}"
        key_b = f"{market_b.platform.value}:{market_b.market_id}"

        if self.manual_mappings.get(key_a) == key_b:
            return 1.0, "manual"
        if self.manual_mappings.get(key_b) == key_a:
            return 1.0, "manual"

        # Normalize questions
        q_a = self._normalize_question(market_a.question)
        q_b = self._normalize_question(market_b.question)

        # Exact match after normalization
        if q_a == q_b:
            return 0.99, "exact"

        # Sequence matching (fuzzy string similarity)
        seq_score = SequenceMatcher(None, q_a, q_b).ratio()

        # Entity matching boost
        entities_a = self._extract_entities(market_a.question)
        entities_b = self._extract_entities(market_b.question)
        entity_overlap = len(entities_a & entities_b) / max(len(entities_a | entities_b), 1)

        # Combined score (weighted)
        combined_score = (seq_score * 0.7) + (entity_overlap * 0.3)

        # Boost if close times match
        if market_a.closes_at and market_b.closes_at:
            time_diff = abs((market_a.closes_at - market_b.closes_at).total_seconds())
            if time_diff < 86400:  # Within 24 hours
                combined_score *= 1.1
            elif time_diff < 604800:  # Within a week
                combined_score *= 1.05

        method = "fuzzy" if seq_score > entity_overlap else "entity"

        return min(combined_score, 1.0), method

    def _normalize_question(self, question: str) -> str:
        """Normalize question text for comparison"""
        text = question.lower().strip()

        for pattern, replacement in self.QUESTION_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Replace aliases with canonical names
        words = text.split()
        normalized_words = []
        for word in words:
            canonical = self._alias_lookup.get(word.lower(), word)
            normalized_words.append(canonical)

        return ' '.join(normalized_words).strip()

    def _canonicalize_question(self, question: str) -> str:
        """Create canonical form of question (less aggressive than normalize)"""
        text = question.strip()

        # Just clean up punctuation and whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.rstrip('?').strip()

        return text

    def _extract_entities(self, text: str) -> Set[str]:
        """Extract key entities from question text"""
        entities = set()
        text_lower = text.lower()

        # Check against known aliases
        for canonical, aliases in self.ENTITY_ALIASES.items():
            for alias in aliases:
                if alias.lower() in text_lower:
                    entities.add(canonical)
                    break

        # Extract numbers/dates (likely significant)
        numbers = re.findall(r'\b\d{4}\b', text)  # Years
        entities.update(numbers)

        # Extract percentages
        percentages = re.findall(r'\b\d+(?:\.\d+)?%', text)
        entities.update(percentages)

        # Extract dollar amounts
        dollars = re.findall(r'\$[\d,]+(?:\.\d{2})?', text)
        entities.update(dollars)

        return entities

    def _infer_category(self, question: str) -> Optional[str]:
        """Infer market category from question text"""
        text_lower = question.lower()

        # Politics
        politics_keywords = ['president', 'election', 'vote', 'congress', 'senate', 'governor']
        if any(kw in text_lower for kw in politics_keywords):
            return 'politics'

        # Sports
        sports_keywords = ['win', 'championship', 'super bowl', 'nfl', 'nba', 'mlb', 'playoffs']
        if any(kw in text_lower for kw in sports_keywords):
            return 'sports'

        # Crypto
        crypto_keywords = ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'price']
        if any(kw in text_lower for kw in crypto_keywords):
            return 'crypto'

        # Economics
        econ_keywords = ['fed', 'interest rate', 'inflation', 'gdp', 'unemployment']
        if any(kw in text_lower for kw in econ_keywords):
            return 'economics'

        return None

    def _generate_event_id(self, question: str) -> str:
        """Generate unique event ID from question"""
        normalized = self._normalize_question(question)
        hash_input = normalized.encode('utf-8')
        return hashlib.sha256(hash_input).hexdigest()[:16]

    def add_manual_mapping(
        self,
        platform_a: Platform,
        market_id_a: str,
        platform_b: Platform,
        market_id_b: str,
    ) -> None:
        """Add a manual market mapping"""
        key_a = f"{platform_a.value}:{market_id_a}"
        key_b = f"{platform_b.value}:{market_id_b}"

        self.manual_mappings[key_a] = key_b
        self.manual_mappings[key_b] = key_a

        logger.info(f"Added manual mapping: {key_a} <-> {key_b}")

    def save_manual_mappings(self, path: Path) -> None:
        """Save manual mappings to file"""
        with open(path, 'w') as f:
            json.dump(self.manual_mappings, f, indent=2)
