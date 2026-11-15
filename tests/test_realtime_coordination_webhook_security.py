"""Security regression tests for the realtime coordination webhook."""
import json
import logging
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer
from unittest.mock import Mock, patch

from scripts import realtime_coordination_service as service


def start_server(tmp_path, monkeypatch):
    bus = tmp_path / "messages.jsonl"
    monkeypatch.setattr(service, "COORDINATION_FILE", bus)
    service.CoordinationWebhook.message_callback = None
    server = HTTPServer(("127.0.0.1", 0), service.CoordinationWebhook)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, bus


def post(server, payload, token=None):
    url = f"http://127.0.0.1:{server.server_port}/coordination/message"
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


def valid_message(sender="copilot"):
    return {"from": sender, "to": "factory", "type": "coordination", "message": "review task"}


def test_webhook_binds_only_to_loopback():
    assert service.WEBHOOK_HOST == "127.0.0.1"
    assert service.is_loopback_host("127.0.0.1")
    assert service.is_loopback_host("::1")
    assert not service.is_loopback_host("0.0.0.0")
    assert not service.is_loopback_host("192.168.1.2")


def test_webhook_requires_host_loopback_and_exact_port():
    assert service.is_local_webhook_request("127.0.0.1:8888", 8888)
    assert not service.is_local_webhook_request("evil.example:8888", 8888)
    assert not service.is_local_webhook_request("127.0.0.1:8887", 8888)
    assert not service.is_local_webhook_request("", 8888)


def test_bearer_token_fails_closed_and_compares_exact_value(monkeypatch):
    monkeypatch.delenv("COORDINATION_WEBHOOK_TOKEN", raising=False)
    assert not service.webhook_authorized("Bearer secret")
    monkeypatch.setenv("COORDINATION_WEBHOOK_TOKEN", "secret")
    assert service.webhook_authorized("Bearer secret")
    assert not service.webhook_authorized("Bearer wrong")
    assert not service.webhook_authorized("secret")
    assert not service.webhook_authorized(None)


def test_sender_validation_rejects_operator_and_unknown_agents(monkeypatch):
    monkeypatch.delenv("COORDINATION_ALLOWED_SENDERS", raising=False)
    assert service.validate_webhook_message(valid_message())[0]
    assert not service.validate_webhook_message(valid_message("operator"))[0]
    assert not service.validate_webhook_message(valid_message("attacker"))[0]
    assert not service.validate_webhook_message({"from": "copilot"})[0]


def test_unauthenticated_post_is_rejected_without_bus_write(tmp_path, monkeypatch):
    monkeypatch.delenv("COORDINATION_WEBHOOK_TOKEN", raising=False)
    server, thread, bus = start_server(tmp_path, monkeypatch)
    try:
        assert post(server, valid_message()) == 503
        assert not bus.exists()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_invalid_token_is_rejected_without_bus_write(tmp_path, monkeypatch):
    monkeypatch.setenv("COORDINATION_WEBHOOK_TOKEN", "correct-secret")
    server, thread, bus = start_server(tmp_path, monkeypatch)
    try:
        assert post(server, valid_message(), token="wrong-secret") == 401
        assert not bus.exists()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_authorized_agent_message_is_persisted_without_git_side_effects(tmp_path, monkeypatch):
    monkeypatch.setenv("COORDINATION_WEBHOOK_TOKEN", "correct-secret")
    server, thread, bus = start_server(tmp_path, monkeypatch)
    callback = Mock()
    service.CoordinationWebhook.message_callback = callback
    try:
        with patch.object(service.subprocess, "run") as run:
            assert post(server, valid_message(), token="correct-secret") == 200
        assert run.call_count == 0
        saved = json.loads(bus.read_text().splitlines()[0])
        assert saved["from"] == "copilot"
        assert saved["timestamp"]
        callback.assert_called_once_with(saved)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_callback_failure_after_persist_still_acknowledges_once(tmp_path, monkeypatch):
    monkeypatch.setenv("COORDINATION_WEBHOOK_TOKEN", "correct-secret")
    server, thread, bus = start_server(tmp_path, monkeypatch)
    callback = Mock(side_effect=RuntimeError("consumer temporarily failed"))
    service.CoordinationWebhook.message_callback = callback
    try:
        assert post(server, valid_message(), token="correct-secret") == 200
        saved = [json.loads(line) for line in bus.read_text().splitlines()]
        assert len(saved) == 1
        callback.assert_called_once_with(saved[0])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_oversized_webhook_body_is_rejected_without_persisting(tmp_path, monkeypatch):
    monkeypatch.setenv("COORDINATION_WEBHOOK_TOKEN", "correct-secret")
    server, thread, bus = start_server(tmp_path, monkeypatch)
    try:
        payload = valid_message()
        payload["message"] = "x" * service.MAX_WEBHOOK_BODY_BYTES
        assert post(server, payload, token="correct-secret") == 413
        assert not bus.exists()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

def test_valid_token_does_not_allow_forged_operator_sender(tmp_path, monkeypatch):
    monkeypatch.setenv("COORDINATION_WEBHOOK_TOKEN", "correct-secret")
    server, thread, bus = start_server(tmp_path, monkeypatch)
    try:
        assert post(server, valid_message("operator"), token="correct-secret") == 403
        assert not bus.exists()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
