"""
Test fixtures for Hands-Off Engine

This module provides common fixtures and utilities for testing.
"""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent


def load_fixture(filename: str) -> dict:
    """Load a JSON fixture file."""
    fixture_path = FIXTURES_DIR / filename
    with open(fixture_path) as f:
        return json.load(f)


def get_sample_model_data() -> dict:
    """Load sample polymarket model data."""
    return load_fixture("sample_polymarket_model.json")


def get_mock_api_response() -> dict:
    """Load mock API response."""
    return load_fixture("mock_api_response.json")


def get_test_config() -> dict:
    """Load test configuration."""
    return load_fixture("test_config.json")
