from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_portable_runtime_service_points_at_autonomous_daemon():
    service = (ROOT / "deploy" / "factory-runtime.service").read_text()
    assert "autonomous_daemon.py" in service
    assert "Restart=always" in service
    assert "RestartSec=10" in service


def test_portable_runtime_installer_resolves_checkout_path():
    installer = (ROOT / "deploy" / "install-user-runtime.sh").read_text()
    assert 'REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"' in installer
    assert "systemctl --user daemon-reload" in installer
    assert "systemctl --user enable --now hands-off-engine-factory.service" in installer


def test_portable_runtime_keeps_live_trading_denied():
    daemon = (ROOT / "scripts" / "autonomous_daemon.py").read_text()
    assert "LIVE_TRADING_ENABLED = False" in daemon
    assert "if not LIVE_TRADING_ENABLED:" in daemon
