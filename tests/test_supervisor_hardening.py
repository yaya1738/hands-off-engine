"""Hardening tests for scripts/supervisor.py and scripts/scheduler.py.

Every path (state, locks, PID, logs, heartbeats) is redirected into tmp_path,
time and process creation are faked, and no real service is ever started, so
these tests never read or modify repository runtime state.
"""
import json
import os
import signal
import subprocess
import sys
import threading
import time as real_time
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import scheduler as sched  # noqa: E402
from scripts import supervisor as sup  # noqa: E402


# ----------------------------------------------------------------- fakes
class FakeTime:
    def __init__(self):
        self.t = 1_700_000_000.0
        self.on_sleep = None

    def time(self):
        return self.t

    def monotonic(self):
        return self.t

    def sleep(self, seconds):
        if self.on_sleep:
            self.on_sleep(seconds)
        self.t += seconds


class FakeProc:
    _pid = 40000

    def __init__(self, clock, lifetime, rc, ignore_term):
        FakeProc._pid += 1
        self.pid = FakeProc._pid
        self.clock = clock
        self.exit_at = None if lifetime is None else clock.time() + lifetime
        self.rc_when_exit = rc
        self.ignore_term = ignore_term
        self.returncode = None
        self.events = []

    def poll(self):
        if self.returncode is None and self.exit_at is not None and self.clock.time() >= self.exit_at:
            self.returncode = self.rc_when_exit
        return self.returncode

    def terminate(self):
        self.events.append("terminate")
        if not self.ignore_term:
            self.returncode = -signal.SIGTERM

    def kill(self):
        self.events.append("kill")
        self.returncode = -signal.SIGKILL

    def wait(self, timeout=None):
        self.events.append("wait")
        if self.poll() is not None:
            return self.returncode
        raise subprocess.TimeoutExpired("fake", timeout)


@pytest.fixture
def env(monkeypatch, tmp_path):
    clock = FakeTime()
    state = tmp_path / "state"
    logs = state / "logs"
    logs.mkdir(parents=True)

    monkeypatch.setattr(sup, "STATE", state)
    monkeypatch.setattr(sup, "LOG_DIR", logs)
    monkeypatch.setattr(sup, "SUPERVISOR_PID", state / "supervisor.pid")
    monkeypatch.setattr(sup, "SUPERVISOR_LOCK", state / "supervisor.lock")
    monkeypatch.setattr(sup, "SUPERVISOR_LOG", logs / "supervisor.log")
    monkeypatch.setattr(sup, "WATCHDOG_STATE", state / "supervisor_state.json")

    services = [{"name": "svc", "cmd": ["fake-svc"], "cwd": str(tmp_path), "log": logs / "svc.log"}]
    monkeypatch.setattr(sup, "SERVICES", services)

    e = SimpleNamespace(
        clock=clock, state=state, services=services, tmp=tmp_path,
        started=[], start_times=[], pid_file_at_start=[], on_start=None,
        spec=lambda: {"lifetime": None, "rc": 1, "ignore_term": False},
    )

    def fake_popen(cmd, cwd=None, stdout=None, stderr=None):
        sp = e.spec()
        p = FakeProc(clock, sp["lifetime"], sp["rc"], sp["ignore_term"])
        e.started.append(p)
        e.start_times.append(clock.time())
        pid_path = sup.SUPERVISOR_PID
        e.pid_file_at_start.append(pid_path.read_text().strip() if pid_path.exists() else None)
        if e.on_start:
            e.on_start(p)
        return p

    monkeypatch.setattr(sup, "time", clock)
    monkeypatch.setattr(
        sup, "subprocess",
        SimpleNamespace(Popen=fake_popen, STDOUT=subprocess.STDOUT, TimeoutExpired=subprocess.TimeoutExpired),
    )
    e.saved = lambda: json.loads((state / "supervisor_state.json").read_text())
    return e


