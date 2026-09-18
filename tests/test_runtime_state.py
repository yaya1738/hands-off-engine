import os
import tempfile

from ai.factory.runtime_state import FactoryRuntimeState


def build():
    directory = tempfile.TemporaryDirectory()
    return directory, FactoryRuntimeState(
        storage_path=os.path.join(directory.name, "runtime_state.json")
    )


def test_save_state():
    directory, engine = build()
    try:
        result = engine.save_state({"status": "running"})
        assert result["saved"] is True
    finally:
        directory.cleanup()


def test_load_state():
    directory, engine = build()
    try:
        engine.save_state({"status": "running"})
        result = engine.load_state()
        assert result["loaded"] is True
    finally:
        directory.cleanup()


def test_snapshot():
    directory, engine = build()
    try:
        engine.save_state({"status": "running"})
        result = engine.snapshot()
        assert result["snapshotted"] is True
    finally:
        directory.cleanup()


def test_restore():
    directory, engine = build()
    try:
        result = engine.restore({"status": "restored"})
        assert result["restored"] is True
    finally:
        directory.cleanup()


def test_history():
    directory, engine = build()
    try:
        engine.save_state({})
        assert len(engine.history()) == 1
    finally:
        directory.cleanup()


def test_load_state_does_not_grow_history():
    directory, engine = build()
    try:
        engine.save_state({"status": "running"})
        before = len(engine.history())
        result = engine.load_state()
        assert result["loaded"] is True
        assert len(engine.history()) == before
    finally:
        directory.cleanup()
