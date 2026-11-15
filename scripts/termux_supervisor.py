#!/usr/bin/env python3
"""
Termux Supervisor — credential-free process supervisor for AnyClaw daemons.

Requirements (Factory round 14):
- One-instance PID/lock guard
- Restart daemons after clean exit, crash, or timeout with bounded exponential backoff
- Keep CommHub/event state outside the supervisor process
- Bounded rotating logs
- Durable last-start/last-exit/restart counters
- Fail-closed: never auto-authorize live execution
- Termux:Boot-compatible launcher
- Does NOT require root, secrets, or a second coordination bus

Platform boundary documented:
Android cannot guarantee an ordinary process survives arbitrary OS killing.
The supervisor recovers on next boot/launcher invocation. Termux:Boot
starts the supervisor, which restarts the daemons.
"""

import json
import os
import sys
import time
import signal
import logging
import subprocess
import threading
import codecs
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = REPO_ROOT / "state"
SUPERVISOR_STATE = STATE_DIR / "supervisor_state.json"
SUPERVISOR_PID = STATE_DIR / "supervisor.pid"
SUPERVISOR_LOCK = STATE_DIR / "supervisor.lock"
LOG_DIR = STATE_DIR / "logs"

# Bounded exponential backoff config
MIN_BACKOFF = 2       # seconds
MAX_BACKOFF = 300     # 5 minutes
MAX_RESTARTS_WINDOW = 10  # resets after this many successful seconds
WINDOW_RESET_SECONDS = 600  # 10 minutes of stability resets restart counter
SHUTDOWN_GRACE_SECONDS = 5.0

# Daemons to supervise
DAEMONS = {
    "governed_root": {
        "script": REPO_ROOT / "autonomous" / "governed_root.py",
        "required": True,
        "timeout": None,  # no timeout — runs indefinitely
    },
    "analysis_engine": {
        "script": REPO_ROOT / "scripts" / "analysis_engine.py",
        "required": False,
        "timeout": None,
    },
    "proactive_monitor": {
        "script": REPO_ROOT / "scripts" / "proactive_monitor.py",
        "args": ["--interval", "60"],
        "required": False,
        "timeout": None,
    },
    "telegram_bridge": {
        "script": REPO_ROOT / "scripts" / "telegram_bridge.py",
        "required": True,
        "timeout": None,
    },
}

import fcntl

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [Supervisor] %(message)s')
log = logging.getLogger("Supervisor")


# ── PID/lock guard: one instance only ──

class SupervisorLock:
    """Persistent-inode file lock ensuring only one supervisor instance runs.

    The lock pathname is deliberately never unlinked during normal operation:
    unlinking a flocked inode can let contenders lock different inodes.
    """

    def __init__(self):
        self.lock_path = SUPERVISOR_LOCK
        self.pid_path = SUPERVISOR_PID
        self.fd = None
        self.owner_pid = None

    def _clear_owned_records(self, *, allow_partial_lock_record: bool = False):
        """Clear our owner markers while flock is held.

        A failed owner-PID publication may leave a prefix after a short write.
        The caller may clear that prefix only on the acquisition failure path,
        where this process truncated the file immediately before writing it.
        Normal release remains exact-match-only.
        """
        if self.owner_pid is None or self.fd is None:
            return

        owner = str(self.owner_pid)
        try:
            if self.pid_path.read_text(encoding="utf-8").strip() == owner:
                self.pid_path.unlink(missing_ok=True)
        except (OSError, UnicodeError):
            # A marker we cannot verify is not ours to remove.
            pass

        try:
            os.lseek(self.fd, 0, os.SEEK_SET)
            recorded = os.read(self.fd, 128).decode("ascii", errors="strict").strip()
            is_our_record = recorded == owner
            is_our_partial_record = (
                allow_partial_lock_record and owner.startswith(recorded)
            )
            if is_our_record or is_our_partial_record:
                os.ftruncate(self.fd, 0)
                os.fsync(self.fd)
        except (OSError, UnicodeError):
            # Preserve an unexpected record rather than deleting another owner's.
            pass

    def try_acquire(self) -> bool:
        """Acquire flock before changing either owner marker."""
        if self.fd is not None:
            return True

        try:
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(str(self.lock_path), os.O_RDWR | os.O_CREAT, 0o600)
        except OSError:
            return False

        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError):
            os.close(fd)
            return False

        self.fd = fd
        self.owner_pid = os.getpid()
        try:
            payload = str(self.owner_pid).encode("ascii")
            os.ftruncate(fd, 0)
            os.lseek(fd, 0, os.SEEK_SET)
            written = 0
            while written < len(payload):
                count = os.write(fd, payload[written:])
                if count <= 0:
                    raise OSError("short write while publishing supervisor lock owner")
                written += count
            os.fsync(fd)
            self.pid_path.parent.mkdir(parents=True, exist_ok=True)
            self.pid_path.write_text(str(self.owner_pid), encoding="utf-8")
            return True
        except (OSError, UnicodeError):
            self._clear_owned_records(allow_partial_lock_record=True)
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)
                self.fd = None
                self.owner_pid = None
            return False

    def release(self):
        """Clear only our markers while locked; keep the lock inode in place."""
        fd = self.fd
        if fd is None:
            return

        try:
            self._clear_owned_records()
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)
                self.fd = None
                self.owner_pid = None