def write_hb(path, pid, phase="idle", updated_at=0.0, deadline=None, task=None):
    Path(path).write_text(json.dumps({
        "pid": pid, "phase": phase, "task": task,
        "task_deadline": deadline, "updated_at": updated_at,
    }))


def live_foreign_process():
    return subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])


def dead_pid():
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


# ----------------------------------------------------------- PID ownership
def test_duplicate_supervisor_cannot_overwrite_active_pid(env):
    holder = sup._acquire_lock(sup.SUPERVISOR_LOCK)
    assert holder is not None
    try:
        sup.SUPERVISOR_PID.write_text("4242")
        sup.run(max_loops=1)
        assert sup.SUPERVISOR_PID.read_text() == "4242"
        assert env.started == []
    finally:
        os.close(holder)


def test_pid_written_only_after_lock_and_removed_by_owner(env):
    sup.run(max_loops=1)
    assert env.pid_file_at_start == [str(os.getpid())]
    assert not sup.SUPERVISOR_PID.exists()
    assert sup._lock_is_held(sup.SUPERVISOR_LOCK) is False


def test_release_pid_file_only_removes_own_pid(env):
    sup.SUPERVISOR_PID.write_text("999999")
    sup._release_pid_file()
    assert sup.SUPERVISOR_PID.read_text() == "999999"
    sup.SUPERVISOR_PID.write_text(str(os.getpid()))
    sup._release_pid_file()
    assert not sup.SUPERVISOR_PID.exists()


def test_lock_probe_never_creates_lock_file(env):
    missing = env.state / "absent.lock"
    assert sup._lock_is_held(missing) is False
    assert not missing.exists()


# ---------------------------------------------------------- lock contention
def test_failed_supervisor_lock_attempt_does_not_truncate(env):
    lock = env.state / "contended.lock"
    lock.write_text("owner-data")
    first = sup._acquire_lock(lock)
    assert first is not None
    try:
        assert sup._acquire_lock(lock) is None
        assert lock.read_text() == "owner-data"
        assert sup._lock_is_held(lock) is True
    finally:
        os.close(first)
    assert sup._lock_is_held(lock) is False


def test_failed_scheduler_lock_attempt_does_not_truncate(tmp_path):
    lock = tmp_path / "scheduler.lock"
    lock.write_text("owner-data")
    first = sched.acquire_singleton_lock(lock)
    assert first is not None
    try:
        assert sched.acquire_singleton_lock(lock) is None
        assert lock.read_text() == "owner-data"
    finally:
        first.close()
    again = sched.acquire_singleton_lock(lock)
    assert again is not None
    again.close()


# --------------------------------------------- repeated rapid crashes/backoff
def test_backoff_is_applied_between_restarts(env):
    env.spec = lambda: {"lifetime": 0, "rc": 1, "ignore_term": False}
    sup.run(max_loops=3)  # t+0 start, t+10 crash seen (backoff 10s), t+20 start
    assert len(env.started) == 2


def test_rapid_crashes_are_bounded_and_enter_cooldown(env):
    env.spec = lambda: {"lifetime": 0, "rc": 1, "ignore_term": False}
    sup.run(max_loops=300)  # 3000 fake seconds of a service that crashes instantly
    gaps = [b - a for a, b in zip(env.start_times, env.start_times[1:])]
    # Never a tight restart loop (one start per 10s supervisor pass would be ~300 starts)
    assert len(env.started) < 30
    assert min(gaps) >= 10
    # Gaps follow the bounded exponential schedule 10, 20, 40, 80, 160, 300, 300, ...
    expected = [10, 20, 40, 80, 160, 300, 300, 300, 300]
    assert all(g >= e for g, e in zip(gaps, expected))
    assert gaps[:9] == sorted(gaps[:9])
    assert all(g <= sup.MAX_BACKOFF + 10 for g in gaps[:9])
    # The 10th consecutive failure triggers the cooldown
    assert gaps[9] >= sup.COOLDOWN_DURATION
    assert "entering cooldown" in sup.SUPERVISOR_LOG.read_text()
    assert env.saved()["services"]["svc"]["consecutive_failures"] <= sup.MAX_CONSECUTIVE


