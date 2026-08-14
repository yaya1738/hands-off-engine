from pathlib import Path
import subprocess


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "bootstrap_host.sh"


def test_bootstrap_host_is_valid_bash():
    result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_bootstrap_host_is_provider_neutral_and_credential_free():
    text = SCRIPT.read_text()

    forbidden = (
        "provision_oracle_cloud.sh",
        "POLYMARKET_API_KEY=",
        "POLYMARKET_API_SECRET=",
        "POLYMARKET_PASSPHRASE=",
        "scp .env",
        "cp .env",
        "LIVE_TRADING_ENABLED=true",
    )
    for marker in forbidden:
        assert marker not in text

    assert "bash -s -- \"$REPO_URL\" \"$REF\" \"$REMOTE_ROOT\"" in text
    assert "LIVE_TRADING_ENABLED is False" in text
    assert "systemctl --user --version" in text