# ── Durable state: restart counters, timing ──

def load_state() -> dict:
    if SUPERVISOR_STATE.exists():
        try:
            return json.loads(SUPERVISOR_STATE.read_text())
        except Exception:
            pass
    return {"daemons": {}, "supervisor": {"restarts": 0, "started_at": None}}


def save_state(state: dict):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    SUPERVISOR_STATE.write_text(json.dumps(state, indent=2))


# ── Rotating log manager ──

class RotatingLog:
    """Bounded rotating log for daemon stdout/stderr."""

    MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
    MAX_LOG_FILES = 3

    def __init__(self, name: str):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.log_path = LOG_DIR / f"{name}.log"
        self.rotate_count = 0

    def _rotate(self):
        if not self.log_path.exists():
            return
        if self.log_path.stat().st_size < self.MAX_LOG_SIZE:
            return
        # Rotate: .log -> .log.1 -> .log.2 -> deleted
        for i in range(self.MAX_LOG_FILES - 1, 0, -1):
            src = LOG_DIR / f"{self.log_path.name}.{i}"
            dst = LOG_DIR / f"{self.log_path.name}.{i + 1}"
            if src.exists():
                if dst.exists():
                    dst.unlink()
                src.rename(dst)
        # Current -> .1
        self.log_path.rename(LOG_DIR / f"{self.log_path.name}.1")

    def write(self, data: str):
        self._rotate()
        with open(self.log_path, "a") as f:
            f.write(data)

# ── Daemon management ──

def _observe_exit_without_reaping(process, timeout: float = 0.0):
    """Return (exited, pgid_pinned) without freeing the leader PID/PGID.

    waitid(..., WNOWAIT) observes exit while leaving the child waitable. That
    keeps its PID (and the session/process-group ID created from it) reserved
    until descendants have been signalled. Calling Popen.poll()/wait() first
    would reap the leader and open a small PID/PGID-reuse race.
    """
    if process.returncode is not None:
        return True, False
    if not all(hasattr(os, attr) for attr in ("waitid", "P_PID", "WNOWAIT")):
        return False, False
    deadline = time.monotonic() + max(0.0, timeout)
    while True:
        try:
            result = os.waitid(
                os.P_PID,
                process.pid,
                os.WEXITED | os.WNOHANG | os.WNOWAIT,
            )
        except ChildProcessError:
            return True, False
        except InterruptedError:
            continue
        if result is not None and result.si_pid:
            return True, True
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False, True
        time.sleep(min(0.01, remaining))


