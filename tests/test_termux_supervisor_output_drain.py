"""ManagedDaemon must continuously drain child output and retain bounded logs."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import scripts.termux_supervisor as supervisor


class ManagedDaemonOutputDrainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        self.original_repo = supervisor.REPO_ROOT
        self.original_log_dir = supervisor.LOG_DIR
        self.original_max_size = supervisor.RotatingLog.MAX_LOG_SIZE
        self.original_max_files = supervisor.RotatingLog.MAX_LOG_FILES
        supervisor.REPO_ROOT = self.repo
        supervisor.LOG_DIR = self.repo / "logs"

    def tearDown(self):
        supervisor.REPO_ROOT = self.original_repo
        supervisor.LOG_DIR = self.original_log_dir
        supervisor.RotatingLog.MAX_LOG_SIZE = self.original_max_size
        supervisor.RotatingLog.MAX_LOG_FILES = self.original_max_files
        self.temp.cleanup()

    def start_child(self, script_text):
        script = self.repo / "noisy_child.py"
        marker = self.repo / "progress.marker"
        script.write_text(script_text.replace("__MARKER__", repr(str(marker))))
        daemon = supervisor.ManagedDaemon(
            "noisy",
            {"script": script},
            {"daemons": {}},
        )
        daemon.start()
        self.assertIsNotNone(daemon.process)
        return daemon, marker

    def wait_for_marker(self, marker, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if marker.exists():
                return True
            time.sleep(0.025)
        return marker.exists()

    def stop_child(self, daemon):
        process = daemon.process
        if process is not None and process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + 3
        while daemon.process is not None and time.monotonic() < deadline:
            daemon.poll()  # Uses WNOWAIT; do not reap the leader before group cleanup.
            if daemon.process is not None:
                time.sleep(0.01)
        if daemon.output_thread is not None:
            daemon.output_thread.join(timeout=2)

    def test_stdout_and_stderr_are_drained_while_child_remains_alive(self):
        script = """
import sys, time
sys.stdout.write('O' * (2 * 1024 * 1024))
sys.stdout.flush()
sys.stderr.write('E' * (2 * 1024 * 1024))
sys.stderr.flush()
open(__MARKER__, 'w').write('continued')
time.sleep(10)
"""
        daemon, marker = self.start_child(script)
        try:
            self.assertTrue(self.wait_for_marker(marker), "child blocked writing to supervisor pipe")
            self.assertIsNone(daemon.process.poll())
            log_path = supervisor.LOG_DIR / "noisy.log"
            self.assertTrue(log_path.exists())
            output = log_path.read_text()
            self.assertIn("O", output)
            self.assertIn("E", output)
            self.assertIsNone(daemon.poll())
        finally:
            self.stop_child(daemon)

    def test_small_output_is_persisted_before_child_exits(self):
        script = """
import sys, time
sys.stdout.write('small-output\\n')
sys.stdout.flush()
open(__MARKER__, 'w').write('written')
time.sleep(10)
"""
        daemon, marker = self.start_child(script)
        try:
            self.assertTrue(self.wait_for_marker(marker), "child did not publish output marker")
            log_path = supervisor.LOG_DIR / "noisy.log"
            deadline = time.monotonic() + 1
            while time.monotonic() < deadline:
                if log_path.exists() and "small-output" in log_path.read_text():
                    break
                time.sleep(0.01)
            else:
                self.fail("small output remained buffered until child exit")
            self.assertIsNone(daemon.process.poll())
        finally:
            self.stop_child(daemon)

    def test_continuous_output_uses_bounded_rotating_retention(self):
        supervisor.RotatingLog.MAX_LOG_SIZE = 256 * 1024
        supervisor.RotatingLog.MAX_LOG_FILES = 2
        script = """
import sys, time
sys.stdout.write('Z' * (8 * 1024 * 1024))
sys.stdout.flush()
open(__MARKER__, 'w').write('continued')
time.sleep(10)
"""
        daemon, marker = self.start_child(script)
        try:
            self.assertTrue(self.wait_for_marker(marker), "child blocked before completing output")
            time.sleep(0.1)
        finally:
            self.stop_child(daemon)

        files = list(supervisor.LOG_DIR.glob("noisy.log*"))
        self.assertGreaterEqual(len(files), 1)
        self.assertLessEqual(len(files), 3)
        total_bytes = sum(path.stat().st_size for path in files)
        self.assertLessEqual(total_bytes, 3 * (256 * 1024 + 4096))
        self.assertTrue(all(path.stat().st_size <= 256 * 1024 + 4096 for path in files))


    def test_log_write_failure_does_not_stop_pipe_draining(self):
        script = """
import sys, time
sys.stdout.write('X' * (2 * 1024 * 1024))
sys.stdout.flush()
sys.stderr.write('Y' * (2 * 1024 * 1024))
sys.stderr.flush()
open(__MARKER__, 'w').write('continued')
time.sleep(10)
"""
        with mock.patch("builtins.open", side_effect=OSError("simulated disk full")), \
             mock.patch.object(supervisor.log, "warning") as warning:
            daemon, marker = self.start_child(script)
            try:
                self.assertTrue(
                    self.wait_for_marker(marker),
                    "child blocked because log persistence failure stopped pipe draining",
                )
                self.assertIsNone(daemon.process.poll())
                self.assertTrue(daemon.output_thread.is_alive())
                warning.assert_called_once()
            finally:
                self.stop_child(daemon)


if __name__ == "__main__":
    unittest.main()
