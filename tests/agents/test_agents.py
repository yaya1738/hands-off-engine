"""
Unit tests for self-healing agent system
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_alert_system():
    """Test alert system initialization and basic functionality"""
    from agents.alerts import AlertSystem, AlertLevel
    
    # Test initialization without Telegram credentials
    alerts = AlertSystem(bot_token=None, chat_id=None)
    assert alerts is not None
    
    # Test alert sending (will fallback to stderr without credentials)
    result = alerts.send_alert("Test alert", level=AlertLevel.INFO)
    # Should return False when no credentials
    assert result == False
    
    print("✓ Alert system tests passed")


def test_backup_system():
    """Test backup system"""
    from agents.backup import BackupSystem
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        state_dir = tmpdir / "state"
        backup_dir = tmpdir / "backups"
        state_dir.mkdir()
        
        # Create test state file
        test_file = state_dir / "test.json"
        test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Initialize backup system
        backup = BackupSystem(state_dir=state_dir, backup_dir=backup_dir)
        backup.backup_files = ["test.json"]
        
        # Test backup creation
        success = backup.create_daily_backup()
        assert success, "Backup should succeed"
        
        # Check backup exists
        today = datetime.now().strftime("%Y-%m-%d")
        backup_file = backup_dir / today / "test.json"
        assert backup_file.exists(), "Backup file should exist"
        
        # Test restoration
        test_file.unlink()  # Delete original
        success = backup.restore_from_backup("test.json")
        assert success, "Restoration should succeed"
        assert test_file.exists(), "Restored file should exist"
        
        # Verify content
        with open(test_file) as f:
            restored_data = json.load(f)
        assert restored_data == test_data, "Restored data should match"
    
    print("✓ Backup system tests passed")


def test_health_monitor():
    """Test health monitor initialization"""
    from agents.health_monitor import HealthMonitor, HealthStatus
    
    monitor = HealthMonitor()
    assert monitor is not None
    
    # Run health check (may fail on some checks, but should not crash)
    results = monitor.run_health_check()
    assert "timestamp" in results
    assert "overall_status" in results
    assert "checks" in results
    assert results["overall_status"] in [
        HealthStatus.HEALTHY,
        HealthStatus.WARNING,
        HealthStatus.CRITICAL,
        HealthStatus.UNKNOWN
    ]
    
    print("✓ Health monitor tests passed")


def test_self_healer():
    """Test self-healer initialization"""
    from agents.self_healer import SelfHealer
    
    healer = SelfHealer()
    assert healer is not None
    assert healer.config is not None
    assert "rules" in healer.config
    
    # Test finding rules
    rule = healer._find_matching_rule("process_not_running")
    assert rule is not None
    assert rule.get("action") == "restart"
    
    print("✓ Self-healer tests passed")


def test_watchdog():
    """Test watchdog initialization"""
    from agents.watchdog import Watchdog
    
    watchdog = Watchdog()
    assert watchdog is not None
    
    # Test heartbeat registration
    watchdog.register_heartbeat("test_agent")
    assert "test_agent" in watchdog.heartbeats
    
    print("✓ Watchdog tests passed")


def run_all_tests():
    """Run all tests"""
    print("Running self-healing agent system tests...\n")
    
    tests = [
        test_alert_system,
        test_backup_system,
        test_health_monitor,
        test_self_healer,
        test_watchdog
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} failed: {e}")
    
    print(f"\n{'='*50}")
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"Tests failed: {failed}/{len(tests)}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
