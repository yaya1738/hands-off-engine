import asyncio
from pathlib import Path

SOURCE = Path("autonomous/telegram_bot_creator.py").read_text()


def test_creator_has_no_process_or_credential_mutation():
    assert "subprocess" not in SOURCE
    assert "TelegramClient" not in SOURCE
    assert "send_message" not in SOURCE
    assert ".env.handsoff_telegram" not in SOURCE


def test_setup_fails_closed():
    namespace = {
        "__name__": "telegram_bot_creator_test",
        "__file__": str(Path("autonomous/telegram_bot_creator.py").resolve()),
    }
    exec(compile(SOURCE, "autonomous/telegram_bot_creator.py", "exec"), namespace)
    creator = namespace["TelegramBotCreator"]("1", "hash", "+1")
    assert asyncio.run(creator.setup_complete_system()) is False
