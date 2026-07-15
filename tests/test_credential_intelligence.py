from autonomous.credentials.intelligence.collector import CredentialEventCollector
from autonomous.credentials.intelligence.metrics import CredentialMetrics
from autonomous.credentials.intelligence.health_score import CredentialHealthScorer
from autonomous.credentials.intelligence.digest import CredentialDigest


def test_event_normalization():

    collector = CredentialEventCollector()

    event = {
        "identity": "gmail",
        "from": "RECOVERY",
        "to": "AWAITING_AUTHORIZATION",
        "reason": "oauth"
    }

    result = collector.normalize(event)

    assert result["identity"] == "gmail"


def test_metrics():

    metrics = CredentialMetrics().calculate(
        [
            {"to": "RECOVERY"},
            {"to": "AUTHORIZED"}
        ]
    )

    assert metrics["total_events"] == 2


def test_health():

    result = CredentialHealthScorer().score(
        {"recovery_events": 0}
    )

    assert result["health_score"] == 100


def test_digest():

    result = CredentialDigest().generate(
        {},
        {}
    )

    assert result["system"] == "credential_bridge"
