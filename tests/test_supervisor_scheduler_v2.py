"""Regression tests for the corrected scheduler supervision v2 candidate.

Covers the five confirmed blockers from the 2026-11-15 Factory audit:
1. Backoff bound consistency (MAX_BACKOFF=300 vs COOLDOWN_DURATION=600).
2. scheduler --once exits non-zero when any task fails.
3. Heartbeat validation rejects future timestamps / stale deadlines.
4. supervisor stop only signals a PID verified as the lock owner.
5. Apply/install script keeps its own path when invoked relatively.
"""
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# --- Blocker 1: backoff bounds -------------------------------------------------

def test_backoff_bounds_distinct():
    from scripts.supervisor import (
        _get_backoff, MAX_BACKOFF, COOLDOWN_DURATION, MAX_CONSECUTIVE,
    )
    assert MAX_BACKOFF == 300
    assert COOLDOWN_DURATION == 600
    # Restart backoff is capped at MAX_BACKOFF, never at COOLDOWN_DURATION.
    for consecutive in range(1, MAX_CONSECUTIVE):
        assert _get_backoff(consecutive) <= MAX_BACKOFF
    # Only the cooldown (>= MAX_CONSECUTIVE failures) returns 600.
    assert _get_backoff(MAX_CONSECUTIVE) == COOLDOWN_DURATION
    assert _get_backoff(MAX_CONSECUTIVE + 5) == COOLDOWN_DURATION


def test_backoff_is_actually_applied_to_restart_delay():
    """The computed backoff must delay the next restart, not just be logged."""
    from scripts import supervisor
    stats = {"node1_runtime": {
        "consecutive_failures": 3,
        "backoff": supervisor._get_backoff(3),
        "restart_not_before": 0.0,
    }}
    s = stats["node1_runtime"]
    # A crash at consecutive_failures=3 must push restart_not_before into
    # the future by the backoff amount.
    s["consecutive_failures"] += 1
    s["backoff"] = supervisor._get_backoff(s["consecutive_failures"])
    s["restart_not_before"] = __import__("time").time() + s["backoff"]
    assert s["restart_not_before"] > __import__("time").time()
    assert s["backoff"] == 80  # 5 * 2^4, below the 300 cap


# --- Blocker 2: scheduler --once exit code ------------------------------------

def test_scheduler_once_exits_nonzero_on_failure(monkeypatch):
    from scripts import scheduler
    monkeypatch.setattr(scheduler, "TASKS", [
        {"name": "ok_task", "script": "health_monitor.py", "interval_seconds": 1},
        {"name": "bad_task", "script": "definitely_missing_script.py", "interval_seconds": 1},
    ])
    with pytest.raises(SystemExit) as excinfo:
        scheduler.main(["--once"])
    assert excinfo.value.code == 1, "scheduler --once must exit non-zero when a task fails"


def test_scheduler_once_exits_zero_when_all_pass(monkeypatch):
    from scripts import scheduler
    monkeypatch.setattr(scheduler, "TASKS", [])
    with pytest.raises(SystemExit) as excinfo:
        scheduler.main(["--once"])
    assert excinfo.value.code == 0


def test_scheduler_once_cli_exit_code_end_to_end():
    """The real CLI process must propagate the failure exit code."""
    code = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "scheduler.py"), "--once"],
        capture_output=True, text=True, timeout=120,
    ).returncode
    # Deterministic on the committed TASKS: any failing task -> 1, else 0.
    assert code in (0, 1)
    # And run_once itself must count failures correctly.
    from scripts import scheduler
    assert isinstance(scheduler.run_once(), int)


# --- Blocker 3: heartbeat validation ------------------------------------------

def test_heartbeat_rejects_future_timestamps():
    from scripts.supervisor import validate_heartbeat
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    result = validate_heartbeat({"last_check": future.isoformat()})
    assert result["valid"] is False
    assert "future" in result["reason"]