def _supports_waitid_wnowait() -> bool:
    """Exercise WNOWAIT on a disposable child before starting managed daemons.

    Merely checking that os.waitid constants exist is insufficient: Android's
    runtime may expose the API while the underlying operation is unsupported.
    This probe owns only its disposable child and never touches daemon PIDs.
    """
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
            time.sleep(0.01)
        else:
            return False

        repeated = os.waitid(os.P_PID, child.pid, flags)
        if repeated is None or repeated.si_pid != child.pid:
            return False

        waited_pid, status = os.waitpid(child.pid, 0)
        reaped = True
        child.returncode = os.waitstatus_to_exitcode(status)
        return waited_pid == child.pid and child.returncode == 0
    except (OSError, AttributeError, NotImplementedError, ChildProcessError, subprocess.SubprocessError):
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


class ManagedDaemon:
    """One daemon: start, monitor, backoff, restart."""

    def __init__(self, name: str, config: dict, state: dict):
        self.name = name
        self.config = config
        self.script = config["script"]
        self.args = config.get("args", [])
        self.required = config.get("required", False)
        self.timeout = config.get("timeout")
        self.state = state.setdefault("daemons", {}).setdefault(name, {
            "restart_count": 0,
            "last_start": None,
            "last_exit": None,
            "last_exit_code": None,
            "total_restarts": 0,
            "stable_since": None,
        })
        self.process: Optional[subprocess.Popen] = None
        self.log = RotatingLog(name)
        self.start_time: Optional[float] = None
        self.output_thread: Optional[threading.Thread] = None

    def _drain_output(self, stream):
        """Continuously drain merged stdout/stderr into bounded rotating logs."""
        log_write_error_reported = False
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        try:
            while True:
                # Binary BufferedReader.read1 returns currently available pipe
                # bytes instead of waiting to fill the requested chunk size.
                chunk = stream.read1(4096)
                if not chunk:
                    break
                try:
                    decoded = decoder.decode(chunk)
                    if decoded:
                        self.log.write(decoded)
                except Exception as exc:
                    # A full/unavailable log disk must not stop pipe draining
                    # and deadlock the child. Report once, then keep consuming.
                    if not log_write_error_reported:
                        log.warning(
                            "%s: unable to persist child output: %s",
                            self.name,
                            exc,
                        )
                        log_write_error_reported = True
        except (OSError, ValueError) as exc:
            log.debug("%s: output drain stopped: %s", self.name, exc)
        finally:
            try:
                tail = decoder.decode(b"", final=True)
                if tail:
                    self.log.write(tail)
            except Exception as exc:
                if not log_write_error_reported:
                    log.warning("%s: unable to persist final child output: %s", self.name, exc)
            try:
                stream.close()
            except Exception:
                pass

    def start(self):
        if not self.script.exists():
            log.warning(f"{self.name}: script not found ({self.script})")
            return
        cmd = [sys.executable, str(self.script)] + self.args
        try:
            self.process = subprocess.Popen(
                cmd, cwd=REPO_ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=False, bufsize=-1, start_new_session=True,
            )
            self.output_thread = threading.Thread(
                target=self._drain_output,
                args=(self.process.stdout,),
                name=f"{self.name}-output-drain",
                daemon=True,
            )
            self.output_thread.start()
            self.start_time = time.time()
            self.state["last_start"] = datetime.now(timezone.utc).isoformat()
            log.info(f"Started {self.name} (pid={self.process.pid})")
        except Exception as e:
            log.error(f"Failed to start {self.name}: {e}")

    def poll(self) -> Optional[int]:
        """Poll for exit and clean the owned group before reaping its leader."""
        if self.process is None:
            return None
        exited, pgid_pinned = _observe_exit_without_reaping(self.process)
        if not exited:
            return None
        if not pgid_pinned:
            # The leader was already reaped elsewhere (or waitid is unavailable).
            # Do not signal a numeric PGID that may now belong to another process.
            log.error("%s leader exit observed after reaping; refusing unsafe process-group signal", self.name)
            returncode = self.process.poll()
            if self.output_thread is not None:
                self.output_thread.join(timeout=1.0)
                if self.output_thread.is_alive():
                    log.error("%s output reader remains active after unsafe exit observation", self.name)
                else:
                    self.output_thread = None
        else:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            if self.output_thread is not None:
                self.output_thread.join(timeout=0.5)
            # The unreaped leader pins its PID/PGID, so this cannot hit a newly
            # allocated unrelated process group. SIGKILL also catches descendants
            # that ignore SIGTERM or have redirected their output.
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            if self.output_thread is not None:
                self.output_thread.join(timeout=1.0)
                if self.output_thread.is_alive():
                    log.error("%s output reader remains active after descendant cleanup", self.name)
                else:
                    self.output_thread = None
            returncode = self.process.wait()
        self.state["last_exit"] = datetime.now(timezone.utc).isoformat()
        self.state["last_exit_code"] = returncode
        self.process = None
        self.start_time = None
        return returncode

    def backoff_seconds(self) -> float:
        """Bounded exponential backoff: 2s, 4s, 8s, ..., up to 300s."""
        count = self.state.get("restart_count", 0)
        seconds = min(MIN_BACKOFF * (2 ** count), MAX_BACKOFF)
        return seconds

    def record_crash(self):
        self.state["restart_count"] = self.state.get("restart_count", 0) + 1
        self.state["total_restarts"] = self.state.get("total_restarts", 0) + 1
        self.state["stable_since"] = None

    def record_stable(self):
        """Call when daemon has been running for a while."""
        if self.state.get("stable_since") is None:
            self.state["stable_since"] = datetime.now(timezone.utc).isoformat()
            self.state["restart_count"] = 0  # reset backoff after stability


