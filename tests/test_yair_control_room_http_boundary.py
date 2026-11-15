import io

from scripts.yair_control_room import (
    MAX_REQUEST_BYTES,
    is_loopback_host,
    read_json_request,
)


def test_control_room_rejects_non_loopback_bind_hosts():
    assert is_loopback_host("127.0.0.1")
    assert is_loopback_host("::1")
    assert is_loopback_host("localhost")
    for host in ("0.0.0.0", "::", "192.168.1.20", "10.0.0.2"):
        assert not is_loopback_host(host)


def test_control_room_reads_valid_bounded_json_object():
    code, body, error = read_json_request(
        {"content-length": "18"}, io.BytesIO(b'{"message":"hello"}')
    )
    assert code == 200
    assert body == {"message": "hello"}
    assert error is None


def test_control_room_rejects_oversized_request_before_reading():
    class NoRead:
        def read(self, _length):
            raise AssertionError("oversized body must not be read")

    code, body, error = read_json_request(
        {"content-length": str(MAX_REQUEST_BYTES + 1)}, NoRead()
    )
    assert code == 413
    assert body is None
    assert error == "request body too large"


def test_control_room_rejects_invalid_lengths_transfer_encoding_and_non_objects():
    for headers in (
        {},
        {"content-length": "-1"},
        {"content-length": "nope"},
        {"content-length": "2", "transfer-encoding": "chunked"},
    ):
        code, body, error = read_json_request(headers, io.BytesIO(b"{}"))
        assert code == 400
        assert body is None
        assert error

    code, body, error = read_json_request(
        {"content-length": "2"}, io.BytesIO(b"[]")
    )
    assert code == 400
    assert body is None
    assert error == "json object required"
