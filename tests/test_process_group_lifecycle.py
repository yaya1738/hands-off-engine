"""Real-process regression tests for shared subprocess-group ownership."""
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

from scripts import process_group


def _pid_is_running(pid):
    stat = Path(f"/proc/{pid}/stat")
    try:
        raw = stat.read_text()
    except FileNotFoundError:
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
        self.assertFalse(result["timed_out"])

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

    def test_waitid_accepts_already_reaped_leader(self):
        with mock.patch.object(process_group.os, "waitid", side_effect=ChildProcessError):
            # An external reaper means there is no wait status left to observe.
            process_group._wait_for_exit_without_reaping(987654, 0.1)


if __name__ == "__main__":
    unittest.main()
