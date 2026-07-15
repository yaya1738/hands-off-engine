from dataclasses import dataclass, field
from typing import List


@dataclass
class ExecutionRecord:
    task_id: str
    status: str = "STARTED"
    commands: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)

    def succeed(self, output: str = "") -> None:
        self.status = "SUCCESS"
        if output:
            self.outputs.append(output)

    def fail(self, error: str) -> None:
        self.status = "FAILED"
        self.outputs.append(error)
