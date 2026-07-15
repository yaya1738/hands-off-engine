from dataclasses import dataclass
from typing import Any, List


@dataclass
class TimelineEvent:
    stage: str
    timestamp: str
    data: Any


class ProvisioningTimeline:
    def __init__(self):
        self._events: List[TimelineEvent] = []

    def add_event(
        self,
        stage: str,
        timestamp: str,
        data: Any,
    ) -> None:
        self._events.append(
            TimelineEvent(
                stage=stage,
                timestamp=timestamp,
                data=data,
            )
        )

    def get_timeline(self) -> List[TimelineEvent]:
        return sorted(
            self._events,
            key=lambda event: event.timestamp,
        )

    def validate_order(self) -> bool:
        timeline = self.get_timeline()

        return all(
            timeline[i].timestamp <= timeline[i + 1].timestamp
            for i in range(len(timeline) - 1)
        )
