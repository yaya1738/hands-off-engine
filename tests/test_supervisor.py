import json, tempfile, shutil
from pathlib import Path
from datetime import datetime, timezone

import os
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_supervisor_loads_save_state(tmp_path):
    from scripts import supervisor
    state_file = tmp_path / "state.json"
    # monkey-patch
    supervisor.WATCHDOG_STATE = state_file
    
    state = supervisor._load_state()
    assert state == {}
    
    state["test"] = True
    supervisor._save_state(state)
    
    loaded = supervisor._load_state()
    assert loaded.get("test") is True


def test_backoff_bounded():
    from scripts.supervisor import _get_backoff, MAX_BACKOFF, COOLDOWN_DURATION
    # Normal backoff
    b = _get_backoff(0, 5)
    assert b == 5
    
    b = _get_backoff(3, 5)
    assert b == 40  # 5 * 2^3
    
    # Cooldown at max failures
    b = _get_backoff(10, 5)
    assert b == COOLDOWN_DURATION
    
    # Normal backoff is bounded
    for i in range(10):
        b = _get_backoff(i, 5)
        assert b <= MAX_BACKOFF


def test_process_alive_check():
    from scripts.supervisor import _is_process_alive
    assert not _is_process_alive(9999999)  # nonexistent
    # Test self (current process is alive)
    assert _is_process_alive(os.getpid())
