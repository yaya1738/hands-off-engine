from ai.factory.observability import (
    FactoryObservability,
)


class FakeDaemon:
    def status(self):
        return {
            "running": True,
        }


class FakeMetrics:
    def calculate(self, results):
        return {
            "jobs_total": len(results),
        }


class FakeAudit:
    def list_events(self):
        return [
            {
                "type": "ACTION",
            }
        ]


class FakeEvents:
    def history(self):
        return [
            {
                "type": "TEST",
            }
        ]


def test_snapshot():
    obs = FactoryObservability(
        FakeDaemon(),
        FakeMetrics(),
        FakeAudit(),
        FakeEvents(),
    )

    result = obs.snapshot(
        [
            {
                "status": "SUCCESS",
            }
        ]
    )

    assert result["health"]["running"] is True
    assert result["metrics"]["jobs_total"] == 1
    assert len(result["audit_events"]) == 1
    assert len(result["events"]) == 1


def test_report():
    obs = FactoryObservability(
        FakeDaemon()
    )

    result = obs.report()

    assert result["health"]["running"] is True