def test_clean_exit_restarts_immediately_without_backoff(env):
    env.spec = lambda: {"lifetime": 0, "rc": 0, "ignore_term": False}
    sup.run(max_loops=4)
    assert len(env.started) == 4
    assert env.saved()["services"]["svc"]["consecutive_failures"] == 0


# ---------------------------------------------------- cooldown persistence
def test_cooldown_persists_across_supervisor_restart(env):
    now = env.clock.time()
    env.state.joinpath("supervisor_state.json").write_text(json.dumps({"services": {"svc": {
        "pid": None, "consecutive_failures": sup.MAX_CONSECUTIVE, "backoff": 300,
        "cooldown_until": now + 500, "next_start_at": now + 500, "last_success": None,
    }}}))
    sup.run(max_loops=3)  # a "restarted" supervisor must still honour the cooldown
    assert env.started == []
    assert env.saved()["services"]["svc"]["cooldown_until"] == now + 500

    env.clock.t = now + 501
    sup.run(max_loops=1)
    assert len(env.started) == 1


def test_crash_counters_survive_restart_and_continue_backoff(env):
    env.spec = lambda: {"lifetime": 0, "rc": 1, "ignore_term": False}
    sup.run(max_loops=6)
    before = env.saved()["services"]["svc"]
    assert before["consecutive_failures"] >= 2
    sup.run(max_loops=1)  # new supervisor instance resumes from persisted counters
    after = env.saved()["services"]["svc"]
    assert after["consecutive_failures"] >= before["consecutive_failures"]
    assert after["backoff"] >= before["backoff"]


def test_restore_clamps_clock_jumps_and_ignores_garbage(env):
    now = env.clock.time()
    far = now + 10 ** 9
    stats = sup._restore_stats({"services": {"svc": {
        "consecutive_failures": 3, "backoff": 10 ** 6, "cooldown_until": far, "next_start_at": far}}})
    st = stats["svc"]
    assert st["cooldown_until"] <= now + sup.COOLDOWN_DURATION
    assert st["next_start_at"] <= now + sup.COOLDOWN_DURATION
    assert st["backoff"] <= sup.MAX_BACKOFF
    assert sup._restore_stats({"services": {"svc": "garbage"}}) == {}
    bad = sup._restore_stats({"services": {"svc": {"consecutive_failures": "abc"}}})
    assert bad["svc"]["consecutive_failures"] == 0
    assert sup._restore_stats({}) == {}


# ------------------------------------------------------------- shutdown
def test_shutdown_terminates_waits_and_kills_only_after_grace(env):
    polite = FakeProc(env.clock, None, 0, ignore_term=False)
    stubborn = FakeProc(env.clock, None, 0, ignore_term=True)
    procs = {"polite": polite, "stubborn": stubborn}
    killed = sup._shutdown_children(procs, grace=5)
    assert killed == ["stubborn"]
    assert polite.events == ["terminate", "wait"]
    assert stubborn.events == ["terminate", "wait", "kill", "wait"]
    assert procs == {}


def test_signal_shutdown_cleans_up_owned_resources(env):
    before = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT)}
    env.clock.on_sleep = lambda _s: os.kill(os.getpid(), signal.SIGTERM)
    with pytest.raises(SystemExit):
        sup.run()
    assert env.started and env.started[0].events[:2] == ["terminate", "wait"]
    assert not sup.SUPERVISOR_PID.exists()
    assert sup._lock_is_held(sup.SUPERVISOR_LOCK) is False
    assert env.saved()["services"]["svc"]["pid"] is None
    assert {s: signal.getsignal(s) for s in before} == before


def test_unexpected_exception_still_cleans_up(env):
    def boom(_s):
        raise RuntimeError("boom")
    env.clock.on_sleep = boom
    with pytest.raises(RuntimeError):
        sup.run()
    assert env.started[0].events[:2] == ["terminate", "wait"]
    assert not sup.SUPERVISOR_PID.exists()
    assert sup._lock_is_held(sup.SUPERVISOR_LOCK) is False


