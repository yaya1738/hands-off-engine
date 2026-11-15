"""Regression tests for supervisor backoff application and cooldown bounds.

Covers item 6 of the integration decision (backoff application and cooldown
bounds) plus the future-timestamp case of item 4 (heartbeat freshness):
- the backoff ladder is bounded (initial, doubling, cap, cooldown);
- persisted restart bookkeeping is clamped so clock jumps cannot block a
  service for longer than one cooldown, and garbage values fail safe;
- a failed service is NOT restarted before its backoff elapses (the restart
  actually waits), and IS restarted once it does;
- ten consecutive failures trigger the bounded cooldown, no restart happens
  inside the cooldown window, and recovery resumes afterwards;
- a heartbeat timestamp in the future is classified stale (fail closed).
"""
import json
import os
import re
import signal
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import supervisor


class FailingChild:
    """Popen stand-in that dies with rc=1 on its first poll()."""

    pid = 45678

    def __init__(self, clock):
        self.clock = clock
        self.returncode = None
        self.fail_observed_at = None

    def poll(self):
        if self.returncode is None:
            self.returncode = 1
            self.fail_observed_at = self.clock.now
        return self.returncode

    def terminate(self):
        self.returncode = -15

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        self.returncode = -9


class CleanExitChild:
    """Long-running service stand-in that unexpectedly exits with rc=0."""
    pid = 45679

    def __init__(self, clock):
        self.clock = clock
        self.returncode = None
        self.exit_observed_at = None

    def poll(self):
        if self.returncode is None:
            self.returncode = 0
            self.exit_observed_at = self.clock.now
        return self.returncode

    def terminate(self):
        self.returncode = -15

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        self.returncode = -9


class ShutdownChild:
    pid = 45680

    def __init__(self, ignore_term=False):
        self.ignore_term = ignore_term
        self.returncode = None
        self.events = []

    def poll(self):
        return self.returncode

    def terminate(self):
        self.events.append("terminate")
        if not self.ignore_term:
            self.returncode = -signal.SIGTERM

    def wait(self, timeout=None):
        self.events.append("wait")
        if self.returncode is None:
            raise subprocess.TimeoutExpired("fake-child", timeout)
        return self.returncode

    def kill(self):
        self.events.append("kill")
        self.returncode = -signal.SIGKILL


class Clock:
    def __init__(self, start=1000.0, step=10.0):
        self.now = start
        self.step = step

    def time(self):
        return self.now

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += self.step


class SupervisorRecoveryContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        logs = root / "logs"
        logs.mkdir()
        self.state = root / "supervisor_state.json"
        self.log = logs / "supervisor.log"
        self.service = {
            "name": "factory_scheduler",
            "cmd": ["scheduler.py"],
            "cwd": str(root),
            "log": self.log,
        }
        self.patchers = [
            mock.patch.object(supervisor, "STATE", root),
            mock.patch.object(supervisor, "LOG_DIR", logs),
            mock.patch.object(supervisor, "SUPERVISOR_PID", root / "supervisor.pid"),
            mock.patch.object(supervisor, "SUPERVISOR_LOCK", root / "supervisor.lock"),
            mock.patch.object(supervisor, "SUPERVISOR_LOG", self.log),
            mock.patch.object(supervisor, "WATCHDOG_STATE", self.state),
        ]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def _run_with(self, clock, max_loops):
        """Run the supervisor loop; return (popen times, children started)."""
        popen_times = []
        children = []

        def fake_popen(*args, **kwargs):
            popen_times.append(clock.now)
            child = FailingChild(clock)
            children.append(child)
            return child

        with mock.patch.object(supervisor, "SERVICES", [self.service]), \
             mock.patch.object(supervisor, "time", clock), \
             mock.patch.object(supervisor.subprocess, "Popen", side_effect=fake_popen):
            supervisor.run(max_loops=max_loops)
        return popen_times, children

    def _run_clean_exit_with(self, clock, max_loops):
        popen_times = []
        children = []

        def fake_popen(*args, **kwargs):
            popen_times.append(clock.now)
            child = CleanExitChild(clock)
            children.append(child)
            return child

        with mock.patch.object(supervisor, "SERVICES", [self.service]), \
             mock.patch.object(supervisor, "time", clock), \
             mock.patch.object(supervisor.subprocess, "Popen", side_effect=fake_popen):
            supervisor.run(max_loops=max_loops)
        return popen_times, children

    def test_unexpected_clean_exit_uses_backoff_instead_of_immediate_restart(self):
        clock = Clock(step=1.0)
        popen_times, _ = self._run_clean_exit_with(clock, max_loops=11)
        self.assertEqual(len(popen_times), 1)
        self.assertIn("exited cleanly but unexpectedly", self.log.read_text())
        self.assertIn("next_backoff=10s", self.log.read_text())

    def test_unexpected_clean_exit_restarts_only_after_backoff(self):
        clock = Clock(step=1.0)
        popen_times, _ = self._run_clean_exit_with(clock, max_loops=12)
        self.assertEqual(len(popen_times), 2)
        self.assertGreaterEqual(popen_times[1] - popen_times[0], 10)

    def test_repeated_clean_exits_reach_bounded_cooldown(self):
        clock = Clock(step=60.0)
        popen_times, children = self._run_clean_exit_with(clock, max_loops=80)
        log = self.log.read_text()
        self.assertIn(
            f"entering cooldown for {supervisor.COOLDOWN_DURATION}s "
            f"after {supervisor.MAX_CONSECUTIVE} consecutive failures",
            log,
        )
        self.assertGreaterEqual(len(children), supervisor.MAX_CONSECUTIVE)
        self.assertTrue(any(t >= children[9].exit_observed_at + supervisor.COOLDOWN_DURATION
                            for t in popen_times[10:]))

    def test_backoff_ladder_is_bounded(self):
        expected = [10, 20, 40, 80, 160, 300, 300, 300, 300, 300]
        for consecutive, want in enumerate(expected, start=1):
            got = supervisor._get_backoff(consecutive, supervisor.INITIAL_BACKOFF)
            self.assertEqual(
                got, want,
                f"backoff for {consecutive} failures should be {want}, got {got}",
            )
        self.assertEqual(supervisor._get_backoff(999, 5), supervisor.MAX_BACKOFF)
        self.assertGreater(supervisor.COOLDOWN_DURATION, supervisor.MAX_BACKOFF)

    def test_restore_stats_clamps_timestamps_and_fails_safe_on_garbage(self):
        name = "factory_scheduler"
        now = supervisor.time.time()
        ceiling = now + supervisor.COOLDOWN_DURATION + 5
        saved = {
            "services": {
                name: {
                    "consecutive_failures": -7,          # negative -> 0
                    "backoff": 99999,                     # too large -> MAX_BACKOFF
                    "cooldown_until": now + 999999,       # far future -> clamped
                    "next_start_at": now + 999999,        # far future -> clamped
                    "last_success": "whenever",
                }
            }
        }
        with mock.patch.object(supervisor, "SERVICES", [self.service]):
            stats = supervisor._restore_stats(saved)
        st = stats[name]
        self.assertEqual(st["consecutive_failures"], 0)
        self.assertEqual(st["backoff"], supervisor.MAX_BACKOFF)
        self.assertLessEqual(st["cooldown_until"], ceiling)
        self.assertGreater(st["cooldown_until"], now)
        self.assertLessEqual(st["next_start_at"], ceiling)
        self.assertEqual(st["last_success"], "whenever")

        # Garbage values fail safe: fresh stats rather than an exception.
        with mock.patch.object(supervisor, "SERVICES", [self.service]):
            fresh = supervisor._restore_stats(
                {"services": {name: {"consecutive_failures": "x", "backoff": None}}}
            )
        self.assertEqual(fresh[name]["consecutive_failures"], 0)
        self.assertEqual(fresh[name]["backoff"], supervisor.INITIAL_BACKOFF)
        self.assertIsNone(fresh[name]["cooldown_until"])

    def test_failed_service_is_not_restarted_before_backoff_elapses(self):
        clock = Clock(step=1.0)  # loops advance 1s; first backoff is 10s
        popen_times, _ = self._run_with(clock, max_loops=11)
        self.assertEqual(
            len(popen_times), 1,
            f"service restarted during backoff window: {popen_times}",
        )

    def test_service_restarts_once_backoff_elapses(self):
        clock = Clock(step=10.0)  # loops advance exactly the first backoff
        popen_times, _ = self._run_with(clock, max_loops=3)
        self.assertEqual(len(popen_times), 2, f"expected restart after backoff: {popen_times}")
        self.assertGreaterEqual(popen_times[1] - popen_times[0], 10)

    def test_ten_failures_trigger_bounded_cooldown_then_recovery(self):
        clock = Clock(step=60.0)
        popen_times, children = self._run_with(clock, max_loops=80)

        log = self.log.read_text()
        self.assertIn(
            f"entering cooldown for {supervisor.COOLDOWN_DURATION}s "
            f"after {supervisor.MAX_CONSECUTIVE} consecutive failures",
            log,
        )
        ladder = [int(m) for m in re.findall(r"next_backoff=(\d+)s", log)]
        self.assertEqual(
            ladder[:10], [10, 20, 40, 80, 160, 300, 300, 300, 300, 300],
            f"backoff ladder wrong: {ladder}",
        )

        # The 10th started child is the one whose failure triggers cooldown.
        fail10 = children[9].fail_observed_at
        self.assertIsNotNone(fail10, "tenth failure never observed")
        window_end = fail10 + supervisor.COOLDOWN_DURATION

        # No restart may start inside the open cooldown window.
        for restart in popen_times[10:]:
            self.assertFalse(
                fail10 < restart < window_end,
                f"restart at t={restart} inside cooldown window "
                f"({fail10}, {window_end})",
            )
        # Recovery must resume once the cooldown expires.
        self.assertTrue(
            any(restart >= window_end for restart in popen_times[10:]),
            f"no restart after cooldown expired at {window_end}; "
            f"restarts={popen_times[10:]}",
        )

    def test_declared_one_shot_completion_is_persisted_across_supervisor_restart(self):
        self.service["expected_exit"] = True
        clock = Clock(step=1.0)
        popen_times, _ = self._run_clean_exit_with(clock, max_loops=4)

        self.assertEqual(len(popen_times), 1)
        saved = json.loads(self.state.read_text())["services"]["factory_scheduler"]
        self.assertTrue(saved["completed"])
        self.assertEqual(saved["consecutive_failures"], 0)
        self.assertIn("completed expected one-shot", self.log.read_text())

        # A second supervisor invocation restores completion and must not
        # relaunch the one-shot after process state has been lost.
        with mock.patch.object(supervisor, "SERVICES", [self.service]), \
             mock.patch.object(supervisor, "time", clock), \
             mock.patch.object(supervisor.subprocess, "Popen") as popen:
            supervisor.run(max_loops=2)
        popen.assert_not_called()

    def test_corrupt_completed_marker_does_not_mark_one_shot_complete(self):
        name = "factory_scheduler"
        with mock.patch.object(supervisor, "SERVICES", [self.service]):
            restored = supervisor._restore_stats({
                "services": {name: {"completed": "false"}}
            })
        self.assertFalse(restored[name]["completed"])

    def test_shutdown_waits_then_kills_only_children_that_ignore_terminate(self):
        polite = ShutdownChild(ignore_term=False)
        stubborn = ShutdownChild(ignore_term=True)
        procs = {"polite": polite, "stubborn": stubborn}

        killed = supervisor._shutdown_children(procs, grace=0.01)

        self.assertEqual(killed, ["stubborn"])
        self.assertEqual(polite.events, ["terminate", "wait"])
        self.assertEqual(stubborn.events, ["terminate", "wait", "kill", "wait"])
        self.assertEqual(procs, {})

    def test_signal_shutdown_cleans_up_owned_resources(self):
        before = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
        clock = Clock(step=1.0)
        clock.sleep = lambda _seconds: os.kill(os.getpid(), signal.SIGTERM)
        child = ShutdownChild()

        with mock.patch.object(supervisor, "SERVICES", [self.service]), \
             mock.patch.object(supervisor, "time", clock), \
             mock.patch.object(supervisor.subprocess, "Popen", return_value=child):
            with self.assertRaises(SystemExit) as raised:
                supervisor.run()

        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(child.events[:2], ["terminate", "wait"])
        self.assertFalse((self.state.parent / "supervisor.pid").exists())
        self.assertFalse(supervisor._lock_is_held(self.state.parent / "supervisor.lock"))
        saved = json.loads(self.state.read_text())["services"]["factory_scheduler"]
        self.assertIsNone(saved["pid"])
        self.assertEqual(
            {sig: signal.getsignal(sig) for sig in before},
            before,
        )

    def test_unexpected_exception_still_cleans_up_owned_resources(self):
        clock = Clock(step=1.0)
        def boom(_seconds):
            raise RuntimeError("injected sleep failure")
        clock.sleep = boom
        child = ShutdownChild()

        with mock.patch.object(supervisor, "SERVICES", [self.service]), \
             mock.patch.object(supervisor, "time", clock), \
             mock.patch.object(supervisor.subprocess, "Popen", return_value=child):
            with self.assertRaisesRegex(RuntimeError, "injected sleep failure"):
                supervisor.run()

        self.assertEqual(child.events[:2], ["terminate", "wait"])
        self.assertFalse((self.state.parent / "supervisor.pid").exists())
        self.assertFalse(supervisor._lock_is_held(self.state.parent / "supervisor.lock"))

    def test_completed_marker_is_ignored_when_service_is_no_longer_one_shot(self):
        name = "factory_scheduler"
        with mock.patch.object(supervisor, "SERVICES", [self.service]):
            restored = supervisor._restore_stats({
                "services": {name: {"completed": True}}
            })
        self.assertFalse(restored[name]["completed"])

    def test_future_heartbeat_timestamp_is_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            hb = Path(tmp) / "heartbeat.json"
            hb.write_text(json.dumps({
                "pid": 321, "phase": "idle", "task": None,
                "task_deadline": None, "updated_at": 5000.0,  # far in the future
            }))
            self.assertEqual(
                supervisor._heartbeat_verdict(hb, 1000.0, expected_pid=321), "stale",
            )
            hb.write_text(json.dumps({
                "pid": 321, "phase": "task", "task": "integrity_check",
                "task_deadline": 5060.0, "updated_at": 5000.0,
            }))
            self.assertEqual(
                supervisor._heartbeat_verdict(hb, 1000.0, expected_pid=321), "stale",
            )


if __name__ == "__main__":
    unittest.main()
