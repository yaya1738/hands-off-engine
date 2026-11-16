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

    def test_shutdown_does_not_signal_after_leader_is_reaped_during_grace(self):
        process = mock.Mock(pid=34568, returncode=None)
        daemon = mock.Mock()
        daemon.process = process
        daemon.output_thread = None
        runner = supervisor.TermuxSupervisor.__new__(supervisor.TermuxSupervisor)
        runner.daemons = {"child": daemon}

        # The leader is initially alive, so SIGTERM is safe. Simulate another
        # waiter reaping it during the grace interval: the second observation
        # must revoke the PGID pin before any SIGKILL is attempted.
        with mock.patch.object(
            supervisor,
            "_observe_exit_without_reaping",
            side_effect=[(False, True), (True, False)],
        ), mock.patch.object(supervisor.os, "killpg") as killpg:
            runner._shutdown_daemons(grace=0.0)

        killpg.assert_called_once_with(process.pid, signal.SIGTERM)
        process.wait.assert_called_once_with(timeout=0)
        self.assertIsNone(daemon.process)

    def test_already_reaped_child_is_never_signalled_by_recycled_pid(self):
        daemon = self.start_child("pass\n")
        process = daemon.process
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            try:
                waited_pid, _ = __import__("os").waitpid(process.pid, __import__("os").WNOHANG)
            except ChildProcessError:
                waited_pid = process.pid
            if waited_pid == process.pid:
                break
            time.sleep(0.01)
        else:
            self.fail("child did not exit for external-reap simulation")

        self.assertIsNone(process.returncode, "Popen should not know about the external reap")
        runner = supervisor.TermuxSupervisor.__new__(supervisor.TermuxSupervisor)
        runner.daemons = {"child": daemon}

        with mock.patch.object(supervisor, "_observe_exit_without_reaping", return_value=(True, False)), \
             mock.patch.object(process, "poll", return_value=None), \
             mock.patch.object(process, "terminate") as terminate, \
             mock.patch.object(process, "kill") as kill, \
             mock.patch.object(supervisor.os, "killpg") as killpg:
            runner._shutdown_daemons(grace=0.0)

        terminate.assert_not_called()
        kill.assert_not_called()
        killpg.assert_not_called()
        self.assertIsNone(daemon.process)
        self.assertIsNone(daemon.output_thread)

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


    def test_stability_pass_does_not_reap_managed_child(self):
        process = mock.Mock(pid=12345)
        process.poll.side_effect = AssertionError("stability pass must not call Popen.poll")
        daemon = mock.Mock()
        daemon.process = process
        daemon.timeout = None
        daemon.start_time = time.time() - supervisor.WINDOW_RESET_SECONDS - 1
        daemon.state = {"total_restarts": 0}
        daemon.poll.return_value = None
        daemon.record_stable = mock.Mock()

        runner = supervisor.TermuxSupervisor.__new__(supervisor.TermuxSupervisor)
        runner.running = True
        runner.daemons = {"child": daemon}
        runner.state = {"supervisor": {}}

        def stop_after_one_iteration(_seconds):
            runner.running = False

        with mock.patch.object(supervisor, "save_state"), \
             mock.patch.object(supervisor.time, "sleep", side_effect=stop_after_one_iteration):
            runner._loop()

        daemon.poll.assert_called_once_with()
        daemon.record_stable.assert_called_once_with()
        process.poll.assert_not_called()

    def test_status_observation_does_not_reap_managed_child(self):
        process = mock.Mock(pid=23456)
        process.poll.side_effect = AssertionError("status must not call Popen.poll")
        daemon = mock.Mock()
        daemon.process = process
        daemon.state = {
            "restart_count": 0,
            "total_restarts": 0,
            "last_exit_code": None,
            "last_start": None,
            "last_exit": None,
        }
        runner = supervisor.TermuxSupervisor.__new__(supervisor.TermuxSupervisor)
        runner.daemons = {"child": daemon}

        with mock.patch.object(supervisor, "_observe_exit_without_reaping", return_value=(False, True)):
            status = runner.get_status()

        self.assertTrue(status["daemons"]["child"]["running"])
        self.assertEqual(status["daemons"]["child"]["pid"], 23456)
        process.poll.assert_not_called()


    def test_timeout_kills_pinned_process_group_without_popen_kill(self):
        process = mock.Mock(pid=34567)
        daemon = mock.Mock()
        daemon.process = process
        daemon.timeout = 0.1
        daemon.start_time = time.time() - 1
        daemon.state = {"total_restarts": 0}
        daemon.poll.return_value = None

        runner = supervisor.TermuxSupervisor.__new__(supervisor.TermuxSupervisor)
        runner.running = True
        runner.daemons = {"child": daemon}
        runner.state = {"supervisor": {}}

        def stop_after_one_iteration(_seconds):
            runner.running = False

        with mock.patch.object(supervisor, "_observe_exit_without_reaping", return_value=(False, True)), \
             mock.patch.object(supervisor.os, "killpg") as killpg, \
             mock.patch.object(supervisor, "save_state"), \
             mock.patch.object(supervisor.time, "sleep", side_effect=stop_after_one_iteration):
            runner._loop()

        killpg.assert_called_once_with(34567, signal.SIGKILL)
        process.kill.assert_not_called()
        process.poll.assert_not_called()
        daemon.poll.assert_called_once_with()
class WaitidCapabilityGateTests(unittest.TestCase):
    def test_capability_probe_succeeds_on_supported_runtime(self):
        self.assertTrue(supervisor._supports_waitid_wnowait())

    def test_capability_probe_rejects_missing_wnowait_attribute(self):
        real_hasattr = hasattr

        def missing_wnowait(obj, name):
            if obj is supervisor.os and name == "WNOWAIT":
                return False
            return real_hasattr(obj, name)

        with mock.patch("builtins.hasattr", side_effect=missing_wnowait):
            self.assertFalse(supervisor._supports_waitid_wnowait())

    def test_capability_probe_rejects_runtime_not_implemented(self):
        with mock.patch.object(supervisor.os, "waitid", side_effect=NotImplementedError):
            self.assertFalse(supervisor._supports_waitid_wnowait())

    def test_capability_probe_rejects_runtime_os_error(self):
        with mock.patch.object(supervisor.os, "waitid", side_effect=OSError("unsupported")):
            self.assertFalse(supervisor._supports_waitid_wnowait())

    def test_supervisor_fails_closed_before_lock_or_daemon_start(self):
        runner = supervisor.TermuxSupervisor.__new__(supervisor.TermuxSupervisor)
        runner.lock = mock.Mock()
        daemon = mock.Mock()
        runner.daemons = {"must_not_start": daemon}
        runner._loop = mock.Mock()

        with mock.patch.object(supervisor, "_supports_waitid_wnowait", return_value=False):
            self.assertFalse(runner.run())

        runner.lock.try_acquire.assert_not_called()
        runner._loop.assert_not_called()
        daemon.start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
