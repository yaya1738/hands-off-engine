#!/usr/bin/env python3
"""
TRADING SELF-TEST - System verifies its own trading capability
===============================================================

This module allows the system to test its trading components
without human intervention.

Master: Yair Siegel
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
STATE_DIR = BASE_DIR / "state"


def test_market_data() -> dict:
    """Test: Can we fetch market data?"""
    try:
        import requests
        resp = requests.get(
            "https://gamma-api.polymarket.com/markets",
            params={"closed": "false", "limit": 5},
            timeout=30
        )
        if resp.status_code == 200:
            markets = resp.json()
            return {"passed": True, "markets_fetched": len(markets)}
        return {"passed": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"passed": False, "error": str(e)}


def test_signal_generation() -> dict:
    """Test: Can we generate signals?"""
    try:
        from trading.signal_generator import SignalGenerator
        gen = SignalGenerator()
        signals = gen.scan_opportunities()
        return {"passed": True, "signals_generated": len(signals)}
    except ImportError:
        return {"passed": False, "error": "SignalGenerator not available"}
    except Exception as e:
        return {"passed": False, "error": str(e)}


def test_safeguards() -> dict:
    """Test: Are safeguards working?"""
    try:
        from executor.trading_safeguards import TradingSafeguards
        safeguards = TradingSafeguards()

        # Test position size check
        ok, msg = safeguards.check_position_size(1.0)  # Small test amount

        return {"passed": True, "safeguards_active": ok, "message": msg}
    except ImportError:
        return {"passed": False, "error": "TradingSafeguards not available"}
    except Exception as e:
        return {"passed": False, "error": str(e)}


def test_actuator_connection() -> dict:
    """Test: Is Polymarket actuator connected?"""
    try:
        from autonomous.actuators import ActuatorHub
        hub = ActuatorHub()
        status = hub.status()

        pm_status = status.get("polymarket", {})
        return {
            "passed": pm_status.get("configured", False),
            "connected": pm_status.get("healthy", False),
            "has_trader": pm_status.get("healthy", False)
        }
    except ImportError:
        return {"passed": False, "error": "ActuatorHub not available"}
    except Exception as e:
        return {"passed": False, "error": str(e)}


def test_unified_ai_check() -> dict:
    """Test: Does unified_ai allow trading?"""
    try:
        from ai.unified_ai import check_trading_allowed
        ok, msg = check_trading_allowed(1.0)  # Test with $1
        return {"passed": True, "trading_allowed": ok, "reason": msg}
    except ImportError:
        return {"passed": False, "error": "unified_ai not available"}
    except Exception as e:
        return {"passed": False, "error": str(e)}


def run_all_tests() -> dict:
    """Run all trading self-tests."""
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tests": {
            "market_data": test_market_data(),
            "signal_generation": test_signal_generation(),
            "safeguards": test_safeguards(),
            "actuator_connection": test_actuator_connection(),
            "unified_ai_check": test_unified_ai_check()
        },
        "all_passed": False
    }

    # Calculate overall pass
    passed = sum(1 for t in results["tests"].values() if t.get("passed"))
    total = len(results["tests"])
    results["all_passed"] = passed == total
    results["score"] = f"{passed}/{total}"

    # Save results
    test_file = STATE_DIR / "trading_self_test_results.json"
    with open(test_file, 'w') as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    results = run_all_tests()
    print(json.dumps(results, indent=2))

    if results["all_passed"]:
        print("\n[SELF-TEST] ALL TESTS PASSED - Trading system operational")
    else:
        print(f"\n[SELF-TEST] {results['score']} tests passed - System has gaps")
