from pathlib import Path


def test_telegram_listener_requires_allowlist():
    source = Path("telegram/telegram_bot_listener.py").read_text(encoding="utf-8")
    assert "if not ALLOWED_CHAT_ID:" in source
    assert "refusing inbound message" in source
    assert 'str(chat_id) != str(ALLOWED_CHAT_ID)' in source


def test_plain_text_reaches_human_loop():
    source = Path("telegram/telegram_bot_listener.py").read_text(encoding="utf-8")
    assert "self.human_loop.receive" in source
    assert "else:" in source
