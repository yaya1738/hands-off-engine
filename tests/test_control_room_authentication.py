import base64
import os
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from scripts import yair_control_room as room


def test_control_room_token_is_created_with_owner_only_permissions(tmp_path):
    token_path = tmp_path / "state" / "control_room.token"
    token = room.load_or_create_control_room_token(token_path)

    assert len(token) >= 32
    assert room.load_or_create_control_room_token(token_path) == token
    assert os.stat(token_path).st_mode & 0o777 == 0o600


def test_control_room_basic_auth_validation():
    token = "a" * 48
    valid = base64.b64encode(f"operator:{token}".encode()).decode()
    wrong_user = base64.b64encode(f"admin:{token}".encode()).decode()
    wrong_token = base64.b64encode("operator:wrong".encode()).decode()

    assert room.authorization_valid(f"Basic {valid}", token)
    assert not room.authorization_valid(f"Basic {wrong_user}", token)
    assert not room.authorization_valid(f"Basic {wrong_token}", token)
    assert not room.authorization_valid("Bearer anything", token)
    assert not room.authorization_valid("", token)


def test_control_room_rejects_unauthenticated_reads_and_writes(monkeypatch):
    room.Handler.control_room_token = "b" * 48
    server = ThreadingHTTPServer(("127.0.0.1", 0), room.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        for path in ("/", "/api/events", "/api/state"):
            try:
                urllib.request.urlopen(base + path, timeout=3)
                assert False, f"{path} unexpectedly allowed unauthenticated access"
            except urllib.error.HTTPError as exc:
                assert exc.code == 401
                assert "Basic" in exc.headers.get("WWW-Authenticate", "")

        request = urllib.request.Request(
            base + "/api/send",
            data=b'{"message":"must not reach CommHub"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(request, timeout=3)
            assert False, "unauthenticated send unexpectedly succeeded"
        except urllib.error.HTTPError as exc:
            assert exc.code == 401
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        room.Handler.control_room_token = None


def test_control_room_refuses_non_loopback_bind_hosts():
    assert room.is_loopback_host("127.0.0.1")
    assert room.is_loopback_host("::1")
    assert room.is_loopback_host("localhost")
    assert not room.is_loopback_host("0.0.0.0")
    assert not room.is_loopback_host("192.168.1.20")
    assert not room.is_loopback_host("example.com")


def test_control_room_accepts_valid_basic_auth_for_ui():
    token = "c" * 48
    room.Handler.control_room_token = token
    server = ThreadingHTTPServer(("127.0.0.1", 0), room.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        credential = base64.b64encode(f"operator:{token}".encode()).decode()
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/",
            headers={"Authorization": f"Basic {credential}"},
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            assert response.status == 200
            assert b"Yair" in response.read()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        room.Handler.control_room_token = None