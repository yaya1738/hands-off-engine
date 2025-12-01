#!/usr/bin/env python3
"""
Immutable financial ledger for tracking costs and revenues
Blockchain-inspired append-only ledger
"""
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class LedgerEntry:
    """Single ledger entry with cryptographic hash for immutability"""
    entry_id: str
    timestamp: str
    session_id: str
    component: str
    action: str
    amount: float  # Positive for revenue, negative for costs
    category: str  # "cost" or "revenue"
    metadata: Dict[str, Any]
    previous_hash: str
    current_hash: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class FinancialLedger:
    """
    Immutable financial ledger for tracking all costs and revenues

    Features:
    - Blockchain-inspired hash chaining for immutability
    - Separate cost and revenue tracking
    - Session-based analysis
    - ROI calculation
    - Budget recommendations
    """

    def __init__(self, ledger_file: str = "audit/ledger.jsonl"):
        self.ledger_file = Path(ledger_file)
        self.ledger_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize with genesis entry if new ledger
        if not self.ledger_file.exists():
            self._create_genesis_entry()

    def _create_genesis_entry(self):
        """Create the first entry in the ledger"""
        genesis = LedgerEntry(
            entry_id="genesis",
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id="system",
            component="ledger.system",
            action="initialize",
            amount=0.0,
            category="system",
            metadata={"description": "Genesis block"},
            previous_hash="0" * 64,
            current_hash=self._compute_hash("genesis", "0" * 64, 0.0)
        )

        with open(self.ledger_file, "w") as f:
            f.write(json.dumps(genesis.to_dict()) + "\n")

    def _compute_hash(self, entry_id: str, previous_hash: str, amount: float) -> str:
        """Compute SHA-256 hash for entry"""
        data = f"{entry_id}{previous_hash}{amount}".encode()
        return hashlib.sha256(data).hexdigest()

    def _get_last_hash(self) -> str:
        """Get hash of the last entry in the ledger"""
        if not self.ledger_file.exists():
            return "0" * 64

        with open(self.ledger_file, "r") as f:
            lines = f.readlines()
            if not lines:
                return "0" * 64

            last_entry = json.loads(lines[-1])
            return last_entry["current_hash"]

    def add_cost(
        self,
        component: str,
        action: str,
        amount: float,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LedgerEntry:
        """
        Record a cost

        Args:
            component: Component incurring cost (e.g., "ai.claude", "ai.openai")
            action: Action being performed
            amount: Cost amount (positive number)
            session_id: Session ID
            metadata: Additional context

        Returns:
            LedgerEntry object
        """
        import uuid
        entry_id = str(uuid.uuid4())
        previous_hash = self._get_last_hash()
        current_hash = self._compute_hash(entry_id, previous_hash, -amount)

        entry = LedgerEntry(
            entry_id=entry_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=session_id,
            component=component,
            action=action,
            amount=-abs(amount),  # Costs are negative
            category="cost",
            metadata=metadata or {},
            previous_hash=previous_hash,
            current_hash=current_hash
        )

        with open(self.ledger_file, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

        return entry

    def add_revenue(
        self,
        component: str,
        action: str,
        amount: float,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LedgerEntry:
        """
        Record revenue

        Args:
            component: Component generating revenue (e.g., "trading.polymarket")
            action: Action being performed
            amount: Revenue amount (positive number)
            session_id: Session ID
            metadata: Additional context

        Returns:
            LedgerEntry object
        """
        import uuid
        entry_id = str(uuid.uuid4())
        previous_hash = self._get_last_hash()
        current_hash = self._compute_hash(entry_id, previous_hash, amount)

        entry = LedgerEntry(
            entry_id=entry_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=session_id,
            component=component,
            action=action,
            amount=abs(amount),  # Revenue is positive
            category="revenue",
            metadata=metadata or {},
            previous_hash=previous_hash,
            current_hash=current_hash
        )

        with open(self.ledger_file, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

        return entry

    def get_entries(
        self,
        session_id: Optional[str] = None,
        component: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[LedgerEntry]:
        """
        Query ledger entries

        Args:
            session_id: Filter by session
            component: Filter by component
            category: Filter by category ("cost" or "revenue")

        Returns:
            List of matching LedgerEntry objects
        """
        if not self.ledger_file.exists():
            return []

        entries = []
        with open(self.ledger_file, "r") as f:
            for line in f:
                entry_data = json.loads(line.strip())

                # Skip genesis entry
                if entry_data["entry_id"] == "genesis":
                    continue

                # Apply filters
                if session_id and entry_data["session_id"] != session_id:
                    continue
                if component and entry_data["component"] != component:
                    continue
                if category and entry_data["category"] != category:
                    continue

                entries.append(LedgerEntry(**entry_data))

        return entries

    def verify_integrity(self) -> bool:
        """
        Verify ledger integrity by checking hash chain

        Returns:
            True if ledger is intact, False if tampered
        """
        if not self.ledger_file.exists():
            return True

        with open(self.ledger_file, "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            entry_data = json.loads(line.strip())

            # Verify hash computation
            computed_hash = self._compute_hash(
                entry_data["entry_id"],
                entry_data["previous_hash"],
                entry_data["amount"]
            )

            if computed_hash != entry_data["current_hash"]:
                print(f"Hash mismatch at entry {i}")
                return False

            # Verify chain linkage
            if i > 0:
                prev_entry = json.loads(lines[i - 1].strip())
                if entry_data["previous_hash"] != prev_entry["current_hash"]:
                    print(f"Chain broken at entry {i}")
                    return False

        return True

    def get_balance(self, session_id: Optional[str] = None) -> Dict[str, float]:
        """
        Get financial balance

        Args:
            session_id: Optional session filter

        Returns:
            Dictionary with costs, revenue, and net profit
        """
        entries = self.get_entries(session_id=session_id)

        total_costs = sum(abs(e.amount) for e in entries if e.category == "cost")
        total_revenue = sum(e.amount for e in entries if e.category == "revenue")
        net_profit = total_revenue - total_costs

        return {
            "total_costs": total_costs,
            "total_revenue": total_revenue,
            "net_profit": net_profit,
            "roi_percent": (net_profit / total_costs * 100) if total_costs > 0 else 0
        }

    def get_component_performance(self) -> Dict[str, Dict[str, float]]:
        """
        Get performance metrics by component

        Returns:
            Dictionary mapping component to performance stats
        """
        entries = self.get_entries()

        component_stats = {}
        for entry in entries:
            if entry.component not in component_stats:
                component_stats[entry.component] = {
                    "total_cost": 0.0,
                    "total_revenue": 0.0,
                    "net_profit": 0.0,
                    "roi_percent": 0.0
                }

            stats = component_stats[entry.component]
            if entry.category == "cost":
                stats["total_cost"] += abs(entry.amount)
            elif entry.category == "revenue":
                stats["total_revenue"] += entry.amount

        # Calculate derived metrics
        for component, stats in component_stats.items():
            stats["net_profit"] = stats["total_revenue"] - stats["total_cost"]
            if stats["total_cost"] > 0:
                stats["roi_percent"] = (stats["net_profit"] / stats["total_cost"]) * 100

        return component_stats
