#!/usr/bin/env python3
"""Owned subprocess-group lifecycle with deferred leader reaping.

The direct child remains waitable (WNOWAIT) until output capture succeeds.
If any operation fails after the leader exits, the still-identifiable process
group is terminated before the leader is reaped, preventing orphan descendants.
"""
import os
import signal
from functools import lru_cache
import subprocess
import sys
import threading
import time


POLL_SECONDS = 0.01


@lru_cache(maxsize=1)
def supports_waitid_wnowait():
    """Verify WNOWAIT against a disposable child before launching real work."""
    required = ("waitid", "P_PID", "WEXITED", "WNOHANG", "WNOWAIT")
    if not all(hasattr(os, name) for name in required):
        return False

    child = None
    reaped = False
    try:
        child = subprocess.Popen(
            [sys.executable, "-c", "pass"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )
        flags = os.WEXITED | os.WNOHANG | os.WNOWAIT
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            observed = os.waitid(os.P_PID, child.pid, flags)
            if observed is not None and observed.si_pid == child.pid:
                break
            time.sleep(POLL_SECONDS)
        else:
            return False

        repeated = os.waitid(os.P_PID, child.pid, flags)
        if repeated is None or repeated.si_pid != child.pid:
            return False

        waited_pid, status = os.waitpid(child.pid, 0)
        reaped = True
        child.returncode = os.waitstatus_to_exitcode(status)
        return waited_pid == child.pid and child.returncode == 0
    except (OSError, AttributeError, NotImplementedError, ChildProcessError,
            subprocess.SubprocessError):
        return False
    finally:
        if child is not None and not reaped and child.returncode is None:
            try:
                child.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                child.terminate()
                try:
                    child.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=2.0)


def _wait_for_exit_without_reaping(pid, timeout):
    """Wait for leader exit without consuming its wait status."""
    deadline = time.monotonic() + timeout
    flags = os.WEXITED | os.WNOHANG | os.WNOWAIT
    while True:
        try:
            info = os.waitid(os.P_PID, pid, flags)
        except ChildProcessError as exc:
            # The leader is no longer waitable by this owner. Its PID/PGID may
            # already have been reused, so signalling that group is unsafe.
            raise ChildProcessError(
                f"cannot prove process-group ownership for reaped leader {pid}"
            ) from exc
        if info is not None and info.si_pid:
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"child process group exceeded {timeout}s")
        time.sleep(min(POLL_SECONDS, remaining))


def _kill_group(pgid):
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _terminate_group(process, grace_seconds=0.25):
    """Send TERM, then re-prove leader ownership before the final KILL."""
    pgid = process.pid
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return True

    time.sleep(max(0.0, grace_seconds))
    try:
        observed = os.waitid(
            os.P_PID, pgid, os.WEXITED | os.WNOHANG | os.WNOWAIT,
        )
        pinned = observed is None or observed.si_pid in (0, pgid)
    except ChildProcessError:
        # A concurrent waiter reaped the leader during the grace period.
        return False
    except (OSError, NotImplementedError):
        # If WNOWAIT itself fails, only a still-live direct child pins the PGID.
        try:
            pinned = process.poll() is None
        except Exception:
            pinned = False

    if not pinned:
        return False
    _kill_group(pgid)
    return True


def _cleanup_after_wait_observation_error(process):
    """Kill a still-live owned group after waitid fails for a non-reap error.

    Popen.poll() is deliberately used only as a liveness check here. If it
    returns None, the direct child is still alive and therefore still pins its
    PID/PGID; if it returns an exit code, poll has reaped the leader and the
    numeric group ID must no longer be signalled. ChildProcessError is handled
    separately because it means another waiter may already own/reap the child.
    """
    try:
        if process.poll() is not None:
            return False, process.returncode
    except ChildProcessError:
        return False, process.returncode
    except Exception:
        return False, process.returncode

    try:
        _kill_group(process.pid)
        try:
            return True, process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            # The group has already received SIGKILL. This direct-child fallback
            # is safe because poll() just proved the leader was still alive.
            process.kill()
            return True, process.wait(timeout=2.0)
    except Exception:
        return False, process.returncode


class _BoundedOutputCapture:
    """Drain child output continuously while retaining only a bounded tail."""

    def __init__(self, stream, max_output_chars):
        self.stream = stream
        self.max_output_chars = max(0, int(max_output_chars))
        # UTF-8 needs at most four bytes per Unicode character. The retained
        # byte buffer is therefore bounded independently of child output size.
        self.max_bytes = max(1, self.max_output_chars * 4)
        self._tail = bytearray()
        self._lock = threading.Lock()
        self._error = None
        self._thread = threading.Thread(
            target=self._drain,
            name="process-group-output-drain",
            daemon=True,
        )
        self._thread.start()

    def _drain(self):
        try:
            while True:
                reader = getattr(self.stream, "read1", self.stream.read)
                chunk = reader(65536)
                if not chunk:
                    break
                with self._lock:
                    self._tail.extend(chunk)
                    overflow = len(self._tail) - self.max_bytes
                    if overflow > 0:
                        del self._tail[:overflow]
        except Exception as exc:
            self._error = exc
        finally:
            try:
                self.stream.close()
            except Exception:
                pass

    def finish(self, timeout=2.0):
        self._thread.join(timeout=max(0.0, timeout))
        if self._thread.is_alive():
            raise TimeoutError("child output pipe did not close after process-group cleanup")
        if self._error is not None:
            raise self._error

    def tail(self):
        self.finish()
        if self.max_output_chars == 0:
            return ""
        with self._lock:
            data = bytes(self._tail)
        return data.decode("utf-8", errors="replace").strip()[-self.max_output_chars:]