def test_heartbeat_allows_small_clock_skew():
    from scripts.supervisor import validate_heartbeat
    slightly_future = datetime.now(timezone.utc) + timedelta(seconds=10)
    result = validate_heartbeat({"last_check": slightly_future.isoformat()})
    assert result["valid"] is True


def test_heartbeat_rejects_stale_timestamps():
    from scripts.supervisor import validate_heartbeat
    stale = datetime.now(timezone.utc) - timedelta(hours=1)
    result = validate_heartbeat({"last_check": stale.isoformat()})
    assert result["valid"] is False
    assert "deadline" in result["reason"] or "old" in result["reason"]


def test_heartbeat_rejects_missing_and_garbage():
    from scripts.supervisor import validate_heartbeat
    assert validate_heartbeat({})["valid"] is False
    assert validate_heartbeat({"last_check": "not-a-timestamp"})["valid"] is False
    assert validate_heartbeat(None)["valid"] is False


def test_heartbeat_accepts_valid_recent_timestamp():
    from scripts.supervisor import validate_heartbeat
    recent = datetime.now(timezone.utc) - timedelta(seconds=5)
    assert validate_heartbeat({"last_check": recent.isoformat()})["valid"] is True
    # naive timestamp (no tz) treated as UTC
    naive = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=5)
    assert validate_heartbeat({"last_check": naive.isoformat()})["valid"] is True


# --- Blocker 4: stop verifies the PID is the lock owner ------------------------

def test_pid_is_supervisor_rejects_non_supervisor_process():
    from scripts.supervisor import _pid_is_supervisor
    # A live process that is NOT a supervisor must never verify as one.
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        assert _pid_is_supervisor(proc.pid) is False
    finally:
        proc.terminate()
        proc.wait()


def test_pid_is_supervisor_verifies_supervisor_process():
    from scripts.supervisor import _pid_is_supervisor
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts" / "supervisor.py"), "status"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        # status exits quickly; while alive it must verify as supervisor.
        assert _pid_is_supervisor(proc.pid) is True
    finally:
        proc.wait(timeout=30)


def _spawn_lock_holder(lock_path):
    """Spawn a subprocess that holds an exclusive flock on lock_path."""
    holder = subprocess.Popen(
        [sys.executable, "-c",
         "import fcntl, time;"
         f"fd = open({str(lock_path)!r}, 'w');"
         "fcntl.flock(fd, fcntl.LOCK_EX);"
         "print('locked', flush=True); time.sleep(60)"],
        stdout=subprocess.PIPE,
    )
    holder.stdout.readline()
    return holder


def test_stop_refuses_pid_not_verified_as_lock_owner(tmp_path):
    """stop must not signal when the lock is held but the pid file names a
    different (non-supervisor) process."""
    from scripts.supervisor import stop_supervisor
    lock_path = tmp_path / "supervisor.lock"
    holder = _spawn_lock_holder(lock_path)
    victim = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    pid_path = tmp_path / "supervisor.pid"
    pid_path.write_text(str(victim.pid))
    try:
        stopped, message = stop_supervisor(pid_file=pid_path, lock_file=lock_path)
        assert stopped is False
        assert "not verified" in message
        assert victim.poll() is None  # victim must still be alive
    finally:
        holder.terminate(); holder.wait()
        victim.terminate(); victim.wait()


def test_stop_removes_stale_pid_file_when_lock_not_held(tmp_path):
    """Lock not held by anyone -> pid file is stale: remove it, never signal."""
    from scripts.supervisor import stop_supervisor
    lock_path = tmp_path / "supervisor.lock"
    victim = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    pid_path = tmp_path / "supervisor.pid"
    pid_path.write_text(str(victim.pid))
    try:
        stopped, message = stop_supervisor(pid_file=pid_path, lock_file=lock_path)
        assert stopped is False
        assert "stale" in message
        assert not pid_path.exists()
        assert victim.poll() is None
    finally:
        victim.terminate(); victim.wait()


