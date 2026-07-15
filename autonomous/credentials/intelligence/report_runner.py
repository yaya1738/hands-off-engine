from autonomous.credentials.intelligence.collector import (
    CredentialEventCollector,
)

from autonomous.credentials.intelligence.metrics import (
    CredentialMetrics,
)

from autonomous.credentials.intelligence.health_score import (
    CredentialHealthScorer,
)

from autonomous.credentials.intelligence.digest import (
    CredentialDigest,
)


class CredentialIntelligenceReport:

    def __init__(self):
        self.collector = CredentialEventCollector()
        self.metrics = CredentialMetrics()
        self.health = CredentialHealthScorer()
        self.digest = CredentialDigest()

    def generate(self):

        events = self.collector.load_events()

        normalized = [
            self.collector.normalize(e)
            for e in events
        ]

        metrics = self.metrics.calculate(
            normalized
        )

        health = self.health.score(
            metrics
        )

        return self.digest.generate(
            metrics,
            health
        )
