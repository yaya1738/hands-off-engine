import json, sys, time, os, tempfile, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _make_supervisor():
    """Create a supervisor with temp state dir (no real daemons)."""
    from scripts.termux_supervisor import TermuxSupervisor, SUPERVISOR_STATE, SUPERVISOR_PID, SUPERVISOR_LOCK, STATE_DIR, DAEMONS
    import scripts.termux_supervisor as s
    tmp = Path(tempfile.mkdtemp())
    (tmp / "state").mkdir()
    (tmp / "state" / "logs").mkdir()

    # Override module-level paths
    s.STATE_DIR = tmp / "state"
    s.SUPERVISOR_STATE = tmp / "state" / "supervisor_state.json"
    s.SUPERVISOR_PID = tmp / "state" / "supervisor.pid"
    s.SUPERVISOR_LOCK = tmp / "state" / "supervisor.lock"
    s.LOG_DIR = tmp / "state" / "logs"

    sup = TermuxSupervisor()
    sup._tmp = tmp
    return sup


def test_one_instance_lock():
    """Duplicate supervisor cannot acquire the lock."""
    from scripts.termux_supervisor import SupervisorLock
    sup = _make_supervisor()
    import scripts.termux_supervisor as s
    s.SUPERVISOR_LOCK = sup._tmp / "state" / "supervisor.lock"
    s.SUPERVISOR_PID = sup._tmp / "state" / "supervisor.pid"

    lock1 = SupervisorLock()
    lock1.lock_path = s.SUPERVISOR_LOCK
    lock1.pid_path = s.SUPERVISOR_PID
    assert lock1.try_acquire()

    lock2 = SupervisorLock()
    lock2.lock_path = s.SUPERVISOR_LOCK
    lock2.pid_path = s.SUPERVISOR_PID
    assert not lock2.try_acquire(), "Second lock should fail"

    lock1.release()
    # After release, new lock should succeed
    lock3 = SupervisorLock()
    lock3.lock_path = s.SUPERVISOR_LOCK
    lock3.pid_path = s.SUPERVISOR_PID
    assert lock3.try_acquire()
    lock3.release()


def test_bounded_backoff():
    """Backoff increases exponentially, capped at MAX_BACKOFF."""
    from scripts.termux_supervisor import ManagedDaemon, MIN_BACKOFF, MAX_BACKOFF
    state = {"daemons": {}}
    config = {"script": Path("/dev/null"), "required": False}
    daemon = ManagedDaemon("test", config, state)

    for expected_count in range(8):
        assert daemon.state["restart_count"] == expected_count
        backoff = daemon.backoff_seconds()
        expected = min(MIN_BACKOFF * (2 ** expected_count), MAX_BACKOFF)
        assert backoff == expected, f"Backoff {backoff} != {expected} for count {expected_count}"
        daemon.record_crash()


def test_stable_resets_backoff():
    """After stable period, backoff resets to minimum."""
    from scripts.termux_supervisor import ManagedDaemon, MIN_BACKOFF
    state = {"daemons": {}}
    config = {"script": Path("/dev/null"), "required": False}
    daemon = ManagedDaemon("test", config, state)

    # Crash a few times
    for _ in range(5):
        daemon.record_crash()
    assert daemon.backoff_seconds() > MIN_BACKOFF

    # Stabilize
    daemon.record_stable()
    assert daemon.state["restart_count"] == 0
    assert daemon.backoff_seconds() == MIN_BACKOFF


def test_state_persistence():
    """Supervisor state survives save/load cycle."""
    from scripts.termux_supervisor import load_state, save_state
    tmp = Path(tempfile.mkdtemp())
    try:
        state_path = tmp / "supervisor_state.json"

        state = {"daemons": {"test": {"restart_count": 3, "total_restarts": 7}}}
        state_path.write_text(json.dumps(state))

        import scripts.termux_supervisor as s
        s.SUPERVISOR_STATE = state_path
        loaded = load_state()
        assert loaded["daemons"]["test"]["restart_count"] == 3
        assert loaded["daemons"]["test"]["total_restarts"] == 7
    finally:
        shutil.rmtree(tmp)


def test_rotating_log():
    """Log files rotate when exceeding max size."""
    from scripts.termux_supervisor import RotatingLog
    tmp = Path(tempfile.mkdtemp())
    import scripts.termux_supervisor as s
    s.LOG_DIR = Path(tmp)

    rl = RotatingLog("test_rotation")
    # Write enough to trigger rotation
    rl.MAX_LOG_SIZE = 100
    rl.MAX_LOG_FILES = 2

    for i in range(20):
        rl.write(f"Line {i}: {'x' * 20}\n")

    assert rl.log_path.exists()
    # Should have rotated
    rotated = list(tmp.glob("test_rotation.log.*"))
    assert len(rotated) > 0, f"Expected rotated files, got {tmp.listdir()}"
    shutil.rmtree(tmp)


def test_platform_boundary_documentation():
    """The module documents the platform boundary."""
    from scripts.termux_supervisor import TermuxSupervisor
    source = Path(TermuxSupervisor.__module__ and sys.modules["scripts.termux_supervisor"].__file__).read_text()
    assert "Android" in source
    assert "cannot guarantee" in source.lower() or "cannot guarantee" in source
    assert "survive" in source.lower()