def _read_tail(capture, limit):
    # Retain the existing helper boundary so callers/tests can inject capture
    # failures while the process-group identity is still owned.
    if capture.max_output_chars != max(0, int(limit)):
        capture.max_output_chars = max(0, int(limit))
    return capture.tail()


def run_process(command, *, cwd, timeout, max_output_chars):
    """Run a command with bounded output and explicit process cleanup certainty."""
    process = None
    capture = None
    group_termination_sent = False
    if not supports_waitid_wnowait():
        return {"success": False, "returncode": None,
                "output": "unsupported waitid(WNOWAIT); refusing to launch subprocess",
                "timed_out": False, "cleanup_guaranteed": True}
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(cwd),
            start_new_session=True,
        )
        capture = _BoundedOutputCapture(process.stdout, max_output_chars)
        try:
            _wait_for_exit_without_reaping(process.pid, timeout)
        except TimeoutError as exc:
            group_termination_sent = _terminate_group(process)
            if not group_termination_sent:
                return {"success": False, "returncode": process.returncode,
                        "output": "process-group ownership lost during termination grace; cleanup not guaranteed",
                        "timed_out": True, "cleanup_guaranteed": False}
            try:
                returncode = process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                process.kill()
                returncode = process.wait(timeout=2.0)
            output = _read_tail(capture, max_output_chars)
            detail = (output + "\n" + str(exc)).strip()
            return {"success": False, "returncode": returncode,
                    "output": detail[-max_output_chars:], "timed_out": True,
                    "cleanup_guaranteed": True}

        # The leader has exited but remains unreaped, pinning the original
        # process-group identity while descendants receive TERM then KILL.
        group_termination_sent = _terminate_group(process)
        if not group_termination_sent:
            return {"success": False, "returncode": process.returncode,
                    "output": "process-group ownership lost during termination grace; cleanup not guaranteed",
                    "timed_out": False, "cleanup_guaranteed": False}

        # The reader continuously drains the pipe but retains only a bounded
        # UTF-8 tail, so child output cannot grow an unbounded temporary file.
        output = _read_tail(capture, max_output_chars)
        returncode = process.wait()
        return {"success": returncode == 0, "returncode": returncode,
                "output": output, "timed_out": False,
                "cleanup_guaranteed": True}
    except ChildProcessError as exc:
        # Another waiter may have reaped the leader. Never signal its numeric
        # PID/PGID after that ownership proof has been lost.
        return {"success": False,
                "returncode": process.returncode if process is not None else None,
                "output": str(exc)[-max_output_chars:], "timed_out": False,
                "cleanup_guaranteed": group_termination_sent}
    except (OSError, NotImplementedError) as exc:
        cleanup_guaranteed = group_termination_sent
        returncode = process.returncode if process is not None else None
        if process is not None and not group_termination_sent:
            # A runtime waitid failure is different from external reaping.
            # poll() returning None proves our direct child is still live and
            # pins the PGID; if poll reaps an exited leader, fail closed.
            cleanup_guaranteed, returncode = _cleanup_after_wait_observation_error(process)
        elif process is not None and process.returncode is None:
            try:
                returncode = process.wait(timeout=2.0)
            except Exception:
                pass
        if capture is not None and cleanup_guaranteed:
            try:
                capture.finish()
            except Exception:
                pass
        return {"success": False, "returncode": returncode,
                "output": str(exc)[-max_output_chars:], "timed_out": False,
                "cleanup_guaranteed": cleanup_guaranteed}
    except Exception as exc:
        cleanup_guaranteed = group_termination_sent
        returncode = process.returncode if process is not None else None
        if process is not None and not group_termination_sent:
            cleanup_guaranteed, returncode = _cleanup_after_wait_observation_error(process)
        elif process is not None and process.returncode is None:
            try:
                returncode = process.wait(timeout=2.0)
            except Exception:
                pass
        if capture is not None and cleanup_guaranteed:
            try:
                capture.finish()
            except Exception:
                pass
        return {"success": False, "returncode": returncode,
                "output": str(exc)[-max_output_chars:], "timed_out": False,
                "cleanup_guaranteed": cleanup_guaranteed}
