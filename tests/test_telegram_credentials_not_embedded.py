import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCANNED_FILES = (
    ".env.social.template",
    "docs/AUTONOMOUS_ACTIVATION_RUNBOOK.md",
    "state/permanent/SYSTEM_TRUTH.md",
    "api/autonomous_promotion.py",
    "api/optimized_marketplace.py",
    "api/signal_marketplace.py",
    "api/social_promotion.py",
    "api/viral_promotion.py",
    "scripts/activate_income_now.py",
    "scripts/autonomous_phase_manager.py",
    "scripts/capital_recovery_monitor.py",
    "scripts/coordination_agent.py",
    "scripts/daily_digest.py",
    "scripts/payment_monitor.py",
    "scripts/setup_autonomous_mode.sh",
    "scripts/snapshot_system_state.py",
    "ai/unified_ai.py",
    "autonomous/instant_manifest.py",
    "autonomous/moonshot_loop.py",
    "autonomous/optimal_singularity.py",
    "autonomous/singularity_trigger.py",
    "autonomous/time_collapse.py",
)

BOT_TOKEN_PATTERN = re.compile(r"api\.telegram\.org/bot\d{6,}:[A-Za-z0-9_-]{20,}", re.IGNORECASE)
TOKEN_ASSIGNMENT_PATTERN = re.compile(
    r"TELEGRAM_BOT_TOKEN\s*=\s*['\"]\d{6,}:[A-Za-z0-9_-]{20,}['\"]"
)
CHAT_ID_ASSIGNMENT_PATTERN = re.compile(r"TELEGRAM_CHAT_ID\s*=\s*['\"]\d{6,}['\"]")


def test_no_embedded_telegram_bot_credentials_or_chat_ids():
    for relative_path in SCANNED_FILES:
        source = (ROOT / relative_path).read_text(encoding="utf-8", errors="replace")
        assert not BOT_TOKEN_PATTERN.search(source), f"Embedded Telegram API credential in {relative_path}"
        assert not TOKEN_ASSIGNMENT_PATTERN.search(source), f"Hard-coded Telegram token in {relative_path}"
        assert not CHAT_ID_ASSIGNMENT_PATTERN.search(source), f"Hard-coded Telegram chat ID in {relative_path}"


def test_telegram_notification_config_uses_environment_without_secret_fallbacks():
    for relative_path in SCANNED_FILES:
        source = (ROOT / relative_path).read_text(encoding="utf-8", errors="replace")
        assert not re.search(
            r"os\.getenv\(\s*['\"]TELEGRAM_BOT_TOKEN['\"]\s*,",
            source,
        ), f"Telegram token fallback configured in {relative_path}"
