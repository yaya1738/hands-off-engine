import json, tempfile, shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _fresh_worker():
    from scripts import task_worker
    tw = task_worker
    # Save originals
    tw._orig_REPO_ROOT = tw.REPO_ROOT
    tw._orig_COORDINATION_BUS = tw.COORDINATION_BUS
    tw._orig_RESULTS = tw.RESULTS
    tw._orig_PROCESSED_IDS = tw.PROCESSED_IDS
    tw._orig_LOCK_DIR = tw.LOCK_DIR
    tmp = Path(tempfile.mkdtemp())
    tw.COORDINATION_BUS = tmp / "ai" / "coordination" / "messages.jsonl"
    tw.COORDINATION_BUS.parent.mkdir(parents=True, exist_ok=True)
    tw.RESULTS = tmp / "state" / "task_results.jsonl"
    tw.RESULTS.parent.mkdir(parents=True, exist_ok=True)
    tw.PROCESSED_IDS = tmp / "state" / "processed.json"
    tw.PROCESSED_IDS.parent.mkdir(parents=True, exist_ok=True)
    tw.LOCK_DIR = tmp / "state" / "locks"
    tw.REPO_ROOT = tmp
    return tw


def _restore_worker():
    from scripts import task_worker
    tw = task_worker
    for attr in ("REPO_ROOT", "COORDINATION_BUS", "RESULTS", "PROCESSED_IDS", "LOCK_DIR"):
        orig = getattr(tw, f"_orig_{attr}", None)
        if orig is not None:
            setattr(tw, attr, orig)


def test_bus_summary_empty(tmp_path):
    from scripts.task_worker import process_task, REPO_ROOT
    tw = _fresh_worker()
    try:
        # Empty bus
        task = {"context": {"task_id": "t1", "action": "bus_summary"}}
        result = process_task(task)
        assert result["context"]["status"] == "error"
    finally:
        shutil.rmtree(tw.REPO_ROOT)
        _restore_worker()


def test_bus_summary_with_messages(tmp_path):
    from scripts import task_worker
    tw = _fresh_worker()
    try:
        bus = tw.REPO_ROOT / "ai" / "coordination" / "messages.jsonl"
        bus.write_text("\n".join([
            json.dumps({"type": "task_result", "msg_id": "m1"}),
            json.dumps({"type": "task_result", "msg_id": "m2"}),
            json.dumps({"type": "continuation_event", "msg_id": "m3"}),
        ]) + "\n")
        task = {"context": {"task_id": "t1", "action": "bus_summary"}}
        result = task_worker.process_task(task)
        assert result["context"]["status"] == "success"
        r = result["context"]["result"]
        assert r["total"] == 3
        assert r["by_type"]["task_result"] == 2
    finally:
        shutil.rmtree(tw.REPO_ROOT)
        _restore_worker()


def test_lifecycle_summary_empty():
    from scripts.task_worker import process_task
    tw = _fresh_worker()
    try:
        task = {"context": {"task_id": "t1", "action": "lifecycle_summary"}}
        result = process_task(task)
        assert result["context"]["status"] == "success"
        assert result["context"]["result"]["total_tasks"] == 0
    finally:
        shutil.rmtree(tw.REPO_ROOT)
        _restore_worker()
