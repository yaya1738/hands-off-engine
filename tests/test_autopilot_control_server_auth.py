import importlib.util
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "termux-hands-off"
    / "autopilot"
    / "control_server.py"
)


def _load_module(monkeypatch, token):
    monkeypatch.setenv("CONTROL_TOKEN", token)
    spec = importlib.util.spec_from_file_location("autopilot_control_server_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_control_api_rejects_all_requests_when_token_is_unconfigured(monkeypatch):
    module = _load_module(monkeypatch, "")
    handler = object.__new__(module.H)
    handler.headers = {}

    assert module.H._auth(handler) is False


def test_control_api_requires_matching_nonempty_token(monkeypatch):
    module = _load_module(monkeypatch, "expected-secret")
    handler = object.__new__(module.H)

    handler.headers = {}
    assert module.H._auth(handler) is False

    handler.headers = {"X-Token": "wrong-secret"}
    assert module.H._auth(handler) is False

    handler.headers = {"X-Token": "expected-secret"}
    assert module.H._auth(handler) is True


def test_control_api_defaults_to_loopback_and_rejects_network_binds(monkeypatch):
    module = _load_module(monkeypatch, "expected-secret")

    assert module.HOST == "127.0.0.1"
    assert module.validate_bind_host("127.0.0.1") == "127.0.0.1"
    assert module.validate_bind_host("::1") == "::1"
    assert module.validate_bind_host("localhost") == "localhost"

    for unsafe_host in ("0.0.0.0", "::", "192.168.1.20", "example.com"):
        try:
            module.validate_bind_host(unsafe_host)
            assert False, f"{unsafe_host} unexpectedly accepted"
        except ValueError:
            pass


def test_control_api_refuses_unsafe_environment_bind_at_import(monkeypatch):
    monkeypatch.setenv("CONTROL_HOST", "0.0.0.0")
    monkeypatch.setenv("CONTROL_TOKEN", "expected-secret")
    spec = importlib.util.spec_from_file_location("autopilot_control_server_unsafe_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        assert False, "unsafe CONTROL_HOST unexpectedly accepted"
    except ValueError as exc:
        assert "loopback" in str(exc)
