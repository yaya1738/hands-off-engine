from ai.factory.authority_gateway import FactoryAuthorityGateway


class FakeJournal:
    def __init__(self):
        self.records = []

    def record(self, execution_id, status, payload=None):
        self.records.append((execution_id, status, payload))

    def interrupted(self):
        return [
            {
                "execution_id": "exec-survived-restart",
                "state": "STARTED",
                "reconciliation": "AMBIGUOUS_REVIEW_REQUIRED",
            }
        ]


class FakeRuntime:
    def __init__(self):
        self.development_tracker = object()
        self.improvement_approval = object()
        self.improvement_queue = object()
        self.artifact_registry = object()
        self.development_pipeline = object()


def test_authority_report_exposes_startup_reconciliation():
    gateway = FactoryAuthorityGateway(FakeRuntime(), FakeJournal())
    report = gateway.report()

    assert report["startup_reconciliation"]["status"] == "startup_reconciliation_complete"
    assert report["startup_reconciliation"]["ambiguous_count"] == 1
    assert report["startup_reconciliation"]["replay_performed"] is False
