"""Prevent Telegram bot credentials and chat IDs from being committed in source."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCAN_SUFFIXES = {".py", ".sh", ".json", ".md", ".env"}
EXCLUDED_PARTS = {".git", "__pycache__", ".venv", "venv", "node_modules"}
BOT_TOKEN = re.compile(r"\bbot\d{8,}:[A-Za-z0-9_-]{20,}\b")
BOT_TOKEN_DEFAULT = re.compile(
    r"""os\.getenv\(\s*["']TELEGRAM_BOT_TOKEN["']\s*,\s*["'][^"']+["']\s*\)"""
)
NUMERIC_CHAT_ID = re.compile(
    r"""["'](?:chat_id|TELEGRAM_CHAT_ID)["']\s*[:=]\s*["']\d{8,}["']"""
)


class TestNoEmbeddedTelegramCredentials(unittest.TestCase):
    def test_source_tree_contains_no_embedded_telegram_credentials(self):
        violations = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
                continue
            if any(part in EXCLUDED_PARTS for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for number, line in enumerate(text.splitlines(), 1):
                if BOT_TOKEN.search(line) or BOT_TOKEN_DEFAULT.search(line) or NUMERIC_CHAT_ID.search(line):
                    violations.append(f"{path.relative_to(ROOT)}:{number}")
        self.assertEqual([], violations, "Embedded Telegram credentials detected: " + ", ".join(violations))


if __name__ == "__main__":
    unittest.main()
