"""Termux supervisor must stop owned daemons before releasing its lock."""
import signal
import tempfile
import time
import unittest
from unittest import mock
from pathlib import Path

import scripts.termux_supervisor as supervisor


class TermuxSupervisorShutdownTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.original_repo = supervisor.REPO_ROOT
        self.original_log_dir = supervisor.LOG_DIR
        supervisor.REPO_ROOT = self.root
        supervisor.LOG_DIR = self.root / "logs"

    def tearDown(self):
        supervisor.REPO_ROOT = self.original_repo
        supervisor.LOG_DIR = self.original_log_dir
        self.temp.cleanup()

    def start_child(self, source):
        script = self.root / "child.py"
        script.write_text(source)
        daemon = supervisor.ManagedDaemon("child", {"script": script}, {"daemons": {}})
        daemon.start()
        self.assertIsNotNone(daemon.process)
        return daemon

    def test_signal_handler_defers_cleanup_to_bounded_shutdown(self):
        daemon = self.start_child("import time\ntime.sleep(30)\n")
        process = daemon.process
        runner = supervisor.TermuxSupervisor.__new__(supervisor.TermuxSupervisor)
        runner.running = True
        runner.daemons = {"child": daemon}

        runner._handle_signal(signal.SIGTERM, None)
        self.assertFalse(runner.running)
        self.assertIs(daemon.process, process)
        runner._shutdown_daemons(grace=1.0)

        self.assertIsNone(daemon.process)
        self.assertIsNone(daemon.output_thread)
        self.assertIsNotNone(process.returncode)

    def test_shutdown_reaps_already_exited_child_and_joins_reader(self):
        daemon = self.start_child("pass\n")
        process = daemon.process
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and process.poll() is None:
            time.sleep(0.01)
        self.assertIsNotNone(process.poll(), "child did not exit")

        runner = supervisor.TermuxSupervisor.__new__(supervisor.TermuxSupervisor)
        runner.daemons = {"child": daemon}
        runner._shutdown_daemons(grace=0.1)

        self.assertIsNone(daemon.process)
        self.assertIsNone(daemon.output_thread)
        self.assertIsNotNone(process.returncode)

    def test_run_releases_singleton_lock_only_after_child_cleanup(self):
        events = []

        class FakeLock:
            def try_acquire(self):
                return True

            def release(self):
                events.append("lock-release")

        runner = supervisor.TermuxSupervisor.__new__(supervisor.TermuxSupervisor)
        runner.lock = FakeLock()
        runner.state = {"supervisor": {}}
        runner.daemons = {}
        runner.running = True
        runner._loop = lambda: events.append("loop-exit")
        runner._shutdown_daemons = lambda: events.append("children-stopped")

        with mock.patch.object(supervisor.signal, "signal", return_value=signal.SIG_DFL), \
             mock.patch.object(supervisor, "save_state"):
            self.assertTrue(runner.run())

        self.assertLess(events.index("children-stopped"), events.index("lock-release"))

    def test_shutdown_kills_descendant_holding_pipe_after_leader_exits(self):
        marker = self.root / "descendant.pid"
        daemon = self.start_child(
            "import subprocess, sys\n"
            "child = (\"import os, signal, time; \"\n"
            "         \"signal.signal(signal.SIGTERM, signal.SIG_IGN); \"\n"
            f"         \"open({str(marker)!r}, 'w').write(str(os.getpid())); \"\n"
            "         \"time.sleep(30)\")\n"
            "subprocess.Popen([sys.executable, '-c', child])\n"
        )
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and not marker.exists():
            time.sleep(0.01)
        self.assertTrue(marker.exists(), "descendant did not start")
        descendant_pid = int(marker.read_text())
        leader = daemon.process
        self.assertEqual(supervisor._observe_exit_without_reaping(leader, timeout=2), (True, True))

        runner = supervisor.TermuxSupervisor.__new__(supervisor.TermuxSupervisor)
        runner.daemons = {"child": daemon}
        runner._shutdown_daemons(grace=0.05)

        self.assertIsNone(daemon.process)
        self.assertIsNone(daemon.output_thread)
        self.assertIsNotNone(leader.returncode)
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            try:
                stat = Path(f"/proc/{descendant_pid}/stat").read_text()
                state = stat.rsplit(")", 1)[1].split()[0]
            except OSError:
                # The process may disappear between opening /proc and reading it.
                break
            if state == "Z":
                break
            time.sleep(0.01)
        else:
            self.fail("descendant holding inherited output pipe survived shutdown")

    def test_poll_kills_descendant_holding_pipe_before_restart(self):
        marker = self.root / "poll-descendant.pid"
        daemon = self.start_child(
            "import subprocess, sys\n"
            "child = (\"import os, signal, time; \"\n"
            "         \"signal.signal(signal.SIGTERM, signal.SIG_IGN); \"\n"
            f"         \"open({str(marker)!r}, 'w').write(str(os.getpid())); \"\n"
            "         \"time.sleep(30)\")\n"
            "subprocess.Popen([sys.executable, '-c', child])\n"
        )
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and not marker.exists():
            time.sleep(0.01)
        self.assertTrue(marker.exists(), "descendant did not start")
        descendant_pid = int(marker.read_text())
        self.assertEqual(supervisor._observe_exit_without_reaping(daemon.process, timeout=2), (True, True))

        exit_code = daemon.poll()

        self.assertEqual(exit_code, 0)
        self.assertIsNone(daemon.process)
        self.assertIsNone(daemon.output_thread)
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            try:
                stat = Path(f"/proc/{descendant_pid}/stat").read_text()
                state = stat.rsplit(")", 1)[1].split()[0]
            except OSError:
                # The process may disappear between opening /proc and reading it.
                break
            if state == "Z":
                break
            time.sleep(0.01)
        else:
            self.fail("descendant survived natural daemon-exit cleanup")

    def test_poll_kills_descendant_even_when_it_redirects_output(self):
        marker = self.root / "redirected-descendant.pid"
        daemon = self.start_child(
            "import subprocess, sys\n"
            "child = (\"import os, signal, time; \"\n"
            "         \"signal.signal(signal.SIGTERM, signal.SIG_IGN); \"\n"
            f"         \"open({str(marker)!r}, 'w').write(str(os.getpid())); \"\n"
            "         \"time.sleep(30)\")\n"
            "subprocess.Popen([sys.executable, '-c', child], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and not marker.exists():
            time.sleep(0.01)
        self.assertTrue(marker.exists(), "redirected descendant did not start")
        descendant_pid = int(marker.read_text())
        self.assertEqual(supervisor._observe_exit_without_reaping(daemon.process, timeout=2), (True, True))

        self.assertEqual(daemon.poll(), 0)
        self.assertIsNone(daemon.process)
        self.assertIsNone(daemon.output_thread)
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            try:
                stat = Path(f"/proc/{descendant_pid}/stat").read_text()
                state = stat.rsplit(")", 1)[1].split()[0]
            except OSError:
                # The process may disappear between opening /proc and reading it.
                break
            if state == "Z":
                break
            time.sleep(0.01)
        else:
            self.fail("redirected descendant survived natural daemon-exit cleanup")

    def test_shutdown_kills_child_that_ignores_terminate(self):
        marker = self.root / "ready.marker"
        daemon = self.start_child(
            "import signal, time\nsignal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
            f"open({str(marker)!r}, 'w').write('ready')\ntime.sleep(30)\n"
        )
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and not marker.exists():
            time.sleep(0.01)
        self.assertTrue(marker.exists(), "child did not install SIGTERM handler")
        process = daemon.process
        runner = supervisor.TermuxSupervisor.__new__(supervisor.TermuxSupervisor)
        runner.daemons = {"child": daemon}

        runner._shutdown_daemons(grace=0.05)

        self.assertIsNone(daemon.process)
        self.assertIsNone(daemon.output_thread)
        self.assertEqual(process.returncode, -signal.SIGKILL)


if __name__ == "__main__":
    unittest.main()
