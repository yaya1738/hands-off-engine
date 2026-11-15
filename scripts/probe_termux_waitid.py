#!/usr/bin/env python3
"""Read-only-in-effect capability probe for Termux supervisor waitid/WNOWAIT.

Runs one short-lived disposable child, verifies non-reaping exit observation,
then reaps that exact child. It does not inspect, signal, or modify supervisor
processes, locks, state, or configured daemons.

Run on the target Android/Termux device:
    python scripts/probe_termux_waitid.py
"""
import json
import os
import subprocess
import sys
import time


REQUIRED = ("waitid", "P_PID", "WEXITED", "WNOHANG", "WNOWAIT")


def probe():
    missing = [name for name in REQUIRED if not hasattr(os, name)]
    if missing:
        return {"ok": False, "stage": "capability-presence", "missing": missing}

    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(0.25)"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        start_new_session=True,
    )
    reaped = False
    try:
        flags = os.WEXITED | os.WNOHANG | os.WNOWAIT
        before = os.waitid(os.P_PID, child.pid, flags)
        if before is not None and before.si_pid:
            return {
                "ok": False,
                "stage": "live-child-observation",
                "detail": "waitid reported exit before the disposable child exited",
            }

        deadline = time.monotonic() + 5.0
        observed = None
        while time.monotonic() < deadline:
            observed = os.waitid(os.P_PID, child.pid, flags)
            if observed is not None and observed.si_pid == child.pid:
                break
            time.sleep(0.01)
        else:
            return {
                "ok": False,
                "stage": "exit-observation",
                "detail": "waitid did not report the exited disposable child within 5 seconds",
            }

        if child.returncode is not None:
            return {
                "ok": False,
                "stage": "non-reaping",
                "detail": "Popen.returncode changed before the explicit waitpid",
            }

        observed_again = os.waitid(os.P_PID, child.pid, flags)
        if observed_again is None or observed_again.si_pid != child.pid:
            return {
                "ok": False,
                "stage": "repeat-non-reaping",
                "detail": "second WNOWAIT observation did not see the same waitable child",
            }

        waited_pid, status = os.waitpid(child.pid, 0)
        reaped = True
        child.returncode = os.waitstatus_to_exitcode(status)
        if waited_pid != child.pid or child.returncode != 0:
            return {
                "ok": False,
                "stage": "explicit-reap",
                "detail": f"waitpid={waited_pid}, exit_code={child.returncode}",
            }

        try:
            os.waitid(os.P_PID, child.pid, flags)
        except ChildProcessError:
            pass
        else:
            return {
                "ok": False,
                "stage": "post-reap",
                "detail": "waitid still observed child after explicit reap",
            }

        return {
            "ok": True,
            "stage": "complete",
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "waitid": True,
            "wnowait_non_reaping": True,
            "explicit_waitpid_reap": True,
        }
    finally:
        # This is our own direct child and has not been externally reaped.
        # wait() is used only for bounded cleanup of the disposable probe child.
        if not reaped and child.returncode is None:
            try:
                child.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                child.terminate()
                try:
                    child.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=2.0)


if __name__ == "__main__":
    try:
        result = probe()
    except (OSError, AttributeError, NotImplementedError, ChildProcessError) as exc:
        result = {
            "ok": False,
            "stage": "exception",
            "error": type(exc).__name__,
            "detail": str(exc),
        }
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result.get("ok") else 1)
