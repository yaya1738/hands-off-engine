from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "production-deploy.yml"


def test_remote_deploy_requires_pinned_host_key_and_strict_ssh_verification():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "secrets.PRODUCTION_KNOWN_HOSTS" in text
    assert "ssh-keyscan" not in text
    assert "StrictHostKeyChecking=yes" in text
    assert 'UserKnownHostsFile="$HOME/.ssh/known_hosts"' in text
    assert "DEPLOY_KNOWN_HOSTS" in text


def test_partial_remote_authority_configuration_fails_closed():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Remote production authority is partially configured; refusing unsafe fallback." in text
    assert "-n \"$DEPLOY_KNOWN_HOSTS\"" in text
