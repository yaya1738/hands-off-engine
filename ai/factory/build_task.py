from dataclasses import dataclass, field
from typing import List


@dataclass
class BuildTask:
    task_id: str
    description: str
    status: str = "PENDING"
    changes: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)

    def complete(self) -> None:
        self.status = "COMPLETED"

    def fail(self, reason: str) -> None:
        self.status = "FAILED"
        self.changes.append(reason)
