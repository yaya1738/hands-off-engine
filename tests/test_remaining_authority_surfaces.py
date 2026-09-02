from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_bounty_monitor_has_no_process_or_embedded_token():
    source = (ROOT / "autonomous/bounty_monitor.py").read_text()
    assert "subprocess" not in source
    assert "ghp_" not in source
    assert "respond_to_pr_comment" in source


def test_auto_identity_has_no_process_execution():
    source = (ROOT / "security/auto_identity.py").read_text()
    assert "subprocess" not in source
    assert "os.system" not in source
    assert "get_current_tty_owner" in source


def test_phase_transition_gate_has_no_process_execution():
    source = (ROOT / "factory_phase_transition_gate.py").read_text()
    assert "subprocess" not in source
    assert "check_output" not in source
    assert "FactoryAuthorityGateway" in source
