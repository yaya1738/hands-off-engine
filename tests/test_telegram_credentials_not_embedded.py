"""Regression checks for credential removal in PR #371."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCANNED_PATHS = (
    ".env.social.template",
    "ai/unified_ai.py",
    "api/autonomous_promotion.py",
    "api/optimized_marketplace.py",
    "api/signal_marketplace.py",
    "api/social_promotion.py",
    "api/viral_promotion.py",
    "autonomous/instant_manifest.py",
    "autonomous/moonshot_loop.py",
    "autonomous/optimal_singularity.py",
    "autonomous/singularity_trigger.py",
    "autonomous/time_collapse.py",
    "docs/AUTONOMOUS_ACTIVATION_RUNBOOK.md",
    "telegram/TELEGRAM_SETUP.md",
    "SETUP_TELEGRAM_STEP_BY_STEP.md",
    "scripts/activate_income_now.py",
    "scripts/autonomous_phase_manager.py",
    "scripts/capital_recovery_monitor.py",
    "scripts/coordination_agent.py",
    "scripts/daily_digest.py",
    "scripts/payment_monitor.py",
    "scripts/setup_autonomous_mode.sh",
    "scripts/setup_telegram.sh",
    "termux-hands-off/autopilot/telegram_setup.sh",
    "scripts/snapshot_system_state.py",
)
PYTHON_PATHS = tuple(path for path in SCANNED_PATHS if path.endswith(".py"))
BOT_TOKEN_PATTERN = re.compile(r"(?<![A-Za-z0-9])\d{8,12}:[A-Za-z0-9_-]{30,}(?![A-Za-z0-9])")


def test_changed_python_files_parse():
    """Catch syntax regressions in every Python file touched by credential cleanup."""
    for relative_path in PYTHON_PATHS:
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        ast.parse(source, filename=relative_path)


def test_no_bot_token_literals_remain_in_credential_cleanup_files():
    """Bot API tokens must come from runtime configuration, never source literals."""
    for relative_path in SCANNED_PATHS:
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        assert BOT_TOKEN_PATTERN.search(source) is None, relative_path


def test_telegram_environment_lookups_have_no_embedded_fallbacks():
    """Missing Telegram credentials must not fall back to committed values."""
    credential_names = {"TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"}
    for relative_path in PYTHON_PATHS:
        tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function = node.func
            if not (
                isinstance(function, ast.Attribute)
                and function.attr in {"getenv", "get"}
            ):
                continue
            if not node.args or not isinstance(node.args[0], ast.Constant):
                continue
            if node.args[0].value in credential_names and len(node.args) > 1:
                fallback = node.args[1]
                assert (
                    isinstance(fallback, ast.Constant)
                    and fallback.value in ("", None)
                ), f"{relative_path}:{node.lineno} embeds a non-empty credential fallback"


def test_chat_id_assignments_are_not_numeric_literals():
    """Chat destinations must be configured outside tracked source."""
    for relative_path in PYTHON_PATHS:
        tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            if any(
                isinstance(target, ast.Name) and target.id.lower() == "chat_id"
                for target in targets
            ):
                assert not (
                    isinstance(value, ast.Constant)
                    and isinstance(value.value, (int, str))
                    and str(value.value).isdigit()
                ), f"{relative_path}:{node.lineno} embeds a numeric chat ID"