# ----------------------------- heartbeat: hung vs healthy task vs stale idle
def test_heartbeat_verdicts():
    now = 10_000.0
    v = sup._heartbeat_verdict
    p = Path(os.devnull)
    assert v(p, now, started_at=now - 10) == "ok"            # startup grace
    assert v(p, now, started_at=now - 500) == "stale"        # never wrote one


def test_heartbeat_idle_vs_task(tmp_path):
    hb = tmp_path / "hb.json"
    now = 10_000.0
    v = sup._heartbeat_verdict
    write_hb(hb, 7, "idle", updated_at=now - 60)
    assert v(hb, now, expected_pid=7) == "ok"
    write_hb(hb, 7, "idle", updated_at=now - (sup.HEARTBEAT_IDLE_MAX_AGE + 5))
    assert v(hb, now, expected_pid=7) == "stale"
    # Healthy scheduler executing a task: old updated_at, still inside deadline+grace
    write_hb(hb, 7, "task", updated_at=now - 85, deadline=now - 85 + 60, task="t")
    assert v(hb, now, expected_pid=7) == "ok"
    # Genuinely hung: task ran past its declared deadline plus grace
    write_hb(hb, 7, "task", updated_at=now - 95, deadline=now - 95 + 60, task="t")
    assert v(hb, now, expected_pid=7) == "hung"
    # Heartbeat from another PID / malformed input never counts as healthy forever
    assert v(hb, now, started_at=now - 500, expected_pid=8) == "stale"
    hb.write_text("{not json")
    assert v(hb, now, started_at=now - 500, expected_pid=7) == "stale"
    write_hb(hb, 7, "task", updated_at=now, deadline=None)
    assert v(hb, now, expected_pid=7) == "stale"


def _hb_service(env, name="svc"):
    hb = env.state / "svc_heartbeat.json"
    env.services[0]["heartbeat"] = hb
    return hb


def test_stale_idle_heartbeat_triggers_orderly_restart(env):
    hb = _hb_service(env)
    env.on_start = lambda p: write_hb(hb, p.pid, "idle", updated_at=env.clock.time())
    sup.run(max_loops=20)  # 200s: first process never refreshes its heartbeat
    first = env.started[0]
    assert first.events[:2] == ["terminate", "wait"]
    assert len(env.started) >= 2
    assert "heartbeat stale" in sup.SUPERVISOR_LOG.read_text()


def test_healthy_scheduler_running_a_task_is_not_restarted(env):
    hb = _hb_service(env)

    def start(p):
        now = env.clock.time()
        write_hb(hb, p.pid, "task", updated_at=now, deadline=now + 60, task="improvement_cycle")
    env.on_start = start
    sup.run(max_loops=8)  # 70s of fake time: inside deadline (60s) + grace (30s)
    assert len(env.started) == 1
    assert "heartbeat" not in sup.SUPERVISOR_LOG.read_text()


def test_hung_task_past_deadline_is_restarted(env):
    hb = _hb_service(env)

    def start(p):
        now = env.clock.time()
        write_hb(hb, p.pid, "task", updated_at=now, deadline=now + 60, task="x")
    env.on_start = start
    sup.run(max_loops=12)  # 110s > deadline(60)+grace(30)
    assert "heartbeat hung" in sup.SUPERVISOR_LOG.read_text()
    assert env.started[0].events[:2] == ["terminate", "wait"]


# ------------------------------------- exit code 75 / external scheduler owner
def _singleton_service(env):
    hb = env.state / "scheduler_heartbeat.json"
    lock = env.state / "scheduler.lock"
    env.services[0].update({"heartbeat": hb, "singleton_lock": lock})
    return hb, lock