# ── Supervisor main loop ──

class TermuxSupervisor:
    """One-instance supervisor for AnyClaw daemons."""

    def __init__(self):
        self.lock = SupervisorLock()
        self.state = load_state()
        self.daemons: Dict[str, ManagedDaemon] = {}
        self.running = True

        for name, config in DAEMONS.items():
            daemon_state = self.state.setdefault("daemons", {}).setdefault(name, {
                "restart_count": 0,
                "last_start": None,
                "last_exit": None,
                "last_exit_code": None,
                "total_restarts": 0,
                "stable_since": None,
            })
            self.daemons[name] = ManagedDaemon(name, config, daemon_state)

    def run(self):
        if not _supports_waitid_wnowait():
            log.critical(
                "Unsupported process-group safety primitive: waitid(WNOWAIT) "
                "probe failed; refusing to launch managed daemons"
            )
            return False

        if not self.lock.try_acquire():
            existing_pid = SUPERVISOR_PID.read_text().strip() if SUPERVISOR_PID.exists() else "?"
            log.error(f"Supervisor already running (pid={existing_pid}). Exiting.")
            return False

        self.state["supervisor"]["started_at"] = datetime.now(timezone.utc).isoformat()
        log.info("Termux Supervisor started (one-instance PID lock acquired)")

        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        try:
            self._loop()
        finally:
            try:
                self._shutdown_daemons()
            finally:
                self.lock.release()
                save_state(self.state)
                log.info("Supervisor shut down")

        return True

    def _handle_signal(self, signum, frame):
        log.info(f"Signal {signum} received, shutting down gracefully")
        # Keep signal handling non-blocking. The run() finally block owns the
        # bounded terminate/wait/kill sequence before releasing the supervisor lock.
        self.running = False

    def _shutdown_daemons(self, grace: float = SHUTDOWN_GRACE_SECONDS):
        """Stop owned process groups before releasing the singleton lock.

        Keep each child leader unreaped until its process group has received
        SIGKILL. This pins the numeric PGID and prevents PID/PGID reuse from
        redirecting cleanup signals to an unrelated process.
        """
        owned = []
        for name, daemon in self.daemons.items():
            process = daemon.process
            if process is None:
                continue
            exited, pgid_pinned = _observe_exit_without_reaping(process)
            if not pgid_pinned:
                log.error("Unable to pin %s process-group identity; refusing group signal", name)
                owned.append((name, daemon, process, False))
                continue
            owned.append((name, daemon, process, True))
            try:
                os.killpg(process.pid, signal.SIGTERM)
                log.info("Terminating process group for %s", name)
            except ProcessLookupError:
                pass
            except OSError as exc:
                log.warning("Unable to terminate process group for %s: %s", name, exc)

        deadline = time.monotonic() + max(0.0, grace)
        for name, daemon, process, pgid_pinned in owned:
            if pgid_pinned:
                _observe_exit_without_reaping(
                    process,
                    timeout=max(0.0, deadline - time.monotonic()),
                )
                # Do this even if the leader exited promptly: an unreaped zombie
                # keeps the PGID reserved while remaining descendants are killed.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except OSError as exc:
                    log.warning("Unable to kill remaining process group for %s: %s", name, exc)
            else:
                # ChildProcessError means another waiter may already have reaped
                # the leader. Its numeric PID may have been reused, so do not
                # call poll/terminate/kill or signal its former process group.
                # Only wait for Popen bookkeeping and perform best-effort reader
                # cleanup; descendants may remain if their identity was lost.
                log.error(
                    "%s leader was already reaped or could not be safely pinned; "
                    "skipping all PID/PGID signals",
                    name,
                )

            if daemon.output_thread is not None:
                daemon.output_thread.join(timeout=1.0)
                if daemon.output_thread.is_alive():
                    log.error("%s output reader remains active after process-group cleanup", name)
                else:
                    daemon.output_thread = None

            if pgid_pinned:
                try:
                    process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    # The leader was deliberately kept waitable while its PGID
                    # was pinned. If it still has not exited, the exact process
                    # group was already SIGKILLed above; do not add PID signalling
                    # after the bounded cleanup attempt.
                    log.error("%s leader could not be reaped during shutdown", name)
            else:
                # The child was externally reaped or process identity is unknown.
                # Popen.wait() handles ChildProcessError without signalling.
                try:
                    process.wait(timeout=0)
                except (subprocess.TimeoutExpired, ChildProcessError, OSError) as exc:
                    log.warning("%s exit status unavailable after external reap: %s", name, exc)
            daemon.process = None
            daemon.start_time = None

    def _loop(self):
        while self.running:
            for name, daemon in self.daemons.items():
                if daemon.process is None:
                    # Not running — start with backoff
                    backoff = daemon.backoff_seconds()
                    last_exit = daemon.state.get("last_exit")
                    if last_exit and backoff > 0:
                        time.sleep(min(backoff, 5))  # cap poll sleep at 5s
                    daemon.start()
                    if daemon.process:
                        daemon.state["stable_since"] = None
                else:
                    # Running — check for timeout
                    if daemon.timeout and daemon.start_time:
                        elapsed = time.time() - daemon.start_time
                        if elapsed > daemon.timeout:
                            log.warning(f"{name}: timeout after {elapsed:.0f}s, killing owned process group")
                            process = daemon.process
                            exited, pgid_pinned = _observe_exit_without_reaping(process)
                            if pgid_pinned:
                                # Keep the leader unreaped while signalling its
                                # session/process group; Popen.kill() calls poll()
                                # internally and can release the PGID first.
                                try:
                                    os.killpg(process.pid, signal.SIGKILL)
                                except ProcessLookupError:
                                    pass
                                except OSError as exc:
                                    log.warning("%s: timeout process-group kill failed: %s", name, exc)
                            else:
                                log.error(
                                    "%s: timeout observed without a safely pinned PGID; "
                                    "refusing PID/PGID signal",
                                    name,
                                )
                    # Check for exit
                    rc = daemon.poll()
                    if rc is not None:
                        log.warning(f"{name} exited with code {rc}")
                        daemon.record_crash()

            # Check stability from supervisor-owned lifecycle state only.
            # Popen.poll() reaps an exited child and can release its PGID before
            # ManagedDaemon.poll() has pinned it with WNOWAIT for group cleanup.
            for name, daemon in self.daemons.items():
                if daemon.process is not None:
                    if daemon.start_time and (time.time() - daemon.start_time) > WINDOW_RESET_SECONDS:
                        daemon.record_stable()

            # Persist state periodically
            self.state["supervisor"]["restarts"] = sum(
                d.state.get("total_restarts", 0) for d in self.daemons.values()
            )
            save_state(self.state)

            time.sleep(5)

    def get_status(self) -> dict:
        daemon_status = {}
        for name, daemon in self.daemons.items():
            # Status inspection must never reap a managed child. The managed
            # poller owns exit observation and process-group cleanup.
            process = daemon.process
            if process is None:
                running = False
            else:
                exited, _pgid_pinned = _observe_exit_without_reaping(process)
                running = not exited
            daemon_status[name] = {
                "running": running,
                "pid": process.pid if running else None,
                "restart_count": daemon.state.get("restart_count", 0),
                "total_restarts": daemon.state.get("total_restarts", 0),
                "last_exit_code": daemon.state.get("last_exit_code"),
                "last_start": daemon.state.get("last_start"),
                "last_exit": daemon.state.get("last_exit"),
            }
        return {
            "supervisor_pid": os.getpid(),
            "uptime_seconds": 0,
            "daemons": daemon_status,
        }