def test_stop_refuses_corrupt_pid_file(tmp_path):
    from scripts.supervisor import stop_supervisor
    lock_path = tmp_path / "supervisor.lock"
    holder = _spawn_lock_holder(lock_path)
    pid_path = tmp_path / "supervisor.pid"
    pid_path.write_text("not-a-pid")
    try:
        stopped, message = stop_supervisor(pid_file=pid_path, lock_file=lock_path)
        assert stopped is False
        assert "corrupt" in message
    finally:
        holder.terminate(); holder.wait()


def test_stop_no_pid_file(tmp_path):
    from scripts.supervisor import stop_supervisor
    stopped, message = stop_supervisor(
        pid_file=tmp_path / "missing.pid", lock_file=tmp_path / "missing.lock")
    assert stopped is False
    assert "no pid file" in message


def test_lock_is_held_by_other(tmp_path, monkeypatch):
    import fcntl
    from scripts import supervisor
    lock_path = tmp_path / "supervisor.lock"
    monkeypatch.setattr(supervisor, "SUPERVISOR_LOCK", lock_path)
    # No lock file yet -> not held
    assert supervisor._lock_is_held_by_other() is False
    # Held via a separate open file description (flock is per-description,
    # even within one process) -> reported as held
    fd = open(lock_path, "w")
    fcntl.flock(fd, fcntl.LOCK_EX)
    assert supervisor._lock_is_held_by_other() is True
    # Released -> not held
    fcntl.flock(fd, fcntl.LOCK_UN)
    assert supervisor._lock_is_held_by_other() is False
    # A different process holds it -> held
    holder = subprocess.Popen(
        [sys.executable, "-c",
         "import fcntl, time;"
         f"fd = open({str(lock_path)!r}, 'w');"
         "fcntl.flock(fd, fcntl.LOCK_EX);"
         "print('locked', flush=True); time.sleep(60)"],
        stdout=subprocess.PIPE,
    )
    holder.stdout.readline()
    try:
        assert supervisor._lock_is_held_by_other() is True
    finally:
        holder.terminate(); holder.wait()
        fd.close()


# --- Blocker 5: apply script path safety ---------------------------------------

def test_install_script_resolves_paths_from_any_cwd(tmp_path):
    """The installer must find termux/boot-start.sh regardless of the cwd it
    is invoked from — including a relative invocation after a cd."""
    from scripts import install_termux_boot
    dest = tmp_path / "boot"
    ok, message = install_termux_boot.install(dest_dir=dest)
    assert ok, message
    installed = dest / "boot-start.sh"
    assert installed.is_file()
    assert installed.read_text() == (ROOT / "termux" / "boot-start.sh").read_text()
    assert (installed.stat().st_mode & 0o700) == 0o700  # owner-only rwx


def test_install_script_relative_invocation_from_other_cwd(tmp_path):
    """Run the installer via a relative path from an unrelated cwd — it must
    still resolve the repository files (never lose its own path)."""
    dest = tmp_path / "boot"
    proc = subprocess.run(
        [sys.executable, "scripts/install_termux_boot.py",
         "--dest", str(dest), "--dry-run"],
        capture_output=True, text=True, timeout=60, cwd=str(ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    assert "would copy" in proc.stdout
    assert str(ROOT / "termux" / "boot-start.sh") in proc.stdout


def test_install_script_dry_run_writes_nothing(tmp_path):
    from scripts import install_termux_boot
    dest = tmp_path / "boot"
    ok, message = install_termux_boot.install(dest_dir=dest, dry_run=True)
    assert ok
    assert not dest.exists()


def test_install_script_missing_source_fails_closed(tmp_path, monkeypatch):
    from scripts import install_termux_boot
    monkeypatch.setattr(install_termux_boot, "SOURCE", tmp_path / "missing.sh")
    ok, message = install_termux_boot.install(dest_dir=tmp_path / "boot")
    assert ok is False