def test_exit_75_with_verified_healthy_owner_is_harmless(env):
    hb, lock = _singleton_service(env)
    owner = live_foreign_process()
    fd = sup._acquire_lock(lock)
    try:
        write_hb(hb, owner.pid, "idle", updated_at=env.clock.time())
        env.spec = lambda: {"lifetime": 0, "rc": sup.EXIT_ALREADY_RUNNING, "ignore_term": False}
        sup.run(max_loops=5)
        assert len(env.started) == 1  # retries only after ALREADY_RUNNING_RETRY
        assert env.saved()["services"]["svc"]["consecutive_failures"] == 0
    finally:
        os.close(fd)
        owner.kill()
        owner.wait()


def test_exit_75_without_verified_owner_counts_as_failure(env):
    hb, lock = _singleton_service(env)
    env.spec = lambda: {"lifetime": 0, "rc": sup.EXIT_ALREADY_RUNNING, "ignore_term": False}
    sup.run(max_loops=4)  # no lock holder, no heartbeat
    assert env.saved()["services"]["svc"]["consecutive_failures"] >= 1
    assert "no healthy external owner verified" in sup.SUPERVISOR_LOG.read_text()


def test_heartbeat_rejects_future_timestamps_deadlines_and_unknown_phases(tmp_path):
    hb = tmp_path / "hb.json"
    now = 10_000.0
    v = sup._heartbeat_verdict
    write_hb(hb, 7, "idle", updated_at=now + 60)
    assert v(hb, now, expected_pid=7) == "stale"
    write_hb(hb, 7, "task", updated_at=now, deadline=now + 10_000, task="x")
    assert v(hb, now, expected_pid=7) == "stale"
    write_hb(hb, 7, "unknown", updated_at=now)
    assert v(hb, now, expected_pid=7) == "stale"
    write_hb(hb, True, "idle", updated_at=now)
    assert v(hb, now, expected_pid=7) == "stale"


def test_stop_requires_verified_supervisor_process_and_lock(monkeypatch):
    monkeypatch.setattr(sup, "_is_process_alive", lambda _pid: True)
    monkeypatch.setattr(sup, "_lock_is_held", lambda _path: False)
    monkeypatch.setattr(sup, "_is_supervisor_process", lambda _pid: True)
    assert sup._can_signal_supervisor(4242) is False  # no singleton owner
    monkeypatch.setattr(sup, "_lock_is_held", lambda _path: True)
    monkeypatch.setattr(sup, "_is_supervisor_process", lambda _pid: False)
    assert sup._can_signal_supervisor(4242) is False  # PID is not this repo's supervisor
    monkeypatch.setattr(sup, "_is_supervisor_process", lambda _pid: True)
    assert sup._can_signal_supervisor(4242) is True
    assert sup._can_signal_supervisor(os.getpid()) is False


def test_external_owner_verification_rejects_each_unhealthy_case(env):
    hb, lock = _singleton_service(env)
    svc, now = env.services[0], env.clock.time()
    owner = live_foreign_process()
    try:
        assert sup._external_owner_healthy(svc, now) is False            # nothing exists
        fd = sup._acquire_lock(lock)
        try:
            assert sup._external_owner_healthy(svc, now) is False        # lock held, no heartbeat
            write_hb(hb, dead_pid(), "idle", updated_at=now)
            assert sup._external_owner_healthy(svc, now) is False        # heartbeat names dead PID
            write_hb(hb, os.getpid(), "idle", updated_at=now)
            assert sup._external_owner_healthy(svc, now) is False        # names the supervisor itself
            write_hb(hb, owner.pid, "idle", updated_at=now - 1000)
            assert sup._external_owner_healthy(svc, now) is False        # stale heartbeat
            write_hb(hb, owner.pid, "idle", updated_at=now)
            assert sup._external_owner_healthy(svc, now) is True         # everything verified
        finally:
            os.close(fd)
        assert sup._external_owner_healthy(svc, now) is False            # lock released
    finally:
        owner.kill()
        owner.wait()


# ------------------------------------------- scheduler: --once / lock / log
def _count_tasks(monkeypatch):
    calls = []
    monkeypatch.setattr(sched, "run_task", lambda t: calls.append(t["name"]) or
                        {"name": t["name"], "success": True, "output": "", "timestamp": "t"})
    return calls