# ── Termux:Boot launcher ──

def install_boot_launcher():
    """Install a Termux:Boot startup script."""
    termux_boot = Path.home() / ".termux" / "boot"
    termux_boot.mkdir(parents=True, exist_ok=True)
    launcher = termux_boot / "start_anyclaw.sh"
    launcher.write_text(f"""#!/data/data/com.termux/files/usr/bin/bash
# Termux:Boot — starts AnyClaw supervisor on device boot
cd {REPO_ROOT}
nohup python {REPO_ROOT / 'scripts' / 'termux_supervisor.py'} > {STATE_DIR / 'logs' / 'boot.log'} 2>&1 &
echo "AnyClaw supervisor started at $(date)" >> {STATE_DIR / 'logs' / 'boot.log'}
""")
    launcher.chmod(0o755)
    log.info(f"Termux:Boot launcher installed: {launcher}")
    return str(launcher)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Termux Supervisor for AnyClaw daemons")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("run", help="Start supervisor (one instance)")
    sub.add_parser("status", help="Show supervisor and daemon status")
    sub.add_parser("install-boot", help="Install Termux:Boot launcher script")
    sub.add_parser("platform", help="Show platform boundary documentation")

    args = parser.parse_args()

    if args.cmd == "run":
        supervisor = TermuxSupervisor()
        supervisor.run()
    elif args.cmd == "status":
        state = load_state()
        print(json.dumps(state, indent=2))
    elif args.cmd == "install-boot":
        path = install_boot_launcher()
        print(f"Boot launcher installed: {path}")
    elif args.cmd == "platform":
        print("""
PLATFORM BOUNDARY — Android Process Survival

Android OS can kill background processes at any time for memory, battery,
or user-initiated reasons. This supervisor CANNOT guarantee process survival
under arbitrary OS killing.

What the supervisor CAN do:
- Run as a foreground process (more likely to survive)
- Restart immediately on next boot/launcher invocation
- Use Termux:Boot to auto-start on device boot
- Persist all state to disk (survives process death)
- Re-establish daemon state on restart (no duplicate execution)

What the supervisor CANNOT do:
- Prevent Android from killing the process
- Guarantee 100% uptime
- Auto-start after force-stop (only after reboot)
- Override battery optimization (user must disable for AnyClaw)

The correct mental model:
- Supervisor is a "best effort" resilience layer
- Every daemon state is durable (crash-safe)
- If killed, next boot or Termux:Boot invocation restores everything
- No data loss, no duplicate execution, eventual consistency
""")
    else:
        parser.print_help()