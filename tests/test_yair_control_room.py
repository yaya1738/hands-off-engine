import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import Mock, patch

from scripts import yair_control_room as room


def test_read_events_reads_valid_json_and_skips_bad_lines(tmp_path, monkeypatch):
    bus = tmp_path / "messages.jsonl"
    bus.write_text(json.dumps({"from": "anyclaw", "to": "factory", "type": "task_result", "timestamp": "now"}) + "\nBAD\n")
    monkeypatch.setattr(room, "BUS", bus)
    events = room.read_events()
    assert len(events) == 1
    assert events[0]["type"] == "task_result"


def test_read_events_empty_when_bus_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(room, "BUS", tmp_path / "missing.jsonl")
    assert room.read_events() == []


def test_control_room_bind_host_must_be_loopback():
    assert room.is_loopback_host("127.0.0.1")
    assert room.is_loopback_host("::1")
    assert room.is_loopback_host("localhost")
    assert not room.is_loopback_host("0.0.0.0")
    assert not room.is_loopback_host("192.168.1.20")
    assert not room.is_loopback_host("example.com")


def test_control_room_rejects_nonlocal_host_and_dns_rebinding():
    assert not room.is_local_request("example.com:8788", None, 8788)
    assert not room.is_local_request("192.168.1.20:8788", None, 8788)
    assert not room.is_local_request("127.0.0.1:8787", None, 8788)


def test_control_room_accepts_loopback_origin_only_on_same_port():
    assert room.is_local_request("127.0.0.1:8788", "http://127.0.0.1:8788", 8788)
    assert room.is_local_request("localhost:8788", None, 8788)
    assert not room.is_local_request("127.0.0.1:8788", "http://attacker.example", 8788)
    assert not room.is_local_request("127.0.0.1:8788", "http://localhost:9999", 8788)


def test_control_room_main_refuses_remote_bind(monkeypatch):
    monkeypatch.setattr("sys.argv", ["yair_control_room.py", "--host", "0.0.0.0"])
    with __import__("pytest").raises(SystemExit) as exc:
        room.main()
    assert exc.value.code == 2


def _post_control_room(server, payload):
    data = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{server.server_port}/api/send",
        data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _start_control_room_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), room.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_control_room_rejects_oversized_operator_body():
    server, thread = _start_control_room_server()
    try:
        status, _ = _post_control_room(server, {"message": "x" * room.MAX_OPERATOR_BODY_BYTES})
        assert status == 413
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)


def test_control_room_rejects_non_object_json_and_non_string_message():
    server, thread = _start_control_room_server()
    try:
        status, _ = _post_control_room(server, ["not", "an", "object"])
        assert status == 400
        status, _ = _post_control_room(server, {"message": {"nested": "value"}})
        assert status == 400
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)


def test_control_room_rejects_malformed_json_without_commhub_call():
    server, thread = _start_control_room_server()
    try:
        with patch("scripts.comm_hub.CommHub") as comm_hub:
            status, _ = _post_control_room(server, b"{not-json")
        assert status == 400
        comm_hub.assert_not_called()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)