def test_once_runs_all_tasks_in_order_when_free(monkeypatch, tmp_path):
    calls = _count_tasks(monkeypatch)
    assert sched.run_once(tmp_path / "s.lock") == 0
    assert calls == [t["name"] for t in sched.TASKS]
    assert sched.acquire_singleton_lock(tmp_path / "s.lock") is not None  # released


def test_once_returns_failure_when_any_task_fails(monkeypatch, tmp_path):
    calls = []

    def task_result(task):
        calls.append(task["name"])
        return {"name": task["name"], "success": task["name"] != "integrity_check",
                "output": "simulated", "timestamp": "t"}

    monkeypatch.setattr(sched, "run_task", task_result)
    assert sched.run_once(tmp_path / "s.lock") == 1
    assert calls == [t["name"] for t in sched.TASKS]


def test_once_refuses_while_singleton_lock_is_held(monkeypatch, tmp_path):
    calls = _count_tasks(monkeypatch)
    held = sched.acquire_singleton_lock(tmp_path / "s.lock")
    try:
        assert sched.run_once(tmp_path / "s.lock") == sched.EXIT_ALREADY_RUNNING
        assert calls == []
    finally:
        held.close()


def test_duplicate_concurrent_once_runs_tasks_only_once(monkeypatch, tmp_path):
    entered, release = threading.Event(), threading.Event()
    calls = []

    def slow_task(t):
        calls.append(t["name"])
        entered.set()
        release.wait(5)
        return {"name": t["name"], "success": True, "output": "", "timestamp": "t"}

    monkeypatch.setattr(sched, "run_task", slow_task)
    lock = tmp_path / "s.lock"
    results = {}
    th = threading.Thread(target=lambda: results.setdefault("first", sched.run_once(lock)))
    th.start()
    assert entered.wait(5)
    assert sched.run_once(lock) == sched.EXIT_ALREADY_RUNNING  # duplicate is refused
    release.set()
    th.join(10)
    assert results["first"] == 0
    assert calls == [t["name"] for t in sched.TASKS]  # each task ran exactly once


def test_run_forever_refuses_second_instance(monkeypatch, tmp_path):
    monkeypatch.setattr(sched, "LOCK_PATH", tmp_path / "scheduler.lock")
    held = sched.acquire_singleton_lock()
    try:
        assert sched.run_forever() == sched.EXIT_ALREADY_RUNNING
    finally:
        held.close()


def test_run_forever_heartbeat_distinguishes_task_from_idle(monkeypatch, tmp_path):
    monkeypatch.setattr(sched, "STATE", tmp_path)
    monkeypatch.setattr(sched, "LOCK_PATH", tmp_path / "scheduler.lock")
    monkeypatch.setattr(sched, "HEARTBEAT", tmp_path / "hb.json")
    monkeypatch.setattr(sched, "SCHEDULER_LOG", tmp_path / "log.json")
    seen = []

    def fake_task(t):
        seen.append(json.loads((tmp_path / "hb.json").read_text()))
        return {"name": t["name"], "success": True, "output": "", "timestamp": "2026-01-01T00:00:00"}

    class Stop(Exception):
        pass

    def stop_sleep(_s):
        raise Stop

    monkeypatch.setattr(sched, "run_task", fake_task)
    monkeypatch.setattr(sched.time, "sleep", stop_sleep)
    with pytest.raises(Stop):
        sched.run_forever()
    assert len(seen) == len(sched.TASKS)
    for hb in seen:
        assert hb["phase"] == "task" and hb["pid"] == os.getpid()
        assert hb["task_deadline"] - hb["updated_at"] == pytest.approx(sched.TASK_TIMEOUT_SECONDS, abs=2)
    final = json.loads((tmp_path / "hb.json").read_text())
    assert final["phase"] == "idle"
    assert len(json.loads((tmp_path / "log.json").read_text())) == len(sched.TASKS)


