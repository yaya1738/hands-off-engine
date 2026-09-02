"""Legacy system-hardening compatibility facade.

The former implementation could kill and spawn configured processes and write
persistent state. Process lifecycle authority now belongs to the deployment
and Factory authority layers. This module is intentionally non-mutating.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ProcessConfig:
    name: str
    command: str
    working_dir: str
    required: bool
    max_restarts: int = 10
    restart_delay: float = 5.0
    health_check_interval: float = 30.0
    memory_limit_mb: int = 500
    cpu_timeout_seconds: int = 300


@dataclass
class ProcessState:
    name: str
    pid: Optional[int]
    status: str
    restarts: int
    last_restart: Optional[str]
    last_health_check: Optional[str]
    health_status: str


@dataclass
class SystemHealth:
    status: str
    processes_running: int
    processes_total: int
    critical_processes_ok: bool
    last_check: str
    uptime_hours: float
    issues: List[str]


CRITICAL_PROCESSES = {
    "backend_loop": ProcessConfig("backend_loop", "", "", True),
    "self_healer": ProcessConfig("self_healer", "", "", True),
    "hardware_brain": ProcessConfig("hardware_brain", "", "", False),
    "scaling_engine": ProcessConfig("scaling_engine", "", "", False),
    "infra_manager": ProcessConfig("infra_manager", "", "", False),
}


class SystemHardening:
    """Read-only compatibility facade for legacy supervision calls."""

    def __init__(self):
        self.state = {}

    def get_process_pid(self, name: str) -> Optional[int]:
        return None

    def is_process_running(self, name: str) -> bool:
        return False

    def check_process_health(self, name: str, config: ProcessConfig) -> ProcessState:
        return ProcessState(name, None, "unknown", 0, None, None, "unknown")

    def restart_process(self, name: str, config: ProcessConfig) -> bool:
        print(
            "[FACTORY-AUTHORITY] legacy process restart is disabled; "
            "submit lifecycle action through FactoryAuthorityGateway"
        )
        return False

    def check_system_health(self) -> SystemHealth:
        return SystemHealth(
            status="unknown",
            processes_running=0,
            processes_total=len(CRITICAL_PROCESSES),
            critical_processes_ok=False,
            last_check="",
            uptime_hours=0.0,
            issues=[
                "[FACTORY-AUTHORITY] legacy process inspection is non-authoritative; "
                "use the managed service health path"
            ],
        )

    def enforce_health(self) -> SystemHealth:
        return self.check_system_health()

    def supervise(self, interval: float = 60.0):
        raise RuntimeError(
            "[FACTORY-AUTHORITY] legacy supervision is disabled; "
            "submit lifecycle actions through FactoryAuthorityGateway"
        )


def status_report() -> str:
    health = SystemHardening().check_system_health()
    return (
        "SYSTEM HARDENING STATUS\n"
        f"System Status: {health.status.upper()}\n"
        "Lifecycle authority: FactoryAuthorityGateway\n"
        "Legacy mutation: disabled"
    )


def main():
    print(status_report())


if __name__ == "__main__":
    main()
