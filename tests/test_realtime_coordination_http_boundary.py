import io
import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "realtime_coordination_service.py"


def load_module():
    spec = importlib.util.spec_from_file_location("realtime_coordination_service_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_valid_message_is_parsed():
    module = load_module()
    body = b'{"from":"agent","to":"factory","type":"coordination","message":"hello"}'
    status, message = module.read_webhook_message({"Content-Length": str(len(body))}, io.BytesIO(body))
    assert status == 200
    assert message["from"] == "agent"


def test_oversized_body_rejected_before_read():
    module = load_module()
    class NoRead:
        def read(self, length):
            raise AssertionError("body should not be read")
    status, message = module.read_webhook_message(
        {"Content-Length": str(module.MAX_WEBHOOK_BYTES + 1)}, NoRead()
    )
    assert status == 413
    assert message is None


@pytest.mark.parametrize("body", [
    b"[]",
    b'{"from":"agent","to":"factory","type":"coordination"}',
    b'{"from":1,"to":"factory","type":"coordination","message":"hello"}',
    b"not-json",
])
def test_invalid_message_rejected(body):
    module = load_module()
    status, message = module.read_webhook_message(
        {"Content-Length": str(len(body))}, io.BytesIO(body)
    )
    assert status == 400
    assert message is None


def test_transfer_encoding_and_missing_length_rejected():
    module = load_module()
    assert module.read_webhook_message(
        {"Content-Length": "2", "Transfer-Encoding": "chunked"}, io.BytesIO(b"{}")
    ) == (400, None)
    assert module.read_webhook_message({}, io.BytesIO(b"{}")) == (400, None)


def test_service_is_loopback_only_and_does_not_auto_push():
    source = MODULE_PATH.read_text()
    assert 'WEBHOOK_HOST = "127.0.0.1"' in source
    assert "HTTPServer((WEBHOOK_HOST, WEBHOOK_PORT)" in source
    assert "git', 'push" not in source
