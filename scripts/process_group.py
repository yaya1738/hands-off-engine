#!/usr/bin/env python3
"""Owned subprocess-group lifecycle with deferred leader reaping.

The direct child remains waitable (WNOWAIT) until output capture succeeds.
If any operation fails after the leader exits, the still-identifiable process
group is terminated before the leader is reaped, preventing orphan descendants.
"""
import os
import signal
import subprocess
import tempfile
import time


POLL_SECONDS = 0.01


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


def _read_tail(stream, limit):
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(max(0, size - limit), os.SEEK_SET)
    return stream.read(limit).decode("utf-8", errors="replace").strip()


def run_process(command, *, cwd, timeout, max_output_chars):
    """Run a command and return bounded output; always clean up on failure.

    Output is captured before the direct child is reaped. This ordering is the
    core ownership guarantee: an output/read/return-code exception can still
    terminate descendants in the original process group.
    """
    process = None
    output = ""
    group_identity_pinned = False
    try:
        with tempfile.TemporaryFile(mode="w+b") as output_file:
            process = subprocess.Popen(
                command,
                stdout=output_file,
                stderr=subprocess.STDOUT,
                cwd=str(cwd),
                start_new_session=True,
            )
            try:
                _wait_for_exit_without_reaping(process.pid, timeout)
            except TimeoutError as exc:
                _kill_group(process.pid)
                try:
                    returncode = process.wait()
                except Exception:
                    returncode = process.returncode
                output = _read_tail(output_file, max_output_chars)
                detail = (output + "\n" + str(exc)).strip()
                return {"success": False, "returncode": returncode,
                        "output": detail[-max_output_chars:], "timed_out": True}

            # The leader has exited but remains unreaped, so its PID still
            # pins the original process-group identity. Remove any descendants
            # it left behind before output capture and before releasing that ID.
            group_identity_pinned = True
            _kill_group(process.pid)

            # Deliberately perform fallible output capture before wait()/reap.
            output = _read_tail(output_file, max_output_chars)
            returncode = process.wait()
            return {"success": returncode == 0, "returncode": returncode,
                    "output": output, "timed_out": False}
    except Exception as exc:
        if process is not None and group_identity_pinned:
            # Only signal/reap after WNOWAIT proved that this owner still has
            # the unreaped leader anchoring the original process-group ID.
            _kill_group(process.pid)
            try:
                process.wait()
            except Exception:
                pass
        return {"success": False,
                "returncode": process.returncode if process is not None else None,
                "output": str(exc)[-max_output_chars:], "timed_out": False}
