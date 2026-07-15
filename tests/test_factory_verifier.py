from types import SimpleNamespace

from ai.factory.verifier import FactoryVerifier


def test_verify_success():
    verifier = FactoryVerifier()

    result = verifier.verify(
        SimpleNamespace(status="SUCCESS")
    )

    assert result["valid"] is True
    assert result["issues"] == []


def test_verify_failure():
    verifier = FactoryVerifier()

    result = verifier.verify(
        SimpleNamespace(status="FAILED")
    )

    assert result["valid"] is False
    assert "execution_failed" in result["issues"]
