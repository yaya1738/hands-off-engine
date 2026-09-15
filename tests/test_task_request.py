"""Checkout-locality tests for the TaskRequest ingress adapter."""
import json
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.task_request import TaskRequest, ALLOWED_TYPES


def _root():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "ai" / "coordination").mkdir(parents=True)
    (tmp / "state").mkdir()
    return tmp


def test_request_written_to_canonical_bus():
    root = _root()
    try:
        adapter = TaskRequest(repo_root=root)
        rid = adapter.send("work_request", "need a task")
        assert rid.startswith("req-")

        lines = [json.loads(l) for l in (root / "ai" / "coordination" / "messages.jsonl").read_text().splitlines() if l.strip()]
        assert len(lines) == 1
        msg = lines[0]
        assert msg["type"] == "task_request"
        assert msg["from"] == "anyclaw" and msg["to"] == "factory"
        assert msg["msg_id"] == rid
        assert msg["context"]["request_type"] == "work_request"

        state = json.loads((root / "state" / "task_request_state.json").read_text())
        assert [s["id"] for s in state["sent"]] == [rid]
    finally:
        shutil.rmtree(root)


def test_two_roots_do_not_cross_contaminate():
    root_a = _root()
    root_b = _root()
    try:
        a = TaskRequest(repo_root=root_a)
        b = TaskRequest(repo_root=root_b)
        rid_a = a.send("work_request", "task A")
        rid_b = b.send("question", "question B")

        bus_a = (root_a / "ai" / "coordination" / "messages.jsonl").read_text()
        bus_b = (root_b / "ai" / "coordination" / "messages.jsonl").read_text()
        assert rid_a in bus_a and rid_b in bus_b
        assert rid_b not in bus_a and rid_a not in bus_b

        state_a = json.loads((root_a / "state" / "task_request_state.json").read_text())
        state_b = json.loads((root_b / "state" / "task_request_state.json").read_text())
        assert [s["id"] for s in state_a["sent"]] == [rid_a]
        assert [s["id"] for s in state_b["sent"]] == [rid_b]
    finally:
        shutil.rmtree(root_a)
        shutil.rmtree(root_b)


def test_local_state_is_bounded():
    root = _root()
    try:
        adapter = TaskRequest(repo_root=root)
        for i in range(105):
            adapter.send("status_probe", f"probe {i}")
        state = adapter.load_state()
        assert len(state["sent"]) == 100
    finally:
        shutil.rmtree(root)


def test_invalid_type_rejected():
    root = _root()
    try:
        adapter = TaskRequest(repo_root=root)
        try:
            adapter.send("not_a_type", "x")
        except ValueError:
            pass
        else:
            raise AssertionError("invalid request type must raise ValueError")
        assert set(ALLOWED_TYPES) == {"work_request", "question", "status_probe"}
    finally:
        shutil.rmtree(root)
