#!/usr/bin/env python3
"""Fail-closed compatibility shim for retired ParallelOrderOrchestrator."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

POLYMARKET_HOST = ""

@dataclass
class OrderTask:
    task_id: str
    wallet_address: str
    action: str
    params: Dict
    priority: int = 1
    created_at: str = None
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

@dataclass
class OrderResult:
    task_id: str
    wallet_address: str
    success: bool
    result: Any
    elapsed_ms: float
    completed_at: str = None
    def __post_init__(self):
        if not self.completed_at:
            self.completed_at = datetime.now(timezone.utc).isoformat()

class WalletWorker:
    """Retired worker; credentials and CLOB clients are intentionally unavailable."""
    def __init__(self, wallet_address: str, private_key: str = "", funder_address: str = ""):
        self.wallet_address = wallet_address
        self.private_key = ""
        self.funder_address = ""
        self.client = None
        self.stats = {"orders_placed": 0, "orders_cancelled": 0, "errors": 0}
    def init_client(self) -> bool:
        return False
    def process_task(self, task: OrderTask) -> OrderResult:
        return OrderResult(task.task_id, task.wallet_address, False,
                           {"status":"DENIED","error":"Parallel order execution is retired."}, 0.0)

class ParallelOrderOrchestrator:
    """Retired compatibility surface; all financial mutations are denied."""
    def __init__(self, *args: Any, **kwargs: Any):
        self.workers = {}
        self.running = False
    @staticmethod
    def _denied(action: str) -> Dict[str, Any]:
        return {"success": False, "status": "DENIED", "action": action,
                "error": "ParallelOrderOrchestrator is retired; financial execution is disabled."}
    def start(self, *args: Any, **kwargs: Any): return self._denied("start")
    def stop(self, *args: Any, **kwargs: Any): self.running = False; return {"success":True,"status":"STOPPED"}
    def execute(self, *args: Any, **kwargs: Any): return self._denied("execute")
    def submit(self, *args: Any, **kwargs: Any): return self._denied("submit")
    def place_order(self, *args: Any, **kwargs: Any): return self._denied("place_order")
    def place_batch(self, *args: Any, **kwargs: Any): return self._denied("place_batch")
    def cancel(self, *args: Any, **kwargs: Any): return self._denied("cancel")
