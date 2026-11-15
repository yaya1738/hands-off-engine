"""Prevent Telegram credentials in source, dotenv files, and templates."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCAN_SUFFIXES = {".py", ".sh", ".json", ".md", ".env", ".template", ".example", ".sample"}
EXCLUDED_PARTS = {".git", "__pycache__", ".venv", "venv", "node_modules"}
BOT_TOKEN = re.compile(r"\bbot\d{8,}:[A-Za-z0-9_-]{20,}\b")
BOT_TOKEN_DEFAULT = re.compile(
    r"""os\.getenv\(\s*["']TELEGRAM_BOT_TOKEN["']\s*,\s*["'](?!your[_-])[^"']+["']\s*\)"""
)
CHAT_ID_ASSIGNMENT = re.compile(
    r"""(?i)(?:["'](?:chat_id|TELEGRAM_CHAT_ID)["']|TELEGRAM_CHAT_ID)\s*[:=]\s*["']?-?\d{7,}["']?\b"""
)

def is_scannable(path):
    name = path.name.lower()
    return path.suffix.lower() in SCAN_SUFFIXES or ".env." in name or name.startswith(".env")

class TestNoEmbeddedTelegramCredentials(unittest.TestCase):
    def test_scans_dotenv_templates_and_backups(self):
        for name in (".env.social.template", "service.env", "auto_sources.env.bak.123"):
            self.assertTrue(is_scannable(Path(name)), name)

    def test_detects_common_credential_assignments(self):
        sample_token = "bot" + "12345678:" + ("A" * 26)
        self.assertIsNotNone(BOT_TOKEN.search("token = '" + sample_token + "'"))
        sample_default = "os.getenv(" + '"TELEGRAM_BOT_TOKEN", ' + '"embedded-value")'
        self.assertIsNotNone(BOT_TOKEN_DEFAULT.search(sample_default))
        self.assertIsNotNone(CHAT_ID_ASSIGNMENT.search("TELEGRAM_" + "CHAT_ID=123456789"))
        self.assertIsNotNone(CHAT_ID_ASSIGNMENT.search('"chat_' + 'id": "123456789"'))
        self.assertIsNone(CHAT_ID_ASSIGNMENT.search("TELEGRAM_" + "CHAT_ID=your_telegram_chat_id_here"))

    def test_source_tree_contains_no_embedded_telegram_credentials(self):
        violations = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or not is_scannable(path):
                continue
            if any(part in EXCLUDED_PARTS for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for number, line in enumerate(text.splitlines(), 1):
                if (BOT_TOKEN.search(line) or BOT_TOKEN_DEFAULT.search(line)
                        or CHAT_ID_ASSIGNMENT.search(line)):
                    violations.append(f"{path.relative_to(ROOT)}:{number}")
        self.assertEqual([], violations, "Embedded Telegram credentials detected: " + ", ".join(violations))

if __name__ == "__main__":
    unittest.main()
