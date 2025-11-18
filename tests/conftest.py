"""Pytest fixtures and shared test utilities"""
import json
import pytest
from pathlib import Path


@pytest.fixture
def sample_markets():
    """Sample Polymarket data across all categories"""
    return {
        "markets": [
            {
                "id": "sports-001",
                "question": "Will the Lakers win the NBA championship?",
                "yes_price": 0.45,
                "no_price": 0.55,
                "volume": 100000,
                "closes_at": "2025-06-15T00:00:00Z"
            },
            {
                "id": "crypto-001",
                "question": "Will Bitcoin reach $100k in 2025?",
                "yes_price": 0.62,
                "no_price": 0.38,
                "volume": 500000,
                "closes_at": "2025-12-31T23:59:59Z"
            },
            {
                "id": "politics-001",
                "question": "Will the Senate pass the infrastructure bill?",
                "yes_price": 0.71,
                "no_price": 0.29,
                "volume": 250000,
                "closes_at": "2025-03-01T00:00:00Z"
            },
            {
                "id": "macro-001",
                "question": "Will the Fed raise interest rates in Q1 2025?",
                "yes_price": 0.58,
                "no_price": 0.42,
                "volume": 150000,
                "closes_at": "2025-04-01T00:00:00Z"
            },
            {
                "id": "other-001",
                "question": "Will it rain in Seattle tomorrow?",
                "yes_price": 0.50,
                "no_price": 0.50,
                "volume": 10000,
                "closes_at": "2025-01-20T00:00:00Z"
            }
        ]
    }


@pytest.fixture
def edge_case_markets():
    """Edge cases: missing fields, extreme prices, alternative field names"""
    return [
        # Missing price fields - should use defaults
        {"id": "missing-prices", "question": "Test market"},

        # No ID field - should generate one
        {"question": "No ID field", "yes_price": 0.5, "no_price": 0.5},

        # Extreme prices
        {"id": "extreme-price", "question": "Edge case", "yes_price": 0.99, "no_price": 0.01},

        # Empty question
        {"id": "empty-question", "question": "", "yes_price": 0.5, "no_price": 0.5},

        # Alternative field names
        {
            "id": "alt-fields",
            "title": "Uses title not question",
            "best_yes": 0.6,
            "best_no": 0.4,
            "end_date": "2025-12-31"
        },

        # Using _id instead of id
        {
            "_id": "underscore-id",
            "question": "Market with _id",
            "yes_price": 0.55,
            "no_price": 0.45
        },

        # String prices (should be converted to float)
        {
            "id": "string-prices",
            "question": "String prices",
            "yes_price": "0.65",
            "no_price": "0.35"
        },

        # Extra custom fields
        {
            "id": "extra-fields",
            "question": "Has custom fields",
            "yes_price": 0.5,
            "no_price": 0.5,
            "custom_field": "custom_value",
            "metadata": {"key": "value"}
        }
    ]


@pytest.fixture
def temp_state_dir(tmp_path):
    """Create temporary state directory for pm_model tests"""
    state_dir = tmp_path / "hands-off-out" / "state"
    state_dir.mkdir(parents=True)
    return state_dir


@pytest.fixture
def sample_compact_json(temp_state_dir, sample_markets):
    """Create a sample polymarket-compact.json file"""
    compact_file = temp_state_dir / "polymarket-compact.json"
    compact_file.write_text(json.dumps(sample_markets, indent=2))
    return compact_file