def test_scheduler_log_write_is_atomic(monkeypatch, tmp_path):
    log = tmp_path / "scheduler_log.json"
    sched._append_log({"name": "a"}, log)
    good = log.read_text()

    def failing_replace(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(sched.os, "replace", failing_replace)
    with pytest.raises(OSError):
        sched._append_log({"name": "b"}, log)
    monkeypatch.undo()
    assert log.read_text() == good  # previous log intact, never half-written
    assert json.loads(log.read_text()) == [{"name": "a"}]
    assert not list(tmp_path.glob("*.tmp"))  # temp file cleaned up


def test_scheduler_log_is_bounded_and_tolerates_corruption(tmp_path):
    log = tmp_path / "scheduler_log.json"
    log.write_text("{corrupt")
    sched._append_log({"n": -1}, log)
    assert json.loads(log.read_text()) == [{"n": -1}]
    for i in range(sched.LOG_MAX_ENTRIES + 20):
        sched._append_log({"n": i}, log)
    data = json.loads(log.read_text())
    assert len(data) == sched.LOG_MAX_ENTRIES
    assert data[-1] == {"n": sched.LOG_MAX_ENTRIES + 19}


def test_heartbeat_write_is_atomic_and_never_raises(tmp_path):
    hb = tmp_path / "hb.json"
    sched.write_heartbeat(hb, phase="task", task="health_check", task_deadline=123.0)
    data = json.loads(hb.read_text())
    assert data["phase"] == "task" and data["task"] == "health_check"
    assert data["task_deadline"] == 123.0 and data["pid"] == os.getpid()
    assert not list(tmp_path.glob("*.tmp"))
    blocker = tmp_path / "blocker"
    blocker.write_text("a file, not a directory")
    sched.write_heartbeat(blocker / "hb.json")  # unwritable location: must not raise


# ------------------------------------------------ preservation of behaviour
def test_existing_service_definitions_and_constants_preserved():
    names = [s["name"] for s in SERVICES_ORIGINAL_VIEW()]
    assert names == ["node1_runtime", "control_room", "scheduler"]
    node1, control = SERVICES_ORIGINAL_VIEW()[:2]
    assert node1["cmd"][1:] == [str(sup.ROOT / "scripts" / "node1_runtime.py"), "run"]
    assert control["cmd"][1:] == [str(sup.ROOT / "scripts" / "yair_control_room.py")]
    assert node1["cwd"] == control["cwd"] == str(sup.ROOT)
    assert (sup.MAX_BACKOFF, sup.INITIAL_BACKOFF, sup.MAX_CONSECUTIVE, sup.COOLDOWN_DURATION) == (300, 5, 10, 600)
    assert sup._get_backoff(3, 5) == 40 and sup._get_backoff(10, 5) == 600


def SERVICES_ORIGINAL_VIEW():
    # Re-read from the module source so the env fixture's monkeypatching can't hide changes.
    import importlib.util
    spec = importlib.util.spec_from_file_location("sup_fresh", sup.ROOT / "scripts" / "supervisor.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SERVICES


def test_scheduler_tasks_and_task_result_shape_preserved(monkeypatch):
    assert sched.TASKS == [
        {"name": "health_check", "script": "health_monitor.py", "interval_seconds": 300},
        {"name": "improvement_cycle", "script": "improvement_cycle.py", "interval_seconds": 900},
        {"name": "integrity_check", "script": "state_integrity.py", "interval_seconds": 600},
        {"name": "learning_analysis", "script": "learning_loop.py", "interval_seconds": 900},
    ]
    assert sched.TASK_TIMEOUT_SECONDS == 60
    captured = {}

    def fake_run(cmd, **kw):
        captured.update(kw)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(sched.subprocess, "run", fake_run)
    result = sched.run_task(sched.TASKS[0])
    assert set(result) == {"name", "success", "output", "timestamp"}
    assert result["success"] is True and result["output"] == "ok"
    assert captured["timeout"] == 60
