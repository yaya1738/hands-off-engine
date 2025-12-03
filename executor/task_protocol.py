from dataclasses import dataclass, asdict
from typing import List, Optional
import datetime

@dataclass
class ExecutionTask:
    task_id: str
    command: List[str]  # ["python", "script.py"]
    working_dir: str = "."
    mode: str = "DRYRUN" # "DRYRUN" or "LIVE"
    timeout_sec: int = 60

@dataclass
class ExecutionResult:
    task_id: str
    status: str  # "success", "error", "rejected", "timeout"
    exit_code: Optional[int]
    stdout: str
    stderr: str
    reason: Optional[str] # Populated if rejected or error
    started_at: str
    finished_at: str
    mode: str

    def to_json(self):
        return asdict(self)
