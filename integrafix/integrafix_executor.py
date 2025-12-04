"""
INTEGRAFIX: Execution bridge for trading.

Handles execution based on credential availability:
1. Direct execution if key available
2. Queue for mobile/termux if no key
3. API fallback options
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional

from integrafix.credential_loader import load_polymarket_key, get_wallet_address

STATE_DIR = Path("/root/hands-off-engine/state")
TERMUX_DIR = Path("/root/hands-off-engine/termux-hands-off")

class IntegrafixExecutor:
    """ABCFC-gated executor with credential handling."""
    
    def __init__(self):
        self.key = load_polymarket_key()
        self.wallet = get_wallet_address()
        self.client = None
        
        if self.key:
            try:
                from py_clob_client.client import ClobClient
                self.client = ClobClient(
                    "https://clob.polymarket.com",
                    key=self.key,
                    chain_id=137
                )
            except Exception as e:
                print(f"Client init failed: {e}")
    
    def can_execute_direct(self) -> bool:
        """Check if direct execution is possible."""
        return self.client is not None
    
    def execute_actions(self, actions: List[Dict]) -> Dict:
        """Execute integrafixed actions."""
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "direct" if self.can_execute_direct() else "queued",
            "executed": [],
            "queued": [],
            "errors": []
        }
        
        if self.can_execute_direct():
            results = self._execute_direct(actions, results)
        else:
            results = self._queue_for_mobile(actions, results)
        
        return results
    
    def _execute_direct(self, actions: List[Dict], results: Dict) -> Dict:
        """Execute directly via API."""
        from py_clob_client.clob_types import OrderArgs
        
        for action in actions:
            try:
                token_ids = action.get("token_ids", [])
                if not token_ids:
                    results["errors"].append({"market": action["market"], "error": "No token IDs"})
                    continue
                
                # YES token is first in list
                token_id = token_ids[0] if action["direction"] == "YES" else token_ids[1]
                
                # Size: $10 max per trade for safety
                size = min(10 / max(action["price"], 0.001), 500)
                
                order = OrderArgs(
                    token_id=token_id,
                    price=action["price"] * 1.05,  # 5% above market for fill
                    size=size,
                    side="BUY"
                )
                
                result = self.client.create_order(order)
                
                results["executed"].append({
                    "market": action["market"],
                    "direction": action["direction"],
                    "price": action["price"],
                    "size": size,
                    "result": str(result)
                })
                
            except Exception as e:
                results["errors"].append({
                    "market": action["market"],
                    "error": str(e)
                })
        
        return results
    
    def _queue_for_mobile(self, actions: List[Dict], results: Dict) -> Dict:
        """Queue actions for mobile execution via termux sync."""
        
        queue = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "PENDING_MOBILE_EXECUTION",
            "wallet": self.wallet,
            "integrafixed": True,
            "orders": []
        }
        
        for action in actions:
            order = {
                "market": action["market"],
                "market_id": action.get("market_id"),
                "direction": action["direction"],
                "price": action["price"],
                "size_usd": min(10 / max(action["price"], 0.001), 100),
                "edge": action.get("edge", 0),
                "token_ids": action.get("token_ids", []),
                "abcfc_score": action.get("abcfc_score", 0),
                "status": "QUEUED",
                "gates_passed": action.get("integrafix_gates", {})
            }
            queue["orders"].append(order)
            results["queued"].append(order)
        
        # Save to multiple locations for sync
        queue_file = STATE_DIR / "execution_queue.json"
        queue_file.write_text(json.dumps(queue, indent=2))
        
        termux_queue = TERMUX_DIR / "execution_queue.json"
        termux_queue.write_text(json.dumps(queue, indent=2))
        
        results["queue_files"] = [str(queue_file), str(termux_queue)]
        
        return results

def execute_integrafixed_actions() -> Dict:
    """Load and execute integrafixed actions."""
    
    actions_file = STATE_DIR / "integrafixed_actions.json"
    if not actions_file.exists():
        return {"error": "No integrafixed actions found"}
    
    with open(actions_file) as f:
        data = json.load(f)
    
    actions = data.get("actions", [])
    if not actions:
        return {"error": "No actions in file"}
    
    executor = IntegrafixExecutor()
    return executor.execute_actions(actions)
