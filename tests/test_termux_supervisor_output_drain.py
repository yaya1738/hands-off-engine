"""ManagedDaemon must continuously drain child output and retain bounded logs."""
import sys
import time
from pathlib import Path

import scripts.termux_supervisor as supervisor


def _start_child(tmp_path, monkeypatch, script_text):
    repo = tmp_path / "repo"
    repo.mkdir()
    script = repo / "noisy_child.py"
    marker = repo / "progress.marker"
    script.write_text(script_text.replace("__MARKER__", repr(str(marker))))
    monkeypatch.setattr(supervisor, "REPO_ROOT", repo)
    monkeypatch.setattr(supervisor, "LOG_DIR", repo / "logs")
    daemon = supervisor.ManagedDaemon(
        "noisy",
        {"script": script},
        {"daemons": {}},
    )
    daemon.start()
    assert daemon.process is not None
    return daemon, marker


def _wait_for_marker(marker, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if marker.exists():
            return True
        time.sleep(0.025)
    return marker.exists()


def _stop_child(daemon):
    process = daemon.process
    if process is not None and process.poll() is None:
        process.kill()
        process.wait(timeout=3)
    if daemon.process is not None:
        daemon.poll()
    if daemon.output_thread is not None:
        daemon.output_thread.join(timeout=2)


def test_stdout_and_stderr_are_drained_while_child_remains_alive(tmp_path, monkeypatch):
    script = """
import sys, time
sys.stdout.write('O' * (2 * 1024 * 1024))
sys.stdout.flush()
sys.stderr.write('E' * (2 * 1024 * 1024))
sys.stderr.flush()
open(__MARKER__, 'w').write('continued')
time.sleep(10)
"""
    daemon, marker = _start_child(tmp_path, monkeypatch, script)
    try:
        assert _wait_for_marker(marker), "child blocked writing to supervisor pipe"
        assert daemon.process.poll() is None
        log_path = supervisor.LOG_DIR / "noisy.log"
        assert log_path.exists()
        output = log_path.read_text()
        assert "O" in output
        assert "E" in output
        assert daemon.poll() is None
    finally:
        _stop_child(daemon)


def test_continuous_output_uses_bounded_rotating_retention(tmp_path, monkeypatch):
    monkeypatch.setattr(supervisor.RotatingLog, "MAX_LOG_SIZE", 256 * 1024)
    monkeypatch.setattr(supervisor.RotatingLog, "MAX_LOG_FILES", 2)
    script = """
import sys, time
sys.stdout.write('Z' * (8 * 1024 * 1024))
sys.stdout.flush()
open(__MARKER__, 'w').write('continued')
time.sleep(10)
"""
    daemon, marker = _start_child(tmp_path, monkeypatch, script)
    try:
        assert _wait_for_marker(marker), "child blocked before completing output"
        time.sleep(0.1)
    finally:
        _stop_child(daemon)

    files = list(supervisor.LOG_DIR.glob("noisy.log*"))
    assert 1 <= len(files) <= 3
    total_bytes = sum(path.stat().st_size for path in files)
    assert total_bytes <= 3 * (256 * 1024 + 4096)
    assert all(path.stat().st_size <= 256 * 1024 + 4096 for path in files)
