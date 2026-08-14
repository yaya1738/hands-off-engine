#!/usr/bin/env python3
"""Fail-closed compatibility shim for retired FleetCommander.

The historical implementation could initialize credential-bearing CLOB clients
per wallet and submit individual or batch orders. It is no longer an authority.
Financial execution must originate from the authoritative Factory gateway and
pass all current-rules and explicit-human-approval gates.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class ProcessStatus:
    process_id: int
    wallet_address: str
    alias: str
    status: str
    started_at: str
    last_heartbeat: str
    orders_placed: int = 0
    orders_cancelled: int = 0
    errors: int = 0


@dataclass
class FleetCommand:
    command: str
    target: str
    params: Dict
    timestamp: str = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class FleetCommander:
    """Retired compatibility surface; no wallet or order execution is possible."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.workers = []
        self.running = False

    @staticmethod
    def _denied(action: str = "financial execution") -> Dict[str, Any]:
        return {"success": False, "status": "DENIED", "action": action,
                "error": "FleetCommander is retired; financial execution is disabled."}

    def start_fleet(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self._denied("start_fleet")

    def stop_fleet(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        self.running = False
        return {"success": True, "status": "STOPPED"}

    def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self._denied("execute")

    def execute_command(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self._denied("execute_command")

    def place_order(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self._denied("place_order")

    def place_batch(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self._denied("place_batch")

    def cancel_order(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self._denied("cancel_order")

    def status(self) -> Dict[str, Any]:
        return {"success": True, "status": "RETIRED", "running": False, "workers": 0}
