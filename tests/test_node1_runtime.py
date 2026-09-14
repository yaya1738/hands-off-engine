import json, sys, os, tempfile, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_node_state_persistence():
    """Node state saves and loads correctly."""
    import scripts.node1_runtime as n
    tmp = Path(tempfile.mkdtemp())
    try:
        n.NODE_STATE = tmp / "node1_state.json"
        state = n.NodeState()
        assert state.data["node_id"] == "node-1"
        assert state.data["node_name"] == "Yair Phone (Xiaomi Redmi)"
        state.record_task()
        state.record_task()
        state.record_heartbeat()

        # Reload from disk
        state2 = n.NodeState()
        assert state2.data["tasks_processed"] == 2
        assert state2.data["health"] == "healthy"
    finally:
        shutil.rmtree(tmp)


def test_one_instance_lock():
    """Duplicate Node1 instances rejected."""
    import scripts.node1_runtime as n
    tmp = Path(tempfile.mkdtemp())
    try:
        n.NODE_LOCK = tmp / "node1.lock"
        n.NODE_PID = tmp / "node1.pid"
        lock1 = n.NodeLock()
        lock2 = n.NodeLock()
        assert lock1.try_acquire()
        assert not lock2.try_acquire(), "Second lock should fail"
        lock1.release()
        assert lock2.try_acquire()
        lock2.release()
    finally:
        shutil.rmtree(tmp)


def test_node_identity_metadata():
    """Node identity metadata is correct."""
    import scripts.node1_runtime as n
    assert n.NODE_ID == "node-1"
    assert n.NODE_PARTY == "anyclaw"
    assert "Xiaomi" in n.NODE_DEVICE
    assert "Android 15" in n.NODE_DEVICE


def test_heartbeat_updates_timestamp():
    """Heartbeat updates last_heartbeat timestamp."""
    import scripts.node1_runtime as n
    tmp = Path(tempfile.mkdtemp())
    try:
        n.NODE_STATE = tmp / "node1_state.json"
        state = n.NodeState()
        assert state.data["last_heartbeat"] is None
        state.record_heartbeat()
        assert state.data["last_heartbeat"] is not None
        assert state.data["health"] == "healthy"
    finally:
        shutil.rmtree(tmp)


def test_restart_counter_increments():
    """Each run increments the restart counter."""
    import scripts.node1_runtime as n
    tmp = Path(tempfile.mkdtemp())
    try:
        n.NODE_STATE = tmp / "node1_state.json"
        state = n.NodeState()
        assert state.data["restarts"] == 0
        state.data["restarts"] = state.data.get("restarts", 0) + 1
        state.save()
        state2 = n.NodeState()
        assert state2.data["restarts"] == 1
    finally:
        shutil.rmtree(tmp)
