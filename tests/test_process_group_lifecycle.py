"""Real-process regression tests for shared subprocess-group ownership."""
import io
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import process_group, scheduler, improvement_cycle


def _pid_is_running(pid):
    stat = Path(f"/proc/{pid}/stat")
    try:
        raw = stat.read_text()
    except (FileNotFoundError, ProcessLookupError):
        return False
    state = raw[raw.rfind(")") + 2:].split()[0]
    return state != "Z"


def _wait_stopped(pid, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _pid_is_running(pid):
            return True
        time.sleep(0.03)
    return not _pid_is_running(pid)


class ProcessGroupLifecycleTests(unittest.TestCase):
    def _script(self, directory, body):
        path = Path(directory) / "child.py"
        path.write_text(body)
        return path

    def test_normal_completion_captures_output_then_reaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = self._script(tmp, "print('normal-output')\n")
            result = process_group.run_process(
                [sys.executable, str(script)], cwd=tmp, timeout=3,
                max_output_chars=100,
            )
        self.assertTrue(result["success"], result)
        self.assertEqual(result["returncode"], 0)
        self.assertIn("normal-output", result["output"])
        self.assertTrue(result["cleanup_guaranteed"])
        self.assertFalse(result["timed_out"])

    def test_output_capture_memory_is_bounded_and_keeps_tail(self):
        limit = 32
        capture = process_group._BoundedOutputCapture(
            io.BytesIO(b"prefix-" + b"x" * 100000 + b"TAIL"), limit,
        )
        self.assertTrue(capture.tail().endswith("TAIL"))
        self.assertLessEqual(len(capture._tail), limit * 4)

    def test_real_child_can_emit_large_output_without_unbounded_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = self._script(tmp, """
import sys
sys.stdout.write('x' * 1000000)
sys.stdout.write('FINAL_MARKER')
""")
            result = process_group.run_process(
                [sys.executable, str(script)], cwd=tmp, timeout=5,
                max_output_chars=32,
            )
        self.assertTrue(result["success"], result)
        self.assertLessEqual(len(result["output"]), 32)
        self.assertTrue(result["output"].endswith("FINAL_MARKER"))

    def test_normal_leader_exit_kills_orphaned_descendants(self):
        with tempfile.TemporaryDirectory() as tmp:
            pid_file = Path(tmp) / "descendant.pid"
            script = self._script(tmp, """
import subprocess, sys
from pathlib import Path
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
Path(sys.argv[1]).write_text(str(child.pid))
print('leader exits while child remains')
""")
            result = process_group.run_process(
                [sys.executable, str(script), str(pid_file)], cwd=tmp,
                timeout=3, max_output_chars=200,
            )
            child_pid = int(pid_file.read_text())
        self.assertTrue(result["success"], result)
        self.assertIn("leader exits while child remains", result["output"])
        self.assertTrue(_wait_stopped(child_pid), f"orphan descendant {child_pid} survived normal exit")

    def test_timeout_kills_entire_real_process_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            pid_file = Path(tmp) / "descendant.pid"
            script = self._script(tmp, """
import subprocess, sys, time
from pathlib import Path
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
Path(sys.argv[1]).write_text(str(child.pid))
time.sleep(60)
""")
            result = process_group.run_process(
                [sys.executable, str(script), str(pid_file)], cwd=tmp,
                timeout=0.25, max_output_chars=200,
            )
            child_pid = int(pid_file.read_text())
        self.assertFalse(result["success"])
        self.assertTrue(result["timed_out"])
        self.assertTrue(_wait_stopped(child_pid), f"descendant {child_pid} survived timeout")

    def test_post_exit_output_exception_kills_descendants_before_reap(self):
        with tempfile.TemporaryDirectory() as tmp:
            pid_file = Path(tmp) / "descendant.pid"
            script = self._script(tmp, """
import subprocess, sys
from pathlib import Path
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
Path(sys.argv[1]).write_text(str(child.pid))
print('leader exits now')
""")
            def fail_after_leader_exit(stream, limit):
                raise OSError("injected output-capture failure after leader exit")

            with mock.patch.object(process_group, "_read_tail", side_effect=fail_after_leader_exit):
                result = process_group.run_process(
                    [sys.executable, str(script), str(pid_file)], cwd=tmp,
                    timeout=3, max_output_chars=200,
                )
            child_pid = int(pid_file.read_text())
        self.assertFalse(result["success"])
        self.assertIn("injected output-capture failure", result["output"])
        self.assertTrue(_wait_stopped(child_pid), f"descendant {child_pid} survived post-exit exception")


    def _assert_wrapper_cleans_descendant_after_output_failure(self, wrapper):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts = root / "scripts"
            scripts.mkdir()
            pid_file = root / "descendant.pid"
            script = scripts / "child.py"
            script.write_text(
                "import subprocess, sys\n"
                "from pathlib import Path\n"
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
                f"Path({str(pid_file)!r}).write_text(str(child.pid))\n"
                "print('leader exited')\n"
            )

            def fail_output(stream, limit):
                raise OSError("injected wrapper output failure")

            with mock.patch.object(process_group, "_read_tail", side_effect=fail_output):
                if wrapper == "scheduler":
                    with mock.patch.object(scheduler, "ROOT", root):
                        result = scheduler.run_task({"name": "process-group-test", "script": "child.py"})
                else:
                    with mock.patch.object(improvement_cycle, "ROOT", root):
                        result = improvement_cycle.run_subprocess("child.py")

            child_pid = int(pid_file.read_text())
        self.assertFalse(result["success"])
        self.assertTrue(
            _wait_stopped(child_pid),
            f"{wrapper} wrapper left descendant {child_pid} alive after output failure",
        )

    def test_scheduler_wrapper_cleans_descendant_after_post_exit_exception(self):
        self._assert_wrapper_cleans_descendant_after_output_failure("scheduler")

    def test_improvement_cycle_wrapper_cleans_descendant_after_post_exit_exception(self):
        self._assert_wrapper_cleans_descendant_after_output_failure("improvement_cycle")

    def test_waitid_fails_closed_for_already_reaped_leader(self):
        with mock.patch.object(process_group.os, "waitid", side_effect=ChildProcessError):
            with self.assertRaises(ChildProcessError):
                process_group._wait_for_exit_without_reaping(987654, 0.1)

    def test_termination_sends_term_then_kill_while_leader_remains_pinned(self):
        process = mock.Mock(pid=987654)
        with mock.patch.object(process_group.os, "killpg") as killpg, \
             mock.patch.object(process_group.os, "waitid", return_value=None), \
             mock.patch.object(process_group.time, "sleep"):
            self.assertTrue(process_group._terminate_group(process, grace_seconds=0.1))
        killpg.assert_has_calls([
            mock.call(987654, process_group.signal.SIGTERM),
            mock.call(987654, process_group.signal.SIGKILL),
        ])

    def test_termination_does_not_kill_after_leader_is_reaped_during_grace(self):
        process = mock.Mock(pid=987654)
        with mock.patch.object(process_group.os, "killpg") as killpg, \
             mock.patch.object(process_group.os, "waitid", side_effect=ChildProcessError), \
             mock.patch.object(process_group.time, "sleep"):
            self.assertFalse(process_group._terminate_group(process, grace_seconds=0.1))
        killpg.assert_called_once_with(987654, process_group.signal.SIGTERM)

    def test_external_reap_fails_closed_without_signalling_group(self):
        process = mock.Mock(pid=987654, returncode=None)
        process.stdout = io.BytesIO()
        with mock.patch.object(process_group, "supports_waitid_wnowait", return_value=True), \
             mock.patch.object(process_group.subprocess, "Popen", return_value=process), \
             mock.patch.object(process_group, "_wait_for_exit_without_reaping",
                                side_effect=ChildProcessError("externally reaped")), \
             mock.patch.object(process_group.os, "killpg") as killpg:
            result = process_group.run_process(
                ["unused"], cwd=".", timeout=0.1, max_output_chars=100,
            )
        self.assertFalse(result["success"])
        self.assertFalse(result["cleanup_guaranteed"])
        killpg.assert_not_called()
        process.poll.assert_not_called()
        process.wait.assert_not_called()

    def test_runtime_wnowait_oserror_kills_live_process_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            pid_file = Path(tmp) / "descendant.pid"
            script = self._script(tmp, """
import subprocess, sys, time
from pathlib import Path
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
Path(sys.argv[1]).write_text(str(child.pid))
time.sleep(60)
""")
            def fail_after_descendant_starts(_pid, _timeout):
                deadline = time.monotonic() + 3.0
                while time.monotonic() < deadline and not pid_file.exists():
                    time.sleep(0.01)
                if not pid_file.exists():
                    raise AssertionError("child did not publish descendant PID")
                raise OSError("runtime WNOWAIT failure")

            with mock.patch.object(
                process_group, "_wait_for_exit_without_reaping",
                side_effect=fail_after_descendant_starts,
            ):
                result = process_group.run_process(
                    [sys.executable, str(script), str(pid_file)], cwd=tmp,
                    timeout=3, max_output_chars=200,
                )
            child_pid = int(pid_file.read_text())
        self.assertFalse(result["success"])
        self.assertTrue(result["cleanup_guaranteed"], result)
        self.assertTrue(
            _wait_stopped(child_pid),
            f"runtime WNOWAIT failure left descendant {child_pid} alive",
        )

    def test_runtime_wnowait_error_after_leader_exit_reports_unproven_cleanup(self):
        process = mock.Mock(pid=987654, returncode=None)
        process.stdout = io.BytesIO()
        process.poll.return_value = 0
        process.returncode = 0
        with mock.patch.object(process_group, "supports_waitid_wnowait", return_value=True), \
             mock.patch.object(process_group.subprocess, "Popen", return_value=process), \
             mock.patch.object(process_group, "_wait_for_exit_without_reaping",
                                side_effect=OSError("runtime WNOWAIT failure")), \
             mock.patch.object(process_group.os, "killpg") as killpg:
            result = process_group.run_process(
                ["unused"], cwd=".", timeout=0.1, max_output_chars=100,
            )
        self.assertFalse(result["success"])
        self.assertFalse(result["cleanup_guaranteed"])
        killpg.assert_not_called()

    def test_unsupported_wnowait_refuses_before_launching_real_subprocess(self):
        with mock.patch.object(process_group, "supports_waitid_wnowait", return_value=False), \
             mock.patch.object(process_group.subprocess, "Popen") as popen:
            result = process_group.run_process(
                ["unused"], cwd=".", timeout=0.1, max_output_chars=100,
            )
        self.assertFalse(result["success"])
        self.assertIn("refusing to launch subprocess", result["output"])
        popen.assert_not_called()



if __name__ == "__main__":
    unittest.main()
